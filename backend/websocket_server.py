"""
WebSocket Server for Live Proctoring
Handles WebRTC signaling for real-time video streaming from candidates to interviewers.
"""
import socketio
import logging
from db_config import get_connection

logger = logging.getLogger(__name__)

sio = socketio.Server(
    cors_allowed_origins='*',
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

# {assessment_id: {'candidate': sid, 'interviewers': [sid1, ...]}}
active_rooms = {}
# {sid: {'type': 'candidate'|'interviewer', 'assessment_id': id, 'user_id': id}}
connections = {}

# Injected by app.py so event handlers can push a Flask app context for JWT decode
_flask_app = None


def init_websocket_server(app):
    global _flask_app
    _flask_app = app


def _verify_candidate_token(access_token, assessment_id):
    """Return True if access_token is valid for the given assessment_id."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id FROM scheduled_assessments
               WHERE access_token = %s AND id = %s AND status != 'cancelled'""",
            (access_token, assessment_id)
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error(f"[PROCTORING] Token verification DB error: {e}")
        return False


def _verify_interviewer_jwt(token):
    """Return (user_id, role) if JWT is valid and role is staff, else None."""
    if not _flask_app or not token:
        return None
    try:
        with _flask_app.app_context():
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            role = decoded.get('role') or (decoded.get('sub', {}) or {}).get('role')
            user_id = decoded.get('sub')
            if role not in ('interviewer', 'proctor', 'admin', 'super_admin'):
                return None
            return user_id, role
    except Exception as e:
        logger.warning(f"[PROCTORING] JWT decode failed: {e}")
        return None


@sio.event
def connect(sid, environ):
    logger.info(f"[PROCTORING] New connection: {sid}")
    return True


@sio.event
def disconnect(sid):
    logger.info(f"[PROCTORING] Disconnect: {sid}")

    if sid in connections:
        conn_info = connections[sid]
        assessment_id = conn_info.get('assessment_id')
        user_type = conn_info.get('type')

        if assessment_id and assessment_id in active_rooms:
            room = active_rooms[assessment_id]

            if user_type == 'candidate' and room.get('candidate') == sid:
                room['candidate'] = None
                for interviewer_sid in room.get('interviewers', []):
                    sio.emit('candidate_disconnected', {'assessment_id': assessment_id}, room=interviewer_sid)
                logger.info(f"[PROCTORING] Candidate disconnected from assessment {assessment_id}")

            elif user_type == 'interviewer':
                if sid in room.get('interviewers', []):
                    room['interviewers'].remove(sid)
                logger.info(f"[PROCTORING] Interviewer disconnected from assessment {assessment_id}")

            if not room.get('candidate') and not room.get('interviewers'):
                del active_rooms[assessment_id]
                logger.info(f"[PROCTORING] Room {assessment_id} deleted (empty)")

        del connections[sid]


@sio.event
def join_as_candidate(sid, data):
    """
    Candidate joins proctoring room.
    Data: {'assessment_id': int, 'access_token': str}
    """
    try:
        assessment_id = data.get('assessment_id')
        access_token = data.get('access_token')

        if not assessment_id or not access_token:
            sio.emit('error', {'message': 'Missing assessment_id or access_token'}, room=sid)
            return

        if not _verify_candidate_token(access_token, assessment_id):
            logger.warning(f"[PROCTORING] Invalid token for assessment {assessment_id} from {sid}")
            sio.emit('error', {'message': 'Invalid or expired assessment token'}, room=sid)
            return

        if assessment_id not in active_rooms:
            active_rooms[assessment_id] = {'candidate': None, 'interviewers': []}

        active_rooms[assessment_id]['candidate'] = sid
        connections[sid] = {'type': 'candidate', 'assessment_id': assessment_id}

        sio.enter_room(sid, f'assessment_{assessment_id}')

        for interviewer_sid in active_rooms[assessment_id].get('interviewers', []):
            sio.emit('candidate_joined', {'assessment_id': assessment_id}, room=interviewer_sid)

        interviewers_present = len(active_rooms[assessment_id].get('interviewers', [])) > 0
        sio.emit('joined', {
            'assessment_id': assessment_id,
            'role': 'candidate',
            'interviewers_present': interviewers_present
        }, room=sid)

        if interviewers_present:
            sio.emit('interviewer_joined', {}, room=sid)

        logger.info(f"[PROCTORING] Verified candidate joined assessment {assessment_id}")

    except Exception as e:
        logger.error(f"[PROCTORING] Error in join_as_candidate: {e}")
        sio.emit('error', {'message': 'Failed to join proctoring room'}, room=sid)


@sio.event
def join_as_interviewer(sid, data):
    """
    Interviewer/proctor joins to monitor assessment.
    Data: {'assessment_id': int, 'user_id': int, 'token': str}
    """
    try:
        assessment_id = data.get('assessment_id')
        token = data.get('token')

        if not assessment_id:
            sio.emit('error', {'message': 'Missing assessment_id'}, room=sid)
            return

        result = _verify_interviewer_jwt(token)
        if result is None:
            logger.warning(f"[PROCTORING] Unauthorized interviewer join attempt for assessment {assessment_id}")
            sio.emit('error', {'message': 'Unauthorized — valid JWT required'}, room=sid)
            return

        user_id, role = result

        if assessment_id not in active_rooms:
            active_rooms[assessment_id] = {'candidate': None, 'interviewers': []}

        if sid not in active_rooms[assessment_id]['interviewers']:
            active_rooms[assessment_id]['interviewers'].append(sid)

        connections[sid] = {'type': 'interviewer', 'assessment_id': assessment_id, 'user_id': user_id}

        sio.enter_room(sid, f'assessment_{assessment_id}')

        candidate_sid = active_rooms[assessment_id].get('candidate')
        candidate_present = candidate_sid is not None

        sio.emit('joined', {
            'assessment_id': assessment_id,
            'role': 'interviewer',
            'candidate_present': candidate_present
        }, room=sid)

        if candidate_present:
            sio.emit('interviewer_joined', {}, room=candidate_sid)

        logger.info(f"[PROCTORING] Verified interviewer (user {user_id}, role {role}) joined assessment {assessment_id}")

    except Exception as e:
        logger.error(f"[PROCTORING] Error in join_as_interviewer: {e}")
        sio.emit('error', {'message': 'Failed to join proctoring room'}, room=sid)


@sio.event
def webrtc_offer(sid, data):
    """Forward WebRTC offer from candidate to interviewers."""
    try:
        assessment_id = data.get('assessment_id')
        offer = data.get('offer')

        if assessment_id not in active_rooms:
            return

        # Only allow if sender is the registered candidate for this room
        if connections.get(sid, {}).get('assessment_id') != assessment_id:
            return

        for interviewer_sid in active_rooms[assessment_id].get('interviewers', []):
            sio.emit('webrtc_offer', {'assessment_id': assessment_id, 'offer': offer}, room=interviewer_sid)

    except Exception as e:
        logger.error(f"[PROCTORING] Error in webrtc_offer: {e}")


@sio.event
def webrtc_answer(sid, data):
    """Forward WebRTC answer from interviewer to candidate."""
    try:
        assessment_id = data.get('assessment_id')
        answer = data.get('answer')

        if assessment_id not in active_rooms:
            return

        candidate_sid = active_rooms[assessment_id].get('candidate')
        if candidate_sid:
            sio.emit('webrtc_answer', {'assessment_id': assessment_id, 'answer': answer}, room=candidate_sid)

    except Exception as e:
        logger.error(f"[PROCTORING] Error in webrtc_answer: {e}")


@sio.event
def ice_candidate(sid, data):
    """Forward ICE candidate between peers."""
    try:
        assessment_id = data.get('assessment_id')
        ice = data.get('candidate')
        target = data.get('target', 'interviewer')

        if assessment_id not in active_rooms:
            return

        room = active_rooms[assessment_id]

        if target == 'interviewer':
            for interviewer_sid in room.get('interviewers', []):
                sio.emit('ice_candidate', {'assessment_id': assessment_id, 'candidate': ice}, room=interviewer_sid)
        else:
            candidate_sid = room.get('candidate')
            if candidate_sid:
                sio.emit('ice_candidate', {'assessment_id': assessment_id, 'candidate': ice}, room=candidate_sid)

    except Exception as e:
        logger.error(f"[PROCTORING] Error in ice_candidate: {e}")


@sio.event
def get_active_assessments(sid, data):
    """Return list of active proctoring rooms — staff only."""
    try:
        if connections.get(sid, {}).get('type') != 'interviewer':
            sio.emit('error', {'message': 'Not authorized'}, room=sid)
            return

        assessments = [
            {
                'assessment_id': aid,
                'has_candidate': room.get('candidate') is not None,
                'interviewer_count': len(room.get('interviewers', []))
            }
            for aid, room in active_rooms.items()
        ]
        sio.emit('active_assessments', {'assessments': assessments}, room=sid)

    except Exception as e:
        logger.error(f"[PROCTORING] Error in get_active_assessments: {e}")


def get_socketio_app():
    return sio
