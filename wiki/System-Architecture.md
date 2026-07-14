# System Architecture

HireSense separates frontend UI, backend services, database, and external providers.

## High-Level Components
- React SPA for all user dashboards and candidate flows
- Flask REST API for business logic and orchestration
- Socket.IO signaling server for WebRTC proctoring
- PostgreSQL for canonical data storage
- OpenAI + email providers as external integrations

## Backend Modules
- `app.py`: app bootstrap, blueprints, middleware
- `auth.py`: authentication and JWT lifecycle
- `admin_routes.py`: admin functions, analytics, management APIs
- `interviewer_routes.py`: candidate review, schedule, decisions
- `interviewee_*`: candidate assessment lifecycle and submissions
- `proctor_routes.py`: monitoring and violations
- `job_routes.py`: sectors, postings, matching, audit logs
- `*_db.py` modules: domain-specific database access

## Frontend Structure
- `src/pages`: route-level pages
- `src/components`: UI and feature components
- `src/services/api.js`: API client
- `src/hooks`: reusable state/data hooks
- `src/context`: provider-level state

## Key Flows
1. Candidate uploads resume
2. System parses and scores candidate-job fit
3. Interviewer schedules assessment
4. Candidate completes timed assessment
5. Proctor monitors live session
6. Interviewer records final decision

## Next Reads
- [Database Schema](Database-Schema.md)
- [Assessment and Proctoring](Assessment-and-Proctoring.md)
