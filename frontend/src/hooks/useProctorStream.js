import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import SimplePeer from 'simple-peer';
import { API_BASE_URL } from '../services/api';

/**
 * Hook for candidate-side WebRTC video streaming to interviewer
 * @param {number} assessmentId - ID of the current assessment
 * @param {string} accessToken - Assessment access token
 * @param {boolean} enabled - Whether streaming is enabled
 */
export const useProctorStream = (assessmentId, accessToken, enabled) => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [streamError, setStreamError] = useState(null);

    const socketRef = useRef(null);
    const peerRef = useRef(null);
    const localStreamRef = useRef(null);

    useEffect(() => {
        if (!enabled || !assessmentId || !accessToken) {
            return;
        }

        // Connect to Socket.IO server using dynamic API URL
        const socket = io(API_BASE_URL, {
            transports: ['websocket', 'polling']
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[STREAM] Connected to server');

            // Get camera stream
            navigator.mediaDevices.getUserMedia({
                video: {
                    facingMode: 'user',
                    width: { ideal: 640 },
                    height: { ideal: 480 }
                },
                audio: false // No audio for proctoring
            })
                .then(stream => {
                    localStreamRef.current = stream;

                    // Join as candidate
                    socket.emit('join_as_candidate', {
                        assessment_id: assessmentId,
                        access_token: accessToken
                    });
                })
                .catch(err => {
                    console.error('[STREAM] Camera error:', err);
                    setStreamError('Failed to access camera');
                });
        });

        socket.on('joined', (data) => {
            console.log('[STREAM] Joined room:', data);
            setIsStreaming(true);
        });

        socket.on('interviewer_joined', () => {
            console.log('[STREAM] Interviewer joined, initiating peer connection');
            initiatePeerConnection();
        });

        socket.on('webrtc_answer', (data) => {
            console.log('[STREAM] Received answer');
            if (peerRef.current) {
                peerRef.current.signal(data.answer);
            }
        });

        socket.on('ice_candidate', (data) => {
            console.log('[STREAM] Received ICE candidate');
            if (peerRef.current) {
                peerRef.current.signal(data.candidate);
            }
        });

        socket.on('error', (data) => {
            console.error('[STREAM] Socket error:', data);
            setStreamError(data.message);
        });

        socket.on('disconnect', () => {
            console.log('[STREAM] Disconnected');
            setIsStreaming(false);
        });

        const initiatePeerConnection = () => {
            if (!localStreamRef.current) {
                console.error('[STREAM] No local stream available');
                return;
            }

            // Create peer connection as initiator
            const peer = new SimplePeer({
                initiator: true,
                trickle: true,
                stream: localStreamRef.current,
                config: {
                    iceServers: [
                        { urls: 'stun:stun.l.google.com:19302' },
                        { urls: 'stun:stun1.l.google.com:19302' }
                    ]
                }
            });

            peerRef.current = peer;

            peer.on('signal', (data) => {
                if (data.type === 'offer') {
                    console.log('[STREAM] Sending offer');
                    socket.emit('webrtc_offer', {
                        assessment_id: assessmentId,
                        offer: data
                    });
                } else {
                    // ICE candidate
                    socket.emit('ice_candidate', {
                        assessment_id: assessmentId,
                        candidate: data,
                        target: 'interviewer'
                    });
                }
            });

            peer.on('connect', () => {
                console.log('[STREAM] Peer connected');
            });

            peer.on('error', (err) => {
                console.error('[STREAM] Peer error:', err);
                setStreamError(`Connection error: ${err.message}`);
            });
        };

        // Cleanup
        return () => {
            if (peerRef.current) {
                peerRef.current.destroy();
            }
            if (localStreamRef.current) {
                localStreamRef.current.getTracks().forEach(track => track.stop());
            }
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, [assessmentId, accessToken, enabled]);

    return { isStreaming, streamError };
};
