# Security and Operations

## Authentication and Authorization
- JWT-based auth for dashboard users
- Role-based access control across APIs
- Token-based assessment access for candidates

## HTTP Hardening
- Security headers include CSP, frame protection, and content-type protections
- CORS should be explicitly configured in production

## Data Safety
- Parameterized SQL usage
- Input validation and secure file handling
- Restricted upload directory and controlled access

## Operational Safeguards
- Request logging for traceability
- Audit logs for sensitive actions
- Email logs for delivery observability
- Rate limiting on critical endpoints

## Environment Practices
- Keep `ALLOW_RUNTIME_ENV_MUTATION=false` in production
- Never expose secrets in frontend `VITE_*` variables
- Rotate JWT secrets and API keys periodically

## Next Reads
- [Deployment Guide](Deployment-Guide.md)
- [Troubleshooting](Troubleshooting.md)
