# HireSense Wiki

HireSense is a full-stack AI recruitment platform covering resume intake, AI analysis, candidate assessments, proctoring, and hiring decisions.

## Wiki Navigation
- [Getting Started](Getting-Started.md)
- [System Architecture](System-Architecture.md)
- [API Reference](API-Reference.md)
- [Database Schema](Database-Schema.md)
- [Roles and Permissions](Roles-and-Permissions.md)
- [Assessment and Proctoring](Assessment-and-Proctoring.md)
- [Deployment Guide](Deployment-Guide.md)
- [Security and Operations](Security-and-Operations.md)
- [Troubleshooting](Troubleshooting.md)
- [Contributing and Branching](Contributing-and-Branching.md)
- [Publish to GitHub Wiki](Publish-to-GitHub-Wiki.md)

## Tech Stack
- Frontend: React 18, Vite, Tailwind, shadcn/ui
- Backend: Flask, Flask-JWT-Extended, Flask-Limiter, Flask-CORS
- Database: PostgreSQL 15 (Supabase compatible)
- AI: OpenAI GPT-4o-mini (with deterministic fallbacks)
- Realtime: Socket.IO + WebRTC

## Core Capabilities
- Resume parsing and AI match scoring
- Job posting and candidate-job matching
- Multi-part assessments (MCQ, coding, psychometric)
- Live proctoring with violation tracking
- RBAC dashboards for admin/interviewer/proctor flows
