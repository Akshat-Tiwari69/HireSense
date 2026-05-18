import React, { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import SimplePeer from 'simple-peer';
import { X, Wifi, WifiOff, Video, Loader2 } from 'lucide-react';
import { API_BASE_URL } from '../services/api';
import './ProctorMonitor.css';

const ProctorMonitor = ({ assessmentId, onClose }) => {
    const [connected, setConnected] = useState(false);
    const [candidatePresent, setCandidatePresent] = useState(false);
    const [error, setError] = useState(null);
    const [hasActiveStream, setHasActiveStream] = useState(false);

    const socketRef = useRef(null);
    const peerRef = useRef(null);
    const videoRef = useRef(null);

    useEffect(() => {
        // Connect to Socket.IO server using dynamic API URL
        const socket = io(API_BASE_URL, {
            transports: ['websocket', 'polling']
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('[PROCTOR] Connected to server');
            setConnected(true);

            const userId = localStorage.getItem('user_id') || '1';
            const token = localStorage.getItem('authToken');
            socket.emit('join_as_interviewer', {
                assessment_id: assessmentId,
                user_id: parseInt(userId),
                token: token,
            });
        });

        socket.on('joined', (data) => {
            console.log('[PROCTOR] Joined room:', data);
            setCandidatePresent(data.candidate_present);
        });

        socket.on('candidate_joined', (data) => {
            console.log('[PROCTOR] Candidate joined');
            setCandidatePresent(true);
            setError(null); // Clear any previous errors
        });

        socket.on('webrtc_offer', (data) => {
            console.log('[PROCTOR] Received WebRTC offer');
            handleOffer(data.offer);
        });

        socket.on('ice_candidate', (data) => {
            console.log('[PROCTOR] Received ICE candidate');
            if (peerRef.current) {
                peerRef.current.signal(data.candidate);
            }
        });

        socket.on('candidate_disconnected', () => {
            console.log('[PROCTOR] Candidate disconnected');
            setCandidatePresent(false);
            setHasActiveStream(false);
            if (peerRef.current) {
                peerRef.current.destroy();
                peerRef.current = null;
            }
        });

        socket.on('error', (data) => {
            console.error('[PROCTOR] Socket error:', data);
            setError(data.message);
        });

        socket.on('disconnect', () => {
            console.log('[PROCTOR] Disconnected from server');
            setConnected(false);
        });

        return () => {
            if (peerRef.current) {
                peerRef.current.destroy();
            }
            socket.disconnect();
        };
    }, [assessmentId]);

    const handleOffer = (offer) => {
        // Create peer connection as receiver
        const peer = new SimplePeer({
            initiator: false,
            trickle: true,
            config: {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' }
                ]
            }
        });

        peerRef.current = peer;

        peer.on('signal', (data) => {
            if (data.type === 'answer') {
                console.log('[PROCTOR] Sending answer');
                socketRef.current.emit('webrtc_answer', {
                    assessment_id: assessmentId,
                    answer: data
                });
            } else {
                // ICE candidate
                socketRef.current.emit('ice_candidate', {
                    assessment_id: assessmentId,
                    candidate: data,
                    target: 'candidate'
                });
            }
        });

        peer.on('stream', (stream) => {
            console.log('[PROCTOR] Received video stream');
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                setHasActiveStream(true);
                setError(null); // Clear errors when stream is active
            }
        });

        peer.on('error', (err) => {
            console.error('[PROCTOR] Peer error:', err);
            setError(`Connection error: ${err.message}`);
        });

        peer.signal(offer);
    };

    return (
        <div className="proctor-monitor-overlay">
            <div className="proctor-monitor-container">
                <div className="proctor-monitor-header">
                    <div className="header-left">
                        <h2>Live Proctoring</h2>
                        <div className="header-status-icons">
                            {connected ? (
                                <Wifi className="w-4 h-4 text-green-400" title="Connection Active" />
                            ) : (
                                <WifiOff className="w-4 h-4 text-red-400" title="Connection Lost" />
                            )}
                            {candidatePresent ? (
                                <Video className="w-4 h-4 text-blue-400" title="Live Stream Active" />
                            ) : (
                                <Loader2 className="w-4 h-4 text-yellow-400 animate-spin" title="Awaiting Candidate" />
                            )}
                        </div>
                    </div>
                    <button onClick={onClose} className="close-button" aria-label="Close">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <div className="proctor-monitor-content">

                    <div className="video-container">
                        {error && !hasActiveStream && (
                            <div className="error-message">
                                 {error}
                            </div>
                        )}

                        {!candidatePresent && !error && (
                            <div className="waiting-message">
                                <div className="spinner"></div>
                                <p>Waiting for candidate to join...</p>
                            </div>
                        )}

                        <video
                            ref={videoRef}
                            autoPlay
                            playsInline
                            className="candidate-video"
                            style={{ display: hasActiveStream ? 'block' : 'none' }}
                        />
                    </div>

                    <div className="proctor-info">
                        <p className="info-text">
                             Monitor the candidate's camera feed during the assessment
                        </p>
                        <p className="info-text">
                             This feed is secure and only visible to authorized interviewers
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ProctorMonitor;
