# Proctoring System Guide

Complete documentation for the assessment proctoring and monitoring system.

---

## Overview

The proctoring system ensures assessment integrity by monitoring candidates during tests. It uses browser-based face detection and activity tracking to identify potential violations.

**Key Features:**
- Real-time face detection
- Tab switching detection
- Window blur detection
- Violation logging and alerts
- Proctor dashboard for monitoring

---

## Architecture

### Client-Side Proctoring

```
┌─────────────────────────────────────────────────────────┐
│                   Assessment Page                        │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │  Video Stream   │    │    Face Detection           │ │
│  │  (Camera)       │───→│    (face-api.js)            │ │
│  └─────────────────┘    └─────────────────────────────┘ │
│                                    │                     │
│                                    ▼                     │
│                         ┌──────────────────┐            │
│                         │ Violation Check  │            │
│                         │ - No face        │            │
│                         │ - Multiple faces │            │
│                         └────────┬─────────┘            │
│                                  │                      │
│  ┌─────────────────┐            │                      │
│  │ Event Listeners │            │                      │
│  │ - visibilitychange           │                      │
│  │ - blur/focus    │────────────┤                      │
│  └─────────────────┘            │                      │
│                                  ▼                      │
│                    POST /api/proctor/report-violation   │
└─────────────────────────────────────────────────────────┘
```

### Server-Side Storage

```
┌─────────────────────┐
│ proctoring_events   │
├─────────────────────┤
│ id                  │
│ assessment_id       │──→ assessments table
│ event_type          │
│ details             │
│ timestamp           │
└─────────────────────┘
```

---

## Violation Types

| Type | Description | Severity |
|------|-------------|----------|
| `no_face` | No face detected in camera | High |
| `multiple_faces` | More than one face detected | High |
| `tab_switch` | Browser tab changed | Medium |
| `window_blur` | Browser window lost focus | Medium |
| `camera_blocked` | Camera access denied/blocked | Critical |
| `screen_share_end` | Screen sharing stopped | Medium |

---

## Client Implementation

### Camera Setup

```javascript
// AssessmentPage.jsx
const [cameraReady, setCameraReady] = useState(false);
const [faceDetectionActive, setFaceDetectionActive] = useState(false);
const videoRef = useRef(null);

const setupCamera = async () => {
  try {
    // Request camera access
    const stream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: 'user'
      }
    });
    
    // Attach to video element
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
    }
    
    // Load face detection models
    await loadFaceDetectionModels();
    
    setCameraReady(true);
    startFaceDetection();
    
  } catch (error) {
    console.error('Camera setup failed:', error);
    reportViolation('camera_blocked', error.message);
  }
};
```

### Face Detection

```javascript
// Load face-api.js models
const loadFaceDetectionModels = async () => {
  const MODEL_URL = '/models';
  await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
};

// Continuous face detection
const startFaceDetection = () => {
  const detectionInterval = setInterval(async () => {
    if (!videoRef.current || !faceDetectionActive) return;
    
    try {
      const detections = await faceapi.detectAllFaces(
        videoRef.current,
        new faceapi.TinyFaceDetectorOptions({
          inputSize: 320,
          scoreThreshold: 0.5
        })
      );
      
      // Check for violations
      if (detections.length === 0) {
        reportViolation('no_face', 'No face detected in camera');
      } else if (detections.length > 1) {
        reportViolation('multiple_faces', `${detections.length} faces detected`);
      }
      
    } catch (error) {
      console.error('Face detection error:', error);
    }
  }, 2000); // Check every 2 seconds
  
  return () => clearInterval(detectionInterval);
};
```

### Tab/Window Monitoring

```javascript
// Tab visibility change
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.hidden) {
      reportViolation('tab_switch', 'User switched to another tab');
    }
  };
  
  document.addEventListener('visibilitychange', handleVisibilityChange);
  return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
}, []);

// Window blur (e.g., switching applications)
useEffect(() => {
  const handleBlur = () => {
    reportViolation('window_blur', 'Browser window lost focus');
  };
  
  window.addEventListener('blur', handleBlur);
  return () => window.removeEventListener('blur', handleBlur);
}, []);
```

### Violation Reporting

```javascript
const reportViolation = async (eventType, details) => {
  // Debounce to prevent spam
  const now = Date.now();
  if (now - lastViolationTime < 3000) return;
  setLastViolationTime(now);
  
  try {
    await api.post('/api/proctor/report-violation', {
      assessment_id: assessmentId,
      event_type: eventType,
      details: details
    });
    
    // Update local violation count
    setViolationCount(prev => prev + 1);
    
    // Show warning to candidate
    toast({
      title: 'Proctoring Alert',
      description: getViolationMessage(eventType),
      variant: 'destructive'
    });
    
  } catch (error) {
    console.error('Failed to report violation:', error);
  }
};

const getViolationMessage = (type) => {
  const messages = {
    'no_face': 'Please ensure your face is visible in the camera.',
    'multiple_faces': 'Multiple faces detected. Please ensure you are alone.',
    'tab_switch': 'Please stay on the assessment page.',
    'window_blur': 'Please keep the browser window in focus.'
  };
  return messages[type] || 'Proctoring violation detected.';
};
```

---

## Backend Implementation

### Proctor Routes (proctor_routes.py)

```python
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from db_helpers import (
    log_proctoring_event,
    get_proctoring_events,
    get_active_assessments,
    flag_assessment,
    get_assessment_violations
)

proctor_bp = Blueprint('proctor', __name__)

def proctor_required():
    """Decorator for proctor-only endpoints"""
    def wrapper(fn):
        @jwt_required()
        def decorated(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role') not in ['proctor', 'admin']:
                return jsonify({
                    'status': 'error',
                    'message': 'Proctor access required'
                }), 403
            return fn(*args, **kwargs)
        decorated.__name__ = fn.__name__
        return decorated
    return wrapper

@proctor_bp.route('/report-violation', methods=['POST'])
def report_violation():
    """Report a proctoring violation (called by assessment page)"""
    data = request.json
    
    assessment_id = data.get('assessment_id')
    event_type = data.get('event_type')
    details = data.get('details', '')
    
    if not assessment_id or not event_type:
        return jsonify({
            'status': 'error',
            'message': 'assessment_id and event_type required'
        }), 400
    
    # Log the violation
    event_id = log_proctoring_event(
        assessment_id=assessment_id,
        event_type=event_type,
        details=details
    )
    
    return jsonify({
        'status': 'success',
        'data': {'event_id': event_id}
    })

@proctor_bp.route('/active-assessments', methods=['GET'])
@proctor_required()
def get_active():
    """Get all currently active assessments"""
    assessments = get_active_assessments()
    
    # Add violation counts
    for assessment in assessments:
        violations = get_assessment_violations(assessment['id'])
        assessment['violation_count'] = len(violations)
        assessment['recent_violations'] = violations[:5]
    
    return jsonify({
        'status': 'success',
        'data': assessments
    })

@proctor_bp.route('/violations/<int:assessment_id>', methods=['GET'])
@proctor_required()
def get_violations(assessment_id):
    """Get all violations for an assessment"""
    violations = get_proctoring_events(assessment_id)
    
    return jsonify({
        'status': 'success',
        'data': violations
    })

@proctor_bp.route('/flag/<int:assessment_id>', methods=['POST'])
@proctor_required()
def flag_for_review(assessment_id):
    """Flag an assessment for manual review"""
    data = request.json
    reason = data.get('reason', 'Flagged by proctor')
    
    flag_assessment(assessment_id, reason)
    
    return jsonify({
        'status': 'success',
        'message': 'Assessment flagged for review'
    })
```

### Database Helpers

```python
# db_helpers.py

def log_proctoring_event(assessment_id, event_type, details=''):
    """Log a proctoring event"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO proctoring_events (assessment_id, event_type, details)
        VALUES (?, ?, ?)
    ''', (assessment_id, event_type, details))
    
    event_id = cursor.lastrowid
    
    # Update violation count in assessments table
    cursor.execute('''
        UPDATE assessments 
        SET proctoring_violations = proctoring_violations + 1
        WHERE id = ?
    ''', (assessment_id,))
    
    conn.commit()
    conn.close()
    
    return event_id

def get_proctoring_events(assessment_id):
    """Get all proctoring events for an assessment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, event_type, details, timestamp
        FROM proctoring_events
        WHERE assessment_id = ?
        ORDER BY timestamp DESC
    ''', (assessment_id,))
    
    events = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return events

def get_active_assessments():
    """Get all currently in-progress assessments"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            a.id,
            a.candidate_id,
            c.name as candidate_name,
            c.email as candidate_email,
            a.created_at as started_at,
            a.status,
            a.proctoring_violations
        FROM assessments a
        JOIN candidates c ON a.candidate_id = c.id
        WHERE a.status = 'in_progress'
        ORDER BY a.created_at DESC
    ''')
    
    assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return assessments
```

---

## Proctor Dashboard

### ProctorDashboardPage.jsx

```jsx
import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Eye, Flag, RefreshCw, AlertTriangle } from 'lucide-react';

export default function ProctorDashboardPage() {
  const [activeAssessments, setActiveAssessments] = useState([]);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [violations, setViolations] = useState([]);
  const [showViolationsDialog, setShowViolationsDialog] = useState(false);
  const [loading, setLoading] = useState(true);

  // Fetch active assessments
  const fetchActiveAssessments = async () => {
    try {
      const response = await api.get('/api/proctor/active-assessments');
      setActiveAssessments(response.data.data);
    } catch (error) {
      console.error('Failed to fetch assessments:', error);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 30 seconds
  useEffect(() => {
    fetchActiveAssessments();
    const interval = setInterval(fetchActiveAssessments, 30000);
    return () => clearInterval(interval);
  }, []);

  // View violations for an assessment
  const viewViolations = async (assessmentId) => {
    const response = await api.get(`/api/proctor/violations/${assessmentId}`);
    setViolations(response.data.data);
    setSelectedAssessment(assessmentId);
    setShowViolationsDialog(true);
  };

  // Flag assessment for review
  const flagAssessment = async (assessmentId) => {
    await api.post(`/api/proctor/flag/${assessmentId}`, {
      reason: 'Excessive violations detected'
    });
    fetchActiveAssessments();
  };

  const getViolationBadge = (count) => {
    if (count === 0) return <Badge variant="default">Clean</Badge>;
    if (count <= 3) return <Badge variant="secondary">{count} violations</Badge>;
    if (count <= 5) return <Badge variant="warning">{count} violations</Badge>;
    return <Badge variant="destructive">{count} violations</Badge>;
  };

  return (
    <div className="container mx-auto p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Proctor Dashboard</h1>
        <Button onClick={fetchActiveAssessments} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <Card>
          <CardHeader>
            <h3>Active Assessments</h3>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{activeAssessments.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <h3>Total Violations</h3>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {activeAssessments.reduce((sum, a) => sum + a.violation_count, 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <h3>High Risk</h3>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-red-500">
              {activeAssessments.filter(a => a.violation_count > 5).length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Active Assessments Table */}
      <Card>
        <CardHeader>
          <h2 className="text-lg font-semibold">Active Assessments</h2>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Candidate</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Started</TableHead>
                <TableHead>Violations</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {activeAssessments.map(assessment => (
                <TableRow 
                  key={assessment.id}
                  className={assessment.violation_count > 5 ? 'bg-red-50' : ''}
                >
                  <TableCell className="font-medium">
                    {assessment.candidate_name}
                  </TableCell>
                  <TableCell>{assessment.candidate_email}</TableCell>
                  <TableCell>
                    {new Date(assessment.started_at).toLocaleTimeString()}
                  </TableCell>
                  <TableCell>
                    {getViolationBadge(assessment.violation_count)}
                  </TableCell>
                  <TableCell className="space-x-2">
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => viewViolations(assessment.id)}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      onClick={() => flagAssessment(assessment.id)}
                    >
                      <Flag className="h-4 w-4 mr-1" />
                      Flag
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {activeAssessments.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                    No active assessments
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Violations Dialog */}
      <Dialog open={showViolationsDialog} onOpenChange={setShowViolationsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Violation History</DialogTitle>
          </DialogHeader>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Details</TableHead>
                <TableHead>Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {violations.map(violation => (
                <TableRow key={violation.id}>
                  <TableCell>
                    <Badge variant={
                      violation.event_type.includes('face') ? 'destructive' : 'secondary'
                    }>
                      {violation.event_type}
                    </Badge>
                  </TableCell>
                  <TableCell>{violation.details}</TableCell>
                  <TableCell>
                    {new Date(violation.timestamp).toLocaleTimeString()}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </DialogContent>
      </Dialog>
    </div>
  );
}
```

---

## API Reference

### Report Violation

```
POST /api/proctor/report-violation
Content-Type: application/json

{
  "assessment_id": 42,
  "event_type": "no_face",
  "details": "No face detected in camera"
}
```

### Get Active Assessments

```
GET /api/proctor/active-assessments
Authorization: Bearer <proctor_token>
```

### Get Violations

```
GET /api/proctor/violations/:assessment_id
Authorization: Bearer <proctor_token>
```

### Flag Assessment

```
POST /api/proctor/flag/:assessment_id
Authorization: Bearer <proctor_token>
Content-Type: application/json

{
  "reason": "Excessive violations detected"
}
```

---

## Configuration

### Face Detection Models

Place face-api.js models in `public/models/`:
- `tiny_face_detector_model-weights_manifest.json`
- `tiny_face_detector_model-shard1`

### Detection Sensitivity

```javascript
// Adjust in AssessmentPage.jsx
const detectorOptions = new faceapi.TinyFaceDetectorOptions({
  inputSize: 320,      // Image size (128, 160, 224, 320, 416, 512, 608)
  scoreThreshold: 0.5  // Minimum confidence (0.0 - 1.0)
});
```

### Violation Debounce

```javascript
// Prevent rapid-fire violations
const VIOLATION_COOLDOWN = 3000; // 3 seconds between reports
```

---

## Best Practices

### For Candidates

1. **Before starting:**
   - Ensure good lighting
   - Position camera at face level
   - Close unnecessary browser tabs
   - Disable browser notifications

2. **During assessment:**
   - Keep face visible at all times
   - Stay in the assessment tab
   - Don't switch applications
   - Complete in one session

### For Proctors

1. **Monitor actively:**
   - Check dashboard regularly
   - Review high-violation assessments
   - Flag suspicious patterns

2. **Investigate violations:**
   - Review violation timeline
   - Consider context (network issues, etc.)
   - Document findings

---

## Troubleshooting

### Camera not working

1. Check browser permissions
2. Ensure no other app is using camera
3. Try different browser
4. Restart browser

### Face detection issues

1. Improve lighting
2. Remove glasses/accessories
3. Position camera at face level
4. Check camera resolution

### High false positives

1. Adjust `scoreThreshold` (lower = more sensitive)
2. Increase detection interval
3. Check lighting conditions

---

## Security Considerations

### Client-Side Limitations

Browser-based proctoring has inherent limitations:
- Cannot detect virtual machines
- Cannot prevent screen sharing to other devices
- Cannot see beyond camera view

### Recommendations for High-Stakes Assessments

1. Use dedicated proctoring software
2. Require ID verification
3. Record video for review
4. Use randomized question pools

---

## Related Documentation

- [ASSESSMENT_SYSTEM_GUIDE.md](ASSESSMENT_SYSTEM_GUIDE.md) - Assessment flow
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Proctoring events table
- [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) - Assessment page implementation

---

*Last Updated: January 2026*
*Version: 1.0*
