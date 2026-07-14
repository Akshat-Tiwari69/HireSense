# Assessment and Proctoring

## Assessment Lifecycle
1. Interviewer schedules assessment
2. Candidate receives secure assessment link
3. Candidate starts within allowed time window
4. Candidate submits MCQ/coding/psychometric answers
5. System computes technical, psychometric, and overall scores
6. Interviewer reviews outputs and submits final decision

## Assessment Composition
- MCQ section
- Coding section (technical roles)
- Psychometric section

## Proctoring Coverage
- Live session monitoring (WebRTC)
- Candidate room presence and signaling via Socket.IO
- Violation reporting: no-face, multi-face, tab-switch, other suspicious behavior
- Violation evidence may include screenshots

## Integrity Controls
- Token-based candidate access
- Assessment window validation
- Time synchronization endpoints
- Role-based proctor/interviewer/admin access controls

## Next Reads
- [API Reference](API-Reference.md)
- [Security and Operations](Security-and-Operations.md)
