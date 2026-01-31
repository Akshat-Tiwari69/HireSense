# Proctoring System Documentation

## Overview
The HireSense platform includes a comprehensive AI-powered proctoring system to monitor candidates during assessments and detect potential integrity violations.

## Features

### 1. Camera Monitoring
- **Continuous video feed** from candidate's webcam
- **Face detection** to ensure candidate remains visible
- Automatic violation reporting if face is not detected
- Visual feedback when face detection fails

### 2. Tab Switching Detection
- Monitors browser tab visibility
- Reports violations when candidate switches to another tab
- High severity violation (indicates possible cheating)

### 3. Violation Tracking
- All violations are logged with:
  - Timestamp
  - Violation type
  - Description
  - Severity level (low/medium/high)
- Real-time violation counter displayed to candidate
- Violation history stored in database

### 4. Multiple Cameras Warning
- Detects if multiple video input devices are present
- Warns candidate about potential privacy concerns

## Violation Types

| Type | Description | Severity | Action |
|------|-------------|----------|--------|
| `camera_denied` | Candidate denied camera access | High | Assessment cannot proceed |
| `no_face` | No face detected in camera feed | Medium | Warning issued |
| `tab_switch` | Candidate switched browser tab | High | Violation recorded |
| `multiple_people` | Multiple faces detected | High | Violation recorded |
| `suspicious_activity` | Other suspicious behavior | Medium | Violation recorded |

## Database Schema

```sql
CREATE TABLE proctoring_events (
    id INTEGER PRIMARY KEY,
    assessment_id INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (assessment_id) REFERENCES assessments(id)
);
```

## API Endpoints

### Report Violation
```
POST /api/interviewee/assessment/{assessment_id}/violation
```

**Request Body:**
```json
{
  "violation_type": "tab_switch",
  "description": "Candidate switched away from assessment tab",
  "severity": "high"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "violation_id": 123,
    "total_violations": 3
  }
}
```

### Get Assessment Violations
```
GET /api/proctor/assessment/{assessment_id}/violations
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "violations": [
      {
        "id": 1,
        "event_type": "tab_switch",
        "severity": "high",
        "details": "Switched away from assessment",
        "timestamp": "2026-01-30T10:30:00Z"
      }
    ],
    "total_count": 5
  }
}
```

## Frontend Implementation

### Camera Component
Located in assessment page, displays live feed with status indicators:
```jsx
<video ref={videoRef} autoPlay playsInline muted />
<Badge>Face {faceDetected ? 'Detected' : 'Not Detected'}</Badge>
```

### Violation Monitoring
```javascript
// Tab switch detection
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    reportViolation('tab_switch', 'Tab switched', 'high');
  }
});

// Face detection
setInterval(() => {
  if (!detectFace()) {
    reportViolation('no_face', 'No face detected', 'medium');
  }
}, 5000);
```

## Configuration

### Enable/Disable Proctoring
Proctoring can be enabled per assessment when scheduling:
```javascript
// In scheduling API
{
  "proctoring_enabled": true,  // Set to false to disable
  "scheduled_time": "2026-01-30T14:00:00Z"
}
```

### Severity Thresholds
Configure in backend settings:
- **Auto-fail threshold**: 5+ high severity violations
- **Manual review threshold**: 3+ high severity violations
- **Warning threshold**: 2+ medium severity violations

## Candidate Experience

1. **Permission Request**: Browser prompts for camera access
2. **Camera Preview**: Candidate sees their own video feed
3. **Face Detection Indicator**: Visual feedback on detection status
4. **Violation Warnings**: Toast notifications for violations
5. **Violation Counter**: Shows total violations during assessment

## Proctor Dashboard

Proctors can:
- View all assessments with violation counts
- See detailed violation timeline
- Filter assessments by violation severity
- Review specific violation events

## Best Practices

### For Candidates
- Use a well-lit room
- Position camera to show full face
- Stay in frame throughout assessment
- Don't switch tabs or windows
- Close unnecessary applications

### For Administrators
- Test proctoring setup before live assessments
- Review violation logs regularly
- Set clear policies on violation thresholds
- Provide candidates with proctoring guidelines
- Consider privacy regulations (GDPR, etc.)

## Privacy & Compliance

- **Video recording**: Not stored, only analyzed in real-time
- **Face detection**: Uses browser-based algorithms (no server upload)
- **Data retention**: Violation logs kept for 90 days
- **GDPR compliance**: Candidates must consent to monitoring
- **Transparency**: Clear notification that proctoring is active

## Troubleshooting

### Camera Not Working
1. Check browser permissions
2. Ensure no other app is using camera
3. Try different browser (Chrome recommended)
4. Disable browser extensions that block camera

### Face Not Detected
1. Improve lighting in room
2. Position face in center of frame
3. Remove hat/sunglasses if wearing
4. Check camera quality/angle

### False Positives
1. Adjust face detection sensitivity
2. Review violation logs manually
3. Consider environmental factors
4. Allow manual override for reviewers

## Future Enhancements

- [ ] Screen recording
- [ ] Eye tracking
- [ ] Audio analysis
- [ ] Behavioral analytics
- [ ] AI-powered anomaly detection
- [ ] Multiple camera angles
- [ ] ID verification
- [ ] Mobile device detection

## API Rate Limits

- Violation reports: 100 per assessment
- Violation queries: 60 per minute per proctor

## Support

For issues or questions:
- Check logs: `/api/proctor/assessment/{id}/violations`
- Review violation count: Assessment object `proctoring_violations` field
- Contact support if violations seem incorrect
