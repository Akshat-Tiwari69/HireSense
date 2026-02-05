# Sector-Based Access Control & Skillset Management - Implementation Guide

## Overview
This document describes the implementation of sector-based access control and skillset management features added to the Cygnusa Elite-Hire recruitment platform.

## Features Implemented

### 1. Sector-Based Email Configuration
- **Purpose**: Enable different departments/sectors to have their own email addresses for candidate communications
- **Database**: New `sector_email_configs` table
- **API Endpoints**:
  - `GET /api/admin/sector-emails` - List all sector email configurations
  - `POST /api/admin/sector-emails` - Create new sector email config (Super Admin only)
  - `PUT /api/admin/sector-emails/<sector>` - Update sector email config (Super Admin only)
  
- **Sectors Supported**: engineering, sales, marketing, hr, finance, operations
- **Email Service**: Updated to use sector-specific sender addresses

### 2. Role-Based Access Control (RBAC)

#### New Roles Added
1. **Super Admin** (`super_admin`)
   - Full system access
   - Can manage all sectors
   - Can create/update sector email configurations
   - Can view all audit logs

2. **Sector Admin** (`sector_admin`)
   - Manages a specific sector
   - Can only view/manage jobs and candidates in their assigned sector
   - Can view audit logs for their sector

3. **Recruiter** (`recruiter`)
   - Works within a specific sector
   - Can create jobs and manage candidates in their sector
   - Limited administrative access

4. **Interviewer** (`interviewer`)
   - Global access to conduct interviews
   - No sector restrictions

5. **Admin** (`admin`)
   - Global administrative access (legacy role)
   - Full system management

6. **Proctor** (`proctor`)
   - Monitors assessments
   - No sector restrictions

#### Access Control Implementation
- **File**: `backend/access_control.py`
- **Decorators**:
  - `@require_role(*roles)` - Enforce specific roles
  - `@require_sector_access()` - Enforce sector-based filtering
  - `@require_any_admin()` - Allow any admin role
  - `@require_super_admin()` - Super admin only
  
- **Helper Functions**:
  - `can_access_sector(user_sector, user_role, target_sector)` - Check sector access
  - `filter_by_sector_access(items, sector_field)` - Filter list by sector

### 3. Audit Trail System
- **Purpose**: Track all user actions for compliance and security
- **Database**: New `audit_logs` table
- **Fields Tracked**:
  - user_id, user_email
  - action (create, update, delete, view)
  - resource_type (job, candidate, user, sector_email_config)
  - resource_id
  - details (JSON with additional context)
  - ip_address, user_agent
  - timestamp

- **Implementation**: `backend/audit_middleware.py`
- **Usage**: `@audit_log('create', 'job')` decorator
- **API**: `GET /api/admin/audit-logs?limit=100&action=create&resource_type=job`

### 4. Enhanced Job Posting Management

#### Database Schema Updates
- Added `sector` field - assign jobs to specific sectors
- Added `preferred_skills` field - skills that are nice-to-have (separate from required_skills)

#### API Updates
- **POST /api/admin/job-postings**
  - Requires `required_skills` to be specified
  - Supports `preferred_skills` (optional)
  - Supports `sector` assignment
  - Sector admins can only create jobs in their sector
  - Logs creation in audit trail

- **GET /api/admin/job-postings**
  - Returns jobs filtered by user's sector access
  - Super admin sees all jobs
  - Sector admin sees only their sector's jobs

#### Frontend Updates
- Job posting form includes:
  - Required Skills field (mandatory)
  - Preferred Skills field (optional)
  - Sector dropdown selection

### 5. Candidate Skill Collection

#### Database Schema Updates
- Added `skills` field (JSONB) - candidate's self-reported skills
- Added `sector` field - target sector for application
- Maintained `parsed_skills` (TEXT) - skills extracted from resume by AI

#### Candidate Application Form
- **New Fields**:
  - Skills input (comma-separated)
  - Sector selection dropdown
  
- **Backend Processing**:
  - Skills are parsed from comma-separated string to JSON array
  - Stored in `skills` JSONB field for efficient querying
  - Sector assignment recorded for filtering

#### API Updates
- **POST /api/resume/upload**
  - Accepts `skills` form field (comma-separated string)
  - Accepts `sector` form field
  - Updated `insert_candidate()` to store new fields

### 6. Email Sender Tracking
- **Database**: Updated `email_logs` table
- **New Fields**:
  - `sender_user_id` - ID of user who triggered the email
  - `sender_email` - Email address of sender
  - `sector` - Sector associated with the email
  
- **Purpose**: Complete audit trail of who sent what to whom

## Database Migration

### Migration Script
Location: `database/migrations/001_sector_and_skills_enhancement.sql`

To apply the migration:
```sql
-- Run this SQL script on your PostgreSQL database
\i database/migrations/001_sector_and_skills_enhancement.sql
```

### Schema Changes Summary
1. **users** table:
   - Added `sector` (TEXT)

2. **candidates** table:
   - Added `sector` (TEXT)
   - Added `skills` (JSONB with GIN index)

3. **job_descriptions** table:
   - Added `sector` (TEXT)
   - Added `preferred_skills` (TEXT)

4. **email_logs** table:
   - Added `sender_user_id` (INTEGER FK)
   - Added `sender_email` (TEXT)
   - Added `sector` (TEXT)

5. **New Tables**:
   - `sector_email_configs` - Sector email configurations
   - `audit_logs` - User action audit trail

## API Authentication & Authorization

### JWT Token Updates
Tokens now include:
- `role` - User's role
- `name` - User's name
- `sector` - User's assigned sector (if applicable)

### Registration Updates
- **POST /api/auth/register**
  - New optional field: `sector`
  - Validation: `sector_admin` and `recruiter` roles require a sector
  - Example:
    ```json
    {
      "email": "eng.admin@company.com",
      "password": "SecurePass123",
      "name": "Engineering Admin",
      "role": "sector_admin",
      "sector": "engineering"
    }
    ```

### Login Response
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "user": {
      "id": 1,
      "email": "user@company.com",
      "role": "sector_admin",
      "name": "User Name",
      "sector": "engineering"
    }
  }
}
```

## Access Control Examples

### Example 1: Sector Admin Creating a Job
```javascript
// Sector admin for "engineering" tries to create a sales job
POST /api/admin/job-postings
Authorization: Bearer <token_with_sector=engineering>

{
  "title": "Sales Representative",
  "required_skills": "Communication, Negotiation",
  "sector": "sales"  // ❌ Will be rejected - sector mismatch
}

// Response: 403 Forbidden
{
  "status": "error",
  "message": "Sector admins can only create jobs in their assigned sector"
}
```

### Example 2: Filtering Candidates by Sector
```javascript
// Recruiter with sector="sales" requests candidates
GET /api/admin/candidates
Authorization: Bearer <token_with_role=recruiter,sector=sales>

// Response: Only candidates with sector="sales" are returned
```

### Example 3: Super Admin Access
```javascript
// Super admin can access all sectors
GET /api/admin/job-postings
Authorization: Bearer <token_with_role=super_admin>

// Response: Returns ALL jobs from ALL sectors
```

## Testing the Implementation

### 1. Test Candidate Application with Skills
```bash
curl -X POST http://localhost:5000/api/resume/upload \
  -F "file=@resume.pdf" \
  -F "skills=Python,React,AWS,Docker" \
  -F "sector=engineering"
```

### 2. Test Job Creation with Required Skills
```bash
curl -X POST http://localhost:5000/api/admin/job-postings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Developer",
    "required_skills": "Python, Django, PostgreSQL",
    "preferred_skills": "Docker, Kubernetes, AWS",
    "sector": "engineering",
    "min_experience": 5
  }'
```

### 3. Test Sector Email Configuration
```bash
# Create sector email config (Super Admin only)
curl -X POST http://localhost:5000/api/admin/sector-emails \
  -H "Authorization: Bearer <super_admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sector": "finance",
    "email_address": "finance@company.com",
    "display_name": "Finance Department"
  }'
```

### 4. Test Audit Logs
```bash
# View audit logs
curl -X GET "http://localhost:5000/api/admin/audit-logs?limit=50&resource_type=job" \
  -H "Authorization: Bearer <admin_token>"
```

## Frontend Integration

### Candidate Application Form (ApplyPage.jsx)
- Added skills input field (comma-separated)
- Added sector dropdown
- Sends skills and sector with resume upload

### Admin Dashboard (AdminDashboardPage.jsx)
- Updated job posting form with:
  - Required skills field (mandatory)
  - Preferred skills field (optional)
  - Sector selection dropdown
- Job listings filtered by user's sector access
- Candidate listings filtered by user's sector access

## Security Considerations

1. **Role Validation**: All roles are validated server-side
2. **Sector Isolation**: Sector admins and recruiters cannot access other sectors' data
3. **Audit Trail**: All administrative actions are logged
4. **Email Tracking**: All sent emails are tracked with sender information
5. **JWT Claims**: User's role and sector are embedded in JWT for fast authorization

## Future Enhancements

1. **Skill Matching Algorithm**: Implement intelligent matching between candidate skills and job requirements
2. **Sector Dashboard Analytics**: Sector-specific analytics and reports
3. **Email Templates**: Sector-specific email templates
4. **Multi-Sector Access**: Allow users to be assigned to multiple sectors
5. **Skill Recommendations**: AI-powered skill recommendations for candidates
6. **Advanced Search**: Search candidates by skills using JSONB queries

## Support

For questions or issues related to these features, please contact the development team or refer to:
- API Documentation: `/docs/API.md`
- Database Schema: `/docs/DATABASE.md`
- Architecture: `/docs/ARCHITECTURE.md`
