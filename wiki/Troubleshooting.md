# Troubleshooting

## Common Issues

### Backend cannot connect to DB
- Verify `DATABASE_URL`
- Ensure PostgreSQL is reachable and credentials are valid
- Confirm network/IP allowlisting for managed DB

### CORS failures
- Set exact frontend origin(s) in `CORS_ORIGINS`
- Ensure no trailing-slash mismatches

### JWT validation errors
- Verify token format and expiry
- Confirm server uses correct `JWT_SECRET_KEY`

### AI features not working
- Check `OPENAI_API_KEY`
- Confirm provider quota/credits

### Email delivery failures
- Configure `RESEND_API_KEY` or SMTP values
- Inspect email log records for error details

### Proctoring connection issues
- Confirm Socket.IO endpoint availability
- Check browser permissions for camera/microphone

## Source Docs
- `/docs/SETUP.md`
- `/docs/DEPLOYMENT_GUIDE.md`
- `/docs/PROCTOR_USER_SETUP.md`
