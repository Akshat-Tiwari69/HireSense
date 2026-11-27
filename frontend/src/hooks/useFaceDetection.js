import { useEffect, useRef, useState } from 'react';

import { createFaceMonitor, FACE_SAMPLE_INTERVAL_MS } from '../lib/proctoring';

// Both files are self-hosted so the strict production CSP needs no CDN.
// The wasm runtime is copied from node_modules at build time (vite.config.js).
const WASM_BASE_PATH = '/mediapipe';
const MODEL_PATH = '/models/blaze_face_short_range.tflite';

const loadDetector = async () => {
  const { FaceDetector, FilesetResolver } = await import('@mediapipe/tasks-vision');
  const fileset = await FilesetResolver.forVisionTasks(WASM_BASE_PATH);
  return FaceDetector.createFromOptions(fileset, {
    baseOptions: { modelAssetPath: MODEL_PATH, delegate: 'CPU' },
    runningMode: 'VIDEO',
    minDetectionConfidence: 0.5,
  });
};

/**
 * Samples the candidate's camera preview once a second with an in-browser
 * face detector and calls `onEvent` when no face, or more than one face, has
 * been visible for long enough to matter. Frames never leave the browser for
 * detection; only the resulting event (and its optional screenshot) is sent.
 *
 * Returns the detector status: 'idle' | 'loading' | 'running' | 'unavailable'.
 */
export const useFaceDetection = (videoRef, enabled, onEvent) => {
  const [status, setStatus] = useState('idle');
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    if (!enabled) {
      setStatus('idle');
      return undefined;
    }

    let cancelled = false;
    let detector = null;
    let timer = null;
    let lastVideoTime = -1;
    const monitor = createFaceMonitor();

    const sample = () => {
      const video = videoRef.current;
      // The tab_hidden event already covers a hidden page, and a paused or
      // not-yet-ready video would read as "no face" without the candidate
      // having done anything.
      if (
        !detector
        || document.visibilityState === 'hidden'
        || !video
        || video.readyState < 2
        || !video.videoWidth
      ) {
        monitor.reset();
        return;
      }
      if (video.currentTime === lastVideoTime) return;
      lastVideoTime = video.currentTime;

      let faceCount;
      try {
        faceCount = detector.detectForVideo(video, performance.now()).detections.length;
      } catch {
        monitor.reset();
        return;
      }
      const event = monitor.observe(faceCount, Date.now());
      if (event) onEventRef.current?.(event);
    };

    setStatus('loading');
    loadDetector()
      .then((created) => {
        if (cancelled) {
          created.close();
          return;
        }
        detector = created;
        setStatus('running');
        timer = window.setInterval(sample, FACE_SAMPLE_INTERVAL_MS);
      })
      .catch(() => {
        if (cancelled) return;
        setStatus('unavailable');
        onEventRef.current?.({
          type: 'face_detection_unavailable',
          severity: 'low',
          description: 'Face detection could not start in this browser; camera video is still streamed to the proctor.',
        });
      });

    return () => {
      cancelled = true;
      if (timer) window.clearInterval(timer);
      detector?.close();
    };
  }, [enabled, videoRef]);

  return status;
};
