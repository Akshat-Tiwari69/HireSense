# Roles and Permissions

## Role Model
- `super_admin` (highest)
- `admin`
- `sector_admin`
- `recruiter`
- `interviewer`
- `proctor`
- Candidate (token-based assessment access)

## Admin
- Manage users, candidates, jobs, sectors
- View analytics and email/audit logs
- Manage question bank and bulk uploads
- Access DB and environment status tooling

## Interviewer
- Review candidates and AI insights
- Schedule assessments
- Reject candidates
- Review assessment outputs
- Record final hire/no-hire decisions

## Proctor
- Monitor live assessments
- Review and log violations
- Track active/completed sessions

## Candidate
- Apply for jobs
- Access assessment via secure token window
- Complete MCQ/coding/psychometric sections

## Notes
- Higher roles inherit lower-role capabilities where enforced.
- Sector scoping applies to relevant endpoints for scoped roles.

## Source of Truth
See `/docs/ROLES.md` for complete matrix and operational details.
