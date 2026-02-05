"""
WebSocket Server for Live Proctoring
Handles WebRTC signaling for real-time video streaming from candidates to interviewers.
"""
import socketio
from flask import request
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO server instance
sio = socketio.Server(
    cors_allowed_origins='*',  # Allow all origins for development
    async_mode='eventlet',  # Must match the WSGI server (eventlet)
    logger=True,
    engineio_logger=True
)

# Store active connections: {assessment_id: {'candidate': sid, 'interviewers': [sid1, sid2]}}
active_rooms = {}

# Store user info: {sid: {'type': 'candidate'|'interviewer', 'assessment_id': id, 'user_id': id}}
connections = {}


@sio.event
def connect(sid, environ):
    """Handle new WebSocket connection"""
    logger.info(f"[PROCTORING] New connection: {sid}")
    return True


@sio.event
def disconnect(sid):
    """Handle WebSocket disconnection"""
    logger.info(f"[PROCTORING] Disconnect: {sid}")
    
    # Clean up connection
    if sid in connections:
        conn_info = connections[sid]
        assessment_id = conn_info.get('assessment_id')
        user_type = conn_info.get('type')
        
        if assessment_id and assessment_id in active_rooms:
            room = active_rooms[assessment_id]
            
            if user_type == 'candidate' and room.get('candidate') == sid:
                # Candidate disconnected - notify interviewers
                room['candidate'] = None
                for interviewer_sid in room.get('interviewers', []):
                    sio.emit('candidate_disconnected', {
                        'assessment_id': assessment_id
                    }, room=interviewer_sid)
                logger.info(f"[PROCTORING] Candidate disconnected from assessment {assessment_id}")
                
            elif user_type == 'interviewer':
                # Interviewer disconnected
                if sid in room.get('interviewers', []):
                    room['interviewers'].remove(sid)
                logger.info(f"[PROCTORING] Interviewer disconnected from assessment {assessment_id}")
            
            # Clean up empty room
            if not room.get('candidate') and not room.get('interviewers'):
                del active_rooms[assessment_id]
                logger.info(f"[PROCTORING] Room {assessment_id} deleted (empty)")
        
        del connections[sid]


@sio.event
def join_as_candidate(sid, data):
    """
    Candidate joins proctoring room
    Data: {'assessment_id': int, 'access_token': str}
    """
    try:
        assessment_id = data.get('assessment_id')
        access_token = data.get('access_token')
        
        if not assessment_id or not access_token:
            sio.emit('error', {'message': 'Missing assessment_id or access_token'}, room=sid)
            return
        
        # TODO: Verify access_token is valid for this assessment
        # For now, we'll trust it
        
        # Create room if doesn't exist
        if assessment_id not in active_rooms:
            active_rooms[assessment_id] = {'candidate': None, 'interviewers': []}
        
        # Join room
        active_rooms[assessment_id]['candidate'] = sid
        connections[sid] = {
            'type': 'candidate',
            'assessment_id': assessment_id,
            'access_token': access_token
        }
        
        sio.enter_room(sid, f'assessment_{assessment_id}')
        
        # Notify interviewers that candidate joined
        for interviewer_sid in active_rooms[assessment_id].get('interviewers', []):
            sio.emit('candidate_joined', {
                'assessment_id': assessment_id
            }, room=interviewer_sid)
        
        # Check if interviewers are already present
        interviewers_present = len(active_rooms[assessment_id].get('interviewers', [])) > 0
        
        sio.emit('joined', {
            'assessment_id': assessment_id,
            'role': 'candidate',
            'interviewers_present': interviewers_present
        }, room=sid)
        
        # If interviewers already present, tell candidate to initiate connection
        if interviewers_present:
            sio.emit('interviewer_joined', {}, room=sid)
            logger.info(f"[PROCTORING] Notifying candidate that interviewers are present")
        
        logger.info(f"[PROCTORING] Candidate {sid} joined assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in join_as_candidate: {e}")
        sio.emit('error', {'message': str(e)}, room=sid)


@sio.event
def join_as_interviewer(sid, data):
    """
    Interviewer joins to monitor assessment
    Data: {'assessment_id': int, 'user_id': int}
    """
    try:
        assessment_id = data.get('assessment_id')
        user_id = data.get('user_id')
        
        if not assessment_id or not user_id:
            sio.emit('error', {'message': 'Missing assessment_id or user_id'}, room=sid)
            return
        
        # TODO: Verify user_id has permission to monitor this assessment
        
        # Create room if doesn't exist
        if assessment_id not in active_rooms:
            active_rooms[assessment_id] = {'candidate': None, 'interviewers': []}
        
        # Join room
        if sid not in active_rooms[assessment_id]['interviewers']:
            active_rooms[assessment_id]['interviewers'].append(sid)
        
        connections[sid] = {
            'type': 'interviewer',
            'assessment_id': assessment_id,
            'user_id': user_id
        }
        
        sio.enter_room(sid, f'assessment_{assessment_id}')
        
        # Check if candidate is already streaming
        candidate_sid = active_rooms[assessment_id].get('candidate')
        candidate_present = candidate_sid is not None
        
        sio.emit('joined', {
            'assessment_id': assessment_id,
            'role': 'interviewer',
            'candidate_present': candidate_present
        }, room=sid)
        
        # If candidate is present, notify them
        if candidate_present:
            sio.emit('interviewer_joined', {}, room=candidate_sid)
        
        logger.info(f"[PROCTORING] Interviewer {sid} joined assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in join_as_interviewer: {e}")
        sio.emit('error', {'message': str(e)}, room=sid)


@sio.event
def webrtc_offer(sid, data):
    """
    Forward WebRTC offer from candidate to interviewers
    Data: {'assessment_id': int, 'offer': RTCSessionDescription}
    """
    try:
        assessment_id = data.get('assessment_id')
        offer = data.get('offer')
        
        if assessment_id not in active_rooms:
            logger.warning(f"[PROCTORING] Offer for non-existent room {assessment_id}")
            return
        
        # Forward to all interviewers
        for interviewer_sid in active_rooms[assessment_id].get('interviewers', []):
            sio.emit('webrtc_offer', {
                'assessment_id': assessment_id,
                'offer': offer
            }, room=interviewer_sid)
        
        logger.info(f"[PROCTORING] Forwarded offer for assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in webrtc_offer: {e}")


@sio.event
def webrtc_answer(sid, data):
    """
    Forward WebRTC answer from interviewer to candidate
    Data: {'assessment_id': int, 'answer': RTCSessionDescription}
    """
    try:
        assessment_id = data.get('assessment_id')
        answer = data.get('answer')
        
        if assessment_id not in active_rooms:
            logger.warning(f"[PROCTORING] Answer for non-existent room {assessment_id}")
            return
        
        # Forward to candidate
        candidate_sid = active_rooms[assessment_id].get('candidate')
        if candidate_sid:
            sio.emit('webrtc_answer', {
                'assessment_id': assessment_id,
                'answer': answer
            }, room=candidate_sid)
            logger.info(f"[PROCTORING] Forwarded answer for assessment {assessment_id}")
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in webrtc_answer: {e}")


@sio.event
def ice_candidate(sid, data):
    """
    Forward ICE candidate between peers
    Data: {'assessment_id': int, 'candidate': RTCIceCandidate, 'target': 'candidate'|'interviewer'}
    """
    try:
        assessment_id = data.get('assessment_id')
        ice_candidate = data.get('candidate')
        target = data.get('target', 'interviewer')
        
        if assessment_id not in active_rooms:
            return
        
        room = active_rooms[assessment_id]
        
        if target == 'interviewer':
            # Forward to all interviewers
            for interviewer_sid in room.get('interviewers', []):
                sio.emit('ice_candidate', {
                    'assessment_id': assessment_id,
                    'candidate': ice_candidate
                }, room=interviewer_sid)
        else:
            # Forward to candidate
            candidate_sid = room.get('candidate')
            if candidate_sid:
                sio.emit('ice_candidate', {
                    'assessment_id': assessment_id,
                    'candidate': ice_candidate
                }, room=candidate_sid)
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in ice_candidate: {e}")


@sio.event
def get_active_assessments(sid, data):
    """
    Get list of all active assessments being streamed
    Returns: {'assessments': [{'assessment_id': int, 'has_candidate': bool, 'interviewer_count': int}]}
    """
    try:
        assessments = []
        for assessment_id, room in active_rooms.items():
            assessments.append({
                'assessment_id': assessment_id,
                'has_candidate': room.get('candidate') is not None,
                'interviewer_count': len(room.get('interviewers', []))
            })
        
        sio.emit('active_assessments', {'assessments': assessments}, room=sid)
        logger.info(f"[PROCTORING] Sent active assessments list to {sid}")
        
    except Exception as e:
        logger.error(f"[PROCTORING] Error in get_active_assessments: {e}")


def get_socketio_app():
    """Get the Socket.IO server instance"""
    return sio
