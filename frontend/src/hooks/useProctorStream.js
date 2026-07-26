import { useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import SimplePeer from 'simple-peer';

import { API_BASE_URL } from '../services/api';

const CAMERA_CONSTRAINTS = {
  video: {
    facingMode: 'user',
    width: { ideal: 640 },
    height: { ideal: 480 },
  },
  audio: false,
};

/**
 * Owns the candidate camera and optional WebRTC connection for one assessment.
 * Keeping camera acquisition here prevents duplicate browser media streams.
 */
export const useProctorStream = (assessmentId, accessToken, enabled) => {
  const [mediaStream, setMediaStream] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState(null);
  const peerRef = useRef(null);

  useEffect(() => {
    if (!enabled || !assessmentId || !accessToken) return undefined;

    let cancelled = false;
    let localStream = null;
    const socket = io(API_BASE_URL || window.location.origin, {
      transports: ['websocket', 'polling'],
      auth: {
        role: 'candidate',
        assessment_id: assessmentId,
        access_token: accessToken,
      },
    });

    const destroyPeer = () => {
      peerRef.current?.destroy();
      peerRef.current = null;
    };

    const startPeer = () => {
      if (!localStream || peerRef.current) return;

      const peer = new SimplePeer({
        initiator: true,
        trickle: true,
        stream: localStream,
        config: {
          iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
          ],
        },
      });
      peerRef.current = peer;

      peer.on('signal', (signal) => {
        if (signal.type === 'offer') {
          socket.emit('webrtc_offer', { assessment_id: assessmentId, offer: signal });
        } else {
          socket.emit('ice_candidate', {
            assessment_id: assessmentId,
            candidate: signal,
            target: 'interviewer',
          });
        }
      });
      peer.on('error', () => {
        setStreamError('The live proctor connection was interrupted.');
        destroyPeer();
      });
      peer.on('close', () => {
        if (peerRef.current === peer) peerRef.current = null;
      });
    };

    socket.on('connect', async () => {
      if (localStream) {
        socket.emit('join_as_candidate', {
          assessment_id: assessmentId,
          access_token: accessToken,
        });
        return;
      }
      try {
        localStream = await navigator.mediaDevices.getUserMedia(CAMERA_CONSTRAINTS);
        if (cancelled) {
          localStream.getTracks().forEach((track) => track.stop());
          return;
        }

        for (const track of localStream.getVideoTracks()) {
          track.addEventListener('ended', () => {
            setIsStreaming(false);
            setStreamError('Camera access ended during the assessment.');
          });
        }

        setMediaStream(localStream);
        setStreamError(null);
        socket.emit('join_as_candidate', {
          assessment_id: assessmentId,
          access_token: accessToken,
        });
      } catch {
        setStreamError('Camera access is required for this proctored assessment.');
      }
    });

    socket.on('joined', () => setIsStreaming(true));
    socket.on('interviewer_joined', startPeer);
    socket.on('webrtc_answer', ({ answer } = {}) => {
      if (answer && peerRef.current) peerRef.current.signal(answer);
    });
    socket.on('ice_candidate', ({ candidate } = {}) => {
      if (candidate && peerRef.current) peerRef.current.signal(candidate);
    });
    socket.on('connect_error', () => {
      setStreamError('Unable to connect to live proctoring.');
    });
    socket.on('error', ({ message } = {}) => {
      setStreamError(message || 'Live proctoring encountered an error.');
    });
    socket.on('disconnect', () => setIsStreaming(false));

    return () => {
      cancelled = true;
      destroyPeer();
      localStream?.getTracks().forEach((track) => track.stop());
      socket.disconnect();
      setMediaStream(null);
      setIsStreaming(false);
    };
  }, [assessmentId, accessToken, enabled]);

  return { mediaStream, isStreaming, streamError };
};
