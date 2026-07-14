# API Reference

Base URL (dev): `http://localhost:5000`

## Authentication
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/auth/verify`

Protected endpoints use an Authorization header with a JWT bearer token.

## Admin APIs (`/api/admin`)
- Users CRUD
- Candidate management
- Analytics, email logs, DB inspection
- Bulk resume upload
- Question bank management

## Interviewer APIs (`/api/interviewer`)
- Candidate list/detail/resume access
- Schedule assessment
- Reject candidate
- Add notes
- View assessment results
- Submit final decision

## Interviewee APIs (`/api/interviewee`)
- Verify assessment token
- Start assessment
- Submit answers (mcq/coding/psychometric)
- Complete assessment
- Violation/time sync endpoints

## Proctor APIs (`/api/proctor`)
- Scheduled/active/completed assessments
- Violation records
- Proctor dashboard stats

## Jobs APIs (`/api/jobs`)
- Sectors CRUD (privileged)
- Job posting CRUD
- Candidate-job matching
- Audit log

## Realtime Events
- Candidate/proctor room join
- WebRTC offer/answer/candidate forwarding
- Active assessment room presence updates

## Source of Truth
For full endpoint contracts and payloads, see `/docs/API.md`.
