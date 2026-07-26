import { useCallback, useEffect, useRef, useState } from 'react';
import { io } from 'socket.io-client';
import SimplePeer from 'simple-peer';
import { AlertCircle, Loader2, Video, Wifi, WifiOff } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { API_BASE_URL } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const ProctorMonitor = ({ assessmentId, onClose }) => {
  const { token, user } = useAuth();
  const [connected, setConnected] = useState(false);
  const [candidatePresent, setCandidatePresent] = useState(false);
  const [error, setError] = useState(null);
  const [hasActiveStream, setHasActiveStream] = useState(false);

  const socketRef = useRef(null);
  const peerRef = useRef(null);
  const videoRef = useRef(null);
  const handleOfferRef = useRef(null);

  const destroyPeer = useCallback(() => {
    if (peerRef.current) {
      peerRef.current.destroy();
      peerRef.current = null;
    }
    if (videoRef.current) videoRef.current.srcObject = null;
    setHasActiveStream(false);
  }, []);

  const handleOffer = useCallback((offer) => {
    destroyPeer();

    const peer = new SimplePeer({
      initiator: false,
      trickle: true,
      config: {
        iceServers: [
          { urls: 'stun:stun.l.google.com:19302' },
          { urls: 'stun:stun1.l.google.com:19302' },
        ],
      },
    });

    peerRef.current = peer;

    peer.on('signal', (data) => {
      if (data.type === 'answer') {
        socketRef.current?.emit('webrtc_answer', {
          assessment_id: assessmentId,
          answer: data,
        });
        return;
      }

      socketRef.current?.emit('ice_candidate', {
        assessment_id: assessmentId,
        candidate: data,
        target: 'candidate',
      });
    });

    peer.on('stream', (stream) => {
      if (!videoRef.current) return;
      videoRef.current.srcObject = stream;
      setHasActiveStream(true);
      setError(null);
    });

    peer.on('error', () => {
      setError('The secure video connection could not be established. Ask the candidate to reconnect their camera.');
      setHasActiveStream(false);
    });

    peer.signal(offer);
  }, [assessmentId, destroyPeer]);

  handleOfferRef.current = handleOffer;

  useEffect(() => {
    const socket = io(API_BASE_URL, {
      transports: ['websocket', 'polling'],
      auth: {
        role: 'staff',
        assessment_id: assessmentId,
        token,
      },
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      setConnected(true);
      setError(null);
      socket.emit('join_as_interviewer', {
        assessment_id: assessmentId,
        user_id: user?.id,
        token,
      });
    });

    socket.on('joined', (data) => {
      setCandidatePresent(Boolean(data?.candidate_present));
    });

    socket.on('candidate_joined', () => {
      setCandidatePresent(true);
      setError(null);
    });

    socket.on('webrtc_offer', (data) => {
      if (data?.offer) handleOfferRef.current?.(data.offer);
    });

    socket.on('ice_candidate', (data) => {
      if (peerRef.current && data?.candidate) peerRef.current.signal(data.candidate);
    });

    socket.on('candidate_disconnected', () => {
      setCandidatePresent(false);
      destroyPeer();
    });

    socket.on('error', (data) => {
      setError(data?.message || 'The monitoring service reported a connection error.');
    });

    socket.on('connect_error', () => {
      setConnected(false);
      setError('Unable to reach the live monitoring service. Retrying automatically.');
    });

    socket.on('disconnect', () => {
      setConnected(false);
    });

    return () => {
      destroyPeer();
      socket.disconnect();
      socketRef.current = null;
    };
  }, [assessmentId, destroyPeer, token, user?.id]);

  const streamLabel = hasActiveStream
    ? 'Camera stream active'
    : candidatePresent
      ? 'Candidate connected; preparing stream'
      : 'Waiting for candidate';

  return (
    <Dialog open onOpenChange={(open) => { if (!open) onClose(); }}>
      <DialogContent className="flex max-h-[calc(100vh-1.5rem)] max-w-6xl flex-col gap-0 overflow-hidden border-slate-700 bg-slate-950 p-0 text-slate-200 shadow-xl sm:max-h-[calc(100vh-3rem)] sm:p-0 [&>button]:right-5 [&>button]:top-5 [&>button]:text-slate-300 [&>button]:opacity-100 [&>button]:focus:ring-blue-400 [&>button]:focus:ring-offset-slate-900 [&>button]:hover:bg-slate-800">
        <DialogHeader className="border-b border-slate-800 bg-slate-900 px-4 py-4 pr-14 text-left sm:px-6 sm:pr-16">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-blue-300">Authorized live view</p>
            <DialogTitle className="mt-1 text-lg text-white sm:text-xl">Candidate monitor</DialogTitle>
            <DialogDescription className="mt-1 text-slate-400">
              Assessment #{assessmentId} · Use integrity events as review signals, not automatic conclusions.
            </DialogDescription>
          </div>
        </DialogHeader>

        <div className="flex min-h-0 flex-1 flex-col overflow-y-auto p-4 sm:p-6">
          <div className="mb-4 flex flex-wrap gap-2" aria-live="polite">
            <div className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium ${
              connected
                ? 'border-emerald-800 bg-emerald-950/60 text-emerald-300'
                : 'border-red-800 bg-red-950/60 text-red-300'
            }`}>
              {connected ? <Wifi className="h-3.5 w-3.5" aria-hidden="true" /> : <WifiOff className="h-3.5 w-3.5" aria-hidden="true" />}
              {connected ? 'Service connected' : 'Service reconnecting'}
            </div>
            <div className={`inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-medium ${
              hasActiveStream
                ? 'border-blue-800 bg-blue-950/60 text-blue-300'
                : 'border-slate-700 bg-slate-900 text-slate-300'
            }`}>
              {candidatePresent && !hasActiveStream
                ? <Loader2 className="h-3.5 w-3.5 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                : <Video className="h-3.5 w-3.5" aria-hidden="true" />}
              {streamLabel}
            </div>
          </div>

          <div className="relative flex min-h-[18rem] flex-1 items-center justify-center overflow-hidden rounded-lg border border-slate-800 bg-black sm:min-h-[30rem]">
            {error && !hasActiveStream ? (
              <div className="mx-6 max-w-lg rounded-lg border border-red-900 bg-red-950/70 p-5 text-center" role="alert">
                <AlertCircle className="mx-auto h-6 w-6 text-red-300" aria-hidden="true" />
                <p className="mt-3 text-sm font-medium text-red-100">Video unavailable</p>
                <p className="mt-1 text-sm leading-6 text-red-300">{error}</p>
              </div>
            ) : null}

            {!candidatePresent && !error ? (
              <div className="px-6 text-center" aria-live="polite">
                <Loader2 className="mx-auto h-7 w-7 animate-spin text-blue-300 motion-reduce:animate-none" aria-hidden="true" />
                <p className="mt-4 text-sm font-medium text-slate-200">Waiting for the candidate</p>
                <p className="mt-1 text-sm text-slate-500">The camera feed will appear when the assessment session connects.</p>
              </div>
            ) : null}

            <video
              ref={videoRef}
              autoPlay
              playsInline
              className={`h-full w-full bg-black object-contain ${hasActiveStream ? 'block' : 'hidden'}`}
              aria-label="Live candidate camera feed"
            />
          </div>

          <div className="mt-4 flex items-start gap-3 rounded-lg border border-slate-800 bg-slate-900/70 px-4 py-3 text-sm text-slate-400">
            <Video className="mt-0.5 h-4 w-4 shrink-0 text-slate-300" aria-hidden="true" />
            <p>Only authorized staff can view this encrypted session feed. Review any detected event in context before recording a decision.</p>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ProctorMonitor;
