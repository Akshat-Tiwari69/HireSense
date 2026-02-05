# Deployment Guide

This guide covers deploying Cygnusa Elite Hire, an AI-powered recruitment and proctoring platform.

## Overview

Cygnusa Elite Hire supports three deployment environments:

- **Development**: Local setup for feature development and testing
- **Staging**: Pre-production environment for QA and integration testing
- **Production**: Live environment serving end users

## Prerequisites

Before deploying, ensure you have:

- Node.js v16+ and Python v3.9+
- Supabase account with a project created
- API keys for AI services (OpenAI or Google Gemini)
- Email service credentials (Resend API)
- Deployment platform accounts (Railway for backend, Vercel for frontend)

## Environment Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
DATABASE_URL=postgresql://user:password@host:port/database

# Authentication
JWT_SECRET_KEY=your-secure-random-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Services
OPENAI_API_KEY=your-openai-key
# OR
GOOGLE_GEMINI_API_KEY=your-gemini-key

# Email
RESEND_API_KEY=your-resend-key
FROM_EMAIL=noreply@yourdomain.com

# CORS
FRONTEND_URL=https://yourdomain.com

# WebSocket
WEBSOCKET_PORT=5001
```

### Frontend Environment Variables

Create a `.env` file in the `frontend/` directory:

```env
VITE_API_URL=https://your-backend.railway.app
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key
VITE_WEBSOCKET_URL=wss://your-backend.railway.app
```

## Development Deployment

To run the platform locally:

1. Clone the repository and install dependencies:

```bash
git clone <repo-url>
cd cygnusa-elite-hire

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install
```

2. Configure environment variables as described above.

3. Start the services:

```bash
# Terminal 1: Backend
cd backend
python app.py

# Terminal 2: WebSocket Server
cd backend
python websocket_server.py

# Terminal 3: Frontend
cd frontend
npm run dev
```

4. Access the application at `http://localhost:5173`.

## Production Deployment

### Database Setup

1. Create a Supabase project at [supabase.com](https://supabase.com).

2. Run the database schema:

```bash
psql $DATABASE_URL -f database/schema.sql
```

3. Enable Row Level Security policies in the Supabase dashboard.

4. Configure realtime subscriptions for the `violations` table.

### Backend Deployment (Railway)

1. Create a new project on [Railway](https://railway.app).

2. Connect your GitHub repository.

3. Add environment variables from the Backend Environment Variables section.

4. Set the start command:

```
python app.py
```

5. Deploy and note the generated URL.

### Frontend Deployment (Vercel)

1. Create a new project on [Vercel](https://vercel.com).

2. Connect your GitHub repository and set the root directory to `frontend/`.

3. Add environment variables from the Frontend Environment Variables section.

4. Set build settings:
   - Build Command: `npm run build`
   - Output Directory: `dist`

5. Deploy and configure a custom domain if needed.

## Post-Deployment Verification

After deployment, verify the following:

1. **Health Check**: Access `https://your-backend.railway.app/health` to confirm the backend is running.

2. **Database Connection**: Check logs to ensure Supabase connection is established.

3. **Authentication**: Test user registration and login flows.

4. **AI Integration**: Upload a test resume to verify AI parsing works.

5. **WebSocket Connection**: Start a test assessment to confirm real-time features work.

6. **Email Delivery**: Verify notification emails are sent successfully.

## Troubleshooting

### Database Connection Errors

If you see "could not connect to database" errors:

- Verify `DATABASE_URL` is correct and includes SSL parameters: `?sslmode=require`
- Check Supabase project status and connection pooling settings
- Ensure IP allowlisting is configured if required

### CORS Issues

If frontend requests are blocked:

- Verify `FRONTEND_URL` in backend environment matches your frontend domain
- Check CORS configuration in `app.py`
- Ensure both HTTP and HTTPS protocols are handled

### WebSocket Connection Failures

If real-time features don't work:

- Confirm WebSocket server is running separately from the main Flask app
- Verify `WEBSOCKET_URL` uses `wss://` protocol for production
- Check firewall rules allow WebSocket connections

### AI API Rate Limits

If AI features fail:

- Monitor API usage in OpenAI/Gemini dashboard
- Implement request queuing for high-volume scenarios
- Consider switching between providers based on rate limits

## Security Considerations

For production deployments:

- **Secrets Management**: Use platform-specific secret managers (Railway secrets, Vercel environment variables)
- **HTTPS Only**: Enforce HTTPS for all connections; redirect HTTP traffic
- **Rate Limiting**: Configure rate limits on API endpoints to prevent abuse
- **SQL Injection**: All database queries use parameterized statements
- **JWT Tokens**: Set short expiration times (1 hour access, 7 days refresh)
- **CORS**: Restrict allowed origins to known frontend domains only
- **File Uploads**: Validate file types and sizes; scan for malware if possible
- **API Keys**: Rotate keys regularly and monitor for unauthorized usage

## Scaling Recommendations

As your platform grows:

### Database Scaling

- Enable Supabase connection pooling (pgBouncer)
- Add read replicas for analytics queries
- Implement table partitioning for large tables (assessments, responses)
- Archive old data to cold storage

### Backend Scaling

- Deploy multiple backend instances with load balancing
- Implement Redis for session storage and caching
- Use background workers (Celery) for AI processing tasks
- Separate WebSocket servers from HTTP servers

### Frontend Scaling

- Enable CDN caching for static assets
- Implement code splitting for faster initial loads
- Use service workers for offline support
- Optimize images and use lazy loading

### Monitoring

- Set up application performance monitoring (APM)
- Configure error tracking (Sentry)
- Monitor API usage and costs
- Set up alerts for downtime and errors

## Next Steps

After successful deployment:

- Configure custom domain names
- Set up SSL certificates
- Implement backup and disaster recovery procedures
- Create a deployment pipeline with CI/CD
- Document rollback procedures
