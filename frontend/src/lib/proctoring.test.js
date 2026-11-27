import { describe, expect, it } from 'vitest';

import {
  classifyFaceCount,
  createFaceMonitor,
  createKeyedThrottle,
  describeClipboardEvent,
} from './proctoring';

const thresholds = { no_face: 5000, multiple_faces: 3000 };

const feed = (monitor, samples) => samples
  .map(([count, at]) => monitor.observe(count, at))
  .filter(Boolean);

describe('classifyFaceCount', () => {
  it('classifies face counts', () => {
    expect(classifyFaceCount(0)).toBe('no_face');
    expect(classifyFaceCount(Number.NaN)).toBe('no_face');
    expect(classifyFaceCount(1)).toBe('ok');
    expect(classifyFaceCount(2)).toBe('multiple_faces');
  });
});

describe('createFaceMonitor', () => {
  it('ignores a short absence', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    expect(feed(monitor, [[1, 0], [0, 1000], [0, 4000], [1, 5000]])).toEqual([]);
  });

  it('reports a sustained absence once per episode', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    const events = feed(monitor, [[0, 0], [0, 4999], [0, 5000], [0, 6000], [0, 60000]]);
    expect(events).toHaveLength(1);
    expect(events[0]).toMatchObject({ type: 'no_face', severity: 'high', faceCount: 0 });
  });

  it('reports multiple faces after its shorter threshold', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    const events = feed(monitor, [[1, 0], [2, 1000], [3, 4000]]);
    expect(events).toEqual([expect.objectContaining({ type: 'multiple_faces', faceCount: 3 })]);
  });

  it('is not fooled by single-frame detector flicker', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    // A missing face with an occasional false positive is still one absence.
    const absent = feed(monitor, [[0, 0], [0, 1000], [1, 2000], [0, 3000], [1, 4000], [0, 5000]]);
    expect(absent.map((event) => event.type)).toEqual(['no_face']);
    // A present face with an occasional miss never starts an absence.
    const present = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    expect(feed(present, [[1, 0], [0, 1000], [1, 2000], [0, 3000], [1, 4000], [0, 9000], [1, 10000]])).toEqual([]);
  });

  it('suppresses a repeat of the same type inside the cooldown', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 30000 });
    const events = feed(monitor, [
      [0, 0], [0, 5000], // reported at 5s
      [1, 6000], [1, 7000],
      [0, 8000], [0, 9000], [0, 14000], // second episode inside cooldown
      [1, 15000], [1, 16000],
      [0, 40000], [0, 41000], [0, 46000], // after cooldown
    ]);
    expect(events.map((event) => event.type)).toEqual(['no_face', 'no_face']);
  });

  it('starts a fresh episode after reset', () => {
    const monitor = createFaceMonitor({ thresholds, cooldownMs: 0 });
    monitor.observe(0, 0);
    monitor.observe(0, 1000);
    expect(monitor.getCondition()).toBe('no_face');
    monitor.reset();
    expect(monitor.getCondition()).toBe('ok');
    expect(monitor.observe(0, 6000)).toBeNull();
    expect(monitor.observe(0, 7000)).toBeNull();
    expect(monitor.observe(0, 12000)).toMatchObject({ type: 'no_face' });
  });
});

describe('createKeyedThrottle', () => {
  it('allows each key once per interval', () => {
    const allow = createKeyedThrottle(10000);
    expect(allow('paste', 0)).toBe(true);
    expect(allow('paste', 5000)).toBe(false);
    expect(allow('copy', 5000)).toBe(true);
    expect(allow('paste', 10000)).toBe(true);
  });
});

describe('describeClipboardEvent', () => {
  it('records the action and length but never the content', () => {
    expect(describeClipboardEvent('paste', 42, 'code editor')).toEqual({
      type: 'copy_paste',
      severity: 'medium',
      description: 'Pasted text in the code editor (42 characters) during the assessment.',
    });
    expect(describeClipboardEvent('copy', 0, 'assessment page')).toMatchObject({
      severity: 'low',
      description: 'Copied text in the assessment page during the assessment.',
    });
  });
});
