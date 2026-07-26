"""Authenticated WebRTC signalling for live assessment proctoring."""

from __future__ import annotations

import contextlib
import logging

import socketio
from eventlet.semaphore import Semaphore

from assessment_db import hash_assessment_token
from db_config import get_connection, return_connection
from security_headers import configured_cors_origins
from user_db import get_user_by_id, user_auth_version


logger = logging.getLogger(__name__)

_allowed_origins = configured_cors_origins()
sio = socketio.Server(
    cors_allowed_origins=_allowed_origins,
    async_mode="eventlet",
    max_http_buffer_size=256 * 1024,
    logger=False,
    engineio_logger=False,
)

# {assessment_id: {'candidate': sid | None, 'interviewers': [sid, ...]}}
active_rooms = {}
# {sid: {'type': 'candidate'|'interviewer', 'assessment_id': int, ...}}
connections = {}
# Every accepted socket is authenticated during the Engine.IO handshake. Keeping
# this separate from room membership bounds idle authenticated sockets too.
authenticated_sockets = {}
_state_lock = Semaphore(1)

# Injected by app.py so handlers can decode staff JWTs in Flask context.
_flask_app = None


def init_websocket_server(app):
    global _flask_app
    _flask_app = app


def _positive_int(value):
    if isinstance(value, bool):
        return None
    try:
        value = int(value)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _verify_candidate_token(access_token, assessment_id):
    """Verify that a candidate token belongs to this active assessment."""

    assessment_id = _positive_int(assessment_id)
    if assessment_id is None or not isinstance(access_token, str) or not access_token:
        return False

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 1
            FROM scheduled_assessments sa
                    JOIN assessments a ON a.scheduled_assessment_id = sa.id
            WHERE sa.access_token_hash = %s
              AND a.id = %s
              AND sa.status = 'in_progress'
              AND a.status IN ('started', 'in_progress')
        """, (hash_assessment_token(access_token), assessment_id))
        return cursor.fetchone() is not None
    except Exception:
        logger.exception("Candidate token verification failed for assessment %s", assessment_id)
        return False
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)


def _verify_interviewer_jwt(token):
    """Return ``(user_id, role)`` for an authenticated staff token."""

    if _flask_app is None or not isinstance(token, str) or not token:
        return None
    try:
        with _flask_app.app_context():
            from flask_jwt_extended import decode_token

            decoded = decode_token(token)
        role = decoded.get("role")
        user_id = _positive_int(decoded.get("sub"))
        if role not in {
            "interviewer", "recruiter", "sector_admin", "proctor", "admin", "super_admin"
        } or user_id is None:
            return None
        user = get_user_by_id(user_id)
        if (
            not user
            or user.get("role") != role
            or decoded.get("user_auth_version") != user_auth_version(user)
            or (
                role in {"recruiter", "sector_admin"}
                and user.get("sector_id") is None
            )
        ):
            return None
        return user_id, role
    except Exception:
        logger.warning("Proctoring JWT decode failed", exc_info=True)
        return None


def _verify_staff_assessment_access(user_id, role, assessment_id):
    """Require an active assessment assignment, except for system administrators."""

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sa.interviewer_id, sa.proctor_id, c.sector_id, staff.sector_id
            FROM assessments a
            JOIN scheduled_assessments sa ON sa.id = a.scheduled_assessment_id
            JOIN candidates c ON c.id = a.candidate_id
            JOIN users staff ON staff.id = %s
            WHERE a.id = %s
              AND a.status IN ('started', 'in_progress')
              AND sa.status = 'in_progress'
        """, (user_id, assessment_id))
        assignment = cursor.fetchone()
        if assignment is None:
            return False
        if role in {"admin", "super_admin"}:
            return True
        if role == "interviewer":
            return assignment[0] == user_id
        if role in {"recruiter", "sector_admin"}:
            return (
                assignment[0] == user_id
                and assignment[2] is not None
                and assignment[2] == assignment[3]
            )
        return role == "proctor" and assignment[1] == user_id
    except Exception:
        logger.exception("Staff access verification failed for assessment %s", assessment_id)
        return False
    finally:
        if cursor is not None:
            with contextlib.suppress(Exception):
                cursor.close()
        if conn is not None:
            return_connection(conn)


def _emit_error(sid, message):
    sio.emit("error", {"message": message}, room=sid)


def _socket_identity_key(identity):
    if identity.get("type") == "candidate":
        return "candidate", identity.get("assessment_id")
    return (
        "staff",
        identity.get("user_id"),
        identity.get("assessment_id"),
    )


@sio.event
def connect(sid, environ, auth=None):
    if not isinstance(auth, dict):
        return False
    assessment_id = _positive_int(auth.get("assessment_id"))
    if assessment_id is None:
        return False

    requested_role = auth.get("role")
    if requested_role == "candidate":
        access_token = auth.get("access_token")
        if not _verify_candidate_token(access_token, assessment_id):
            return False
        identity = {"type": "candidate", "assessment_id": assessment_id}
    elif requested_role == "staff":
        staff = _verify_interviewer_jwt(auth.get("token"))
        if staff is None:
            return False
        user_id, role = staff
        if not _verify_staff_assessment_access(user_id, role, assessment_id):
            return False
        identity = {
            "type": "interviewer",
            "assessment_id": assessment_id,
            "user_id": user_id,
            "role": role,
        }
    else:
        return False

    identity_key = _socket_identity_key(identity)
    with _state_lock:
        if any(
            _socket_identity_key(existing) == identity_key
            for existing in authenticated_sockets.values()
        ):
            return False
        authenticated_sockets[sid] = identity
    logger.info("Proctoring socket connected: %s", sid)
    return True


@sio.event
def disconnect(sid):
    logger.info("Proctoring socket disconnected: %s", sid)
    candidate_notification = None
    interviewer_notifications = []
    with _state_lock:
        authenticated_sockets.pop(sid, None)
        connection = connections.pop(sid, None)
        if connection is None:
            return
        assessment_id = connection.get("assessment_id")
        room = active_rooms.get(assessment_id)
        if room is None:
            return

        if connection.get("type") == "candidate" and room.get("candidate") == sid:
            room["candidate"] = None
            interviewer_notifications = list(room.get("interviewers", []))
        elif connection.get("type") == "interviewer":
            with contextlib.suppress(ValueError):
                room.get("interviewers", []).remove(sid)
            candidate_notification = room.get("candidate")

        if room.get("candidate") is None and not room.get("interviewers"):
            active_rooms.pop(assessment_id, None)

    for interviewer_sid in interviewer_notifications:
        sio.emit("candidate_disconnected", {"assessment_id": assessment_id}, room=interviewer_sid)
    if candidate_notification:
        sio.emit("interviewer_disconnected", {"assessment_id": assessment_id}, room=candidate_notification)


@sio.event
def join_as_candidate(sid, data):
    if not isinstance(data, dict):
        _emit_error(sid, "Invalid join payload")
        return
    assessment_id = _positive_int(data.get("assessment_id"))
    with _state_lock:
        authenticated = authenticated_sockets.get(sid, {})
    if (
        assessment_id is None
        or authenticated.get("type") != "candidate"
        or authenticated.get("assessment_id") != assessment_id
    ):
        _emit_error(sid, "Socket authentication required for this assessment")
        return

    join_error = None
    interviewer_sids = []
    with _state_lock:
        if sid in connections:
            join_error = "Socket has already joined a proctoring room"
        else:
            room = active_rooms.setdefault(
                assessment_id, {"candidate": None, "interviewers": []}
            )
            existing_candidate = room.get("candidate")
            if existing_candidate and existing_candidate in connections:
                join_error = "Candidate is already connected to this assessment"
            else:
                room["candidate"] = sid
                connections[sid] = {"type": "candidate", "assessment_id": assessment_id}
                interviewer_sids = list(room.get("interviewers", []))
    if join_error:
        _emit_error(sid, join_error)
        return

    sio.enter_room(sid, f"assessment_{assessment_id}")
    for interviewer_sid in interviewer_sids:
        sio.emit("candidate_joined", {"assessment_id": assessment_id}, room=interviewer_sid)
    sio.emit("joined", {
        "assessment_id": assessment_id,
        "role": "candidate",
        "interviewers_present": bool(interviewer_sids),
    }, room=sid)
    if interviewer_sids:
        sio.emit("interviewer_joined", {}, room=sid)


@sio.event
def join_as_interviewer(sid, data):
    if not isinstance(data, dict):
        _emit_error(sid, "Invalid join payload")
        return
    assessment_id = _positive_int(data.get("assessment_id"))
    if assessment_id is None:
        _emit_error(sid, "Missing assessment_id")
        return
    with _state_lock:
        authenticated = authenticated_sockets.get(sid, {})
    if (
        authenticated.get("type") != "interviewer"
        or authenticated.get("assessment_id") != assessment_id
    ):
        _emit_error(sid, "Socket authentication required for this assessment")
        return
    user_id = authenticated["user_id"]
    role = authenticated["role"]

    join_error = None
    candidate_sid = None
    with _state_lock:
        if sid in connections:
            join_error = "Socket has already joined a proctoring room"
        else:
            room = active_rooms.setdefault(
                assessment_id, {"candidate": None, "interviewers": []}
            )
            room["interviewers"].append(sid)
            connections[sid] = {
                "type": "interviewer",
                "assessment_id": assessment_id,
                "user_id": user_id,
                "role": role,
            }
            candidate_sid = room.get("candidate")
    if join_error:
        _emit_error(sid, join_error)
        return

    sio.enter_room(sid, f"assessment_{assessment_id}")
    sio.emit("joined", {
        "assessment_id": assessment_id,
        "role": "interviewer",
        "candidate_present": candidate_sid is not None,
    }, room=sid)
    if candidate_sid:
        sio.emit("interviewer_joined", {}, room=candidate_sid)


@sio.event
def webrtc_offer(sid, data):
    if not isinstance(data, dict) or data.get("offer") is None:
        _emit_error(sid, "Invalid WebRTC offer")
        return
    assessment_id = _positive_int(data.get("assessment_id"))
    authorized = False
    interviewer_sids = []
    with _state_lock:
        connection = connections.get(sid, {})
        room = active_rooms.get(assessment_id)
        authorized = (
            room is not None
            and connection.get("type") == "candidate"
            and connection.get("assessment_id") == assessment_id
            and room.get("candidate") == sid
        )
        if authorized:
            interviewer_sids = list(room.get("interviewers", []))
    if not authorized:
        _emit_error(sid, "Not authorized for this assessment")
        return
    for interviewer_sid in interviewer_sids:
        sio.emit("webrtc_offer", {
            "assessment_id": assessment_id,
            "offer": data["offer"],
        }, room=interviewer_sid)


@sio.event
def webrtc_answer(sid, data):
    if not isinstance(data, dict) or data.get("answer") is None:
        _emit_error(sid, "Invalid WebRTC answer")
        return
    assessment_id = _positive_int(data.get("assessment_id"))
    authorized = False
    candidate_sid = None
    with _state_lock:
        connection = connections.get(sid, {})
        room = active_rooms.get(assessment_id)
        authorized = (
            room is not None
            and connection.get("type") == "interviewer"
            and connection.get("assessment_id") == assessment_id
            and sid in room.get("interviewers", [])
        )
        if authorized:
            candidate_sid = room.get("candidate")
    if not authorized:
        _emit_error(sid, "Not authorized for this assessment")
        return
    if candidate_sid:
        sio.emit("webrtc_answer", {
            "assessment_id": assessment_id,
            "answer": data["answer"],
        }, room=candidate_sid)


@sio.event
def ice_candidate(sid, data):
    if not isinstance(data, dict) or data.get("candidate") is None:
        _emit_error(sid, "Invalid ICE candidate")
        return
    assessment_id = _positive_int(data.get("assessment_id"))
    target = data.get("target", "interviewer")
    routing_error = None
    recipients = []
    with _state_lock:
        connection = connections.get(sid, {})
        room = active_rooms.get(assessment_id)
        if room is None or connection.get("assessment_id") != assessment_id:
            routing_error = "Not authorized for this assessment"
        else:
            sender_type = connection.get("type")
            if (
                target == "interviewer"
                and sender_type == "candidate"
                and room.get("candidate") == sid
            ):
                recipients = list(room.get("interviewers", []))
            elif (
                target == "candidate"
                and sender_type == "interviewer"
                and sid in room.get("interviewers", [])
            ):
                recipients = [room.get("candidate")] if room.get("candidate") else []
            else:
                routing_error = "Invalid ICE routing target"
    if routing_error:
        _emit_error(sid, routing_error)
        return
    for recipient in recipients:
        sio.emit("ice_candidate", {
            "assessment_id": assessment_id,
            "candidate": data["candidate"],
        }, room=recipient)


@sio.event
def get_active_assessments(sid, data):
    authorized = False
    assessments = []
    with _state_lock:
        connection = connections.get(sid, {})
        assessment_id = connection.get("assessment_id")
        room = active_rooms.get(assessment_id)
        authorized = connection.get("type") == "interviewer" and room is not None
        if authorized:
            assessments = [{
                "assessment_id": assessment_id,
                "has_candidate": room.get("candidate") is not None,
                "interviewer_count": len(room.get("interviewers", [])),
            }]
    if not authorized:
        _emit_error(sid, "Not authorized")
        return
    sio.emit("active_assessments", {"assessments": assessments}, room=sid)


def get_socketio_app():
    return sio
