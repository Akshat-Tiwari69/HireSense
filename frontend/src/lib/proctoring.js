/**
 * Pure proctoring decision logic, kept free of browser and MediaPipe APIs so
 * it can be unit tested. The hooks feed it observations; it decides when an
 * observation has lasted long enough to be worth a proctor's attention.
 */

export const FACE_SAMPLE_INTERVAL_MS = 1000;

// A condition must persist this long before it is reported, so a candidate
// glancing down or a detector miss on one frame does not create an event.
const FACE_CONDITION_THRESHOLD_MS = {
  no_face: 5000,
  multiple_faces: 3000,
};

// After an event is reported, the same type is not reported again until the
// candidate has been back in a normal state and this much time has passed.
const FACE_REPORT_COOLDOWN_MS = 30000;

const FACE_EVENTS = {
  no_face: {
    severity: 'high',
    description: 'No face was visible on camera for several seconds.',
  },
  multiple_faces: {
    severity: 'high',
    description: 'More than one face was visible on camera.',
  },
};

export const classifyFaceCount = (count) => {
  if (!Number.isFinite(count) || count <= 0) return 'no_face';
  if (count > 1) return 'multiple_faces';
  return 'ok';
};

/**
 * Tracks face-count samples and returns an event to report, or null. Each
 * episode (a continuous stretch of one abnormal condition) yields at most one
 * event. A new condition only takes over after `confirmSamples` consecutive
 * samples agree, so a single-frame detector miss or false positive neither
 * starts nor breaks an episode.
 */
export const createFaceMonitor = ({
  thresholds = FACE_CONDITION_THRESHOLD_MS,
  cooldownMs = FACE_REPORT_COOLDOWN_MS,
  confirmSamples = 2,
} = {}) => {
  let condition = 'ok';
  let since = 0;
  let reported = false;
  let candidate = null;
  let candidateSince = 0;
  let candidateHits = 0;
  const lastReportedAt = new Map();

  const reset = () => {
    condition = 'ok';
    since = 0;
    reported = false;
    candidate = null;
    candidateHits = 0;
  };

  const observe = (faceCount, now) => {
    const next = classifyFaceCount(faceCount);
    if (next === condition) {
      candidate = null;
      candidateHits = 0;
    } else {
      if (candidate === next) {
        candidateHits += 1;
      } else {
        candidate = next;
        candidateSince = now;
        candidateHits = 1;
      }
      if (candidateHits >= confirmSamples) {
        condition = next;
        since = candidateSince;
        reported = false;
        candidate = null;
        candidateHits = 0;
      }
    }
    if (condition === 'ok' || reported) return null;
    if (now - since < thresholds[condition]) return null;

    reported = true;
    const previous = lastReportedAt.get(condition);
    if (previous !== undefined && now - previous < cooldownMs) return null;
    lastReportedAt.set(condition, now);
    return {
      type: condition,
      faceCount: Math.max(0, Number(faceCount) || 0),
      ...FACE_EVENTS[condition],
    };
  };

  return { observe, reset, getCondition: () => condition };
};

/**
 * Returns a function that reports true at most once per `intervalMs` for each
 * key. Used to keep bursts of browser events from flooding the API.
 */
export const createKeyedThrottle = (intervalMs) => {
  const last = new Map();
  return (key, now) => {
    const previous = last.get(key);
    if (previous !== undefined && now - previous < intervalMs) return false;
    last.set(key, now);
    return true;
  };
};

const CLIPBOARD_SEVERITY = { paste: 'medium', cut: 'low', copy: 'low' };

/**
 * Builds the violation payload for a clipboard event. Only the action, where
 * it happened and the text length are recorded, never the clipboard content.
 */
export const describeClipboardEvent = (action, textLength, location) => {
  const where = location ? ` in the ${location}` : '';
  const size = Number.isFinite(textLength) && textLength > 0
    ? ` (${textLength} character${textLength === 1 ? '' : 's'})`
    : '';
  const verb = { paste: 'Pasted', cut: 'Cut', copy: 'Copied' }[action] || 'Clipboard used';
  return {
    type: 'copy_paste',
    severity: CLIPBOARD_SEVERITY[action] || 'low',
    description: `${verb} text${where}${size} during the assessment.`,
  };
};
