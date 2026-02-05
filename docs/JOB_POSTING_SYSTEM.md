# Job Posting System with Sector-Based Access Control

## Overview

This document describes the enhanced job posting system with sector-based organization, role-based access control, and automatic candidate-job matching.

## Key Features

### 1. Sector-Based Organization

**What is it?**
- Sectors are organizational units (e.g., Engineering, Sales, Marketing, HR)
- Each sector has its own email address for communications
- Users can be assigned to specific sectors for access control

**Use Cases:**
- Large organizations with multiple departments
- Restricting job postings and candidate access by department
- Department-specific email communications

### 2. Enhanced Role-Based Access Control

**Roles:**
- **Super Admin**: Full access to all sectors and system-wide operations
- **Sector Admin**: Access only to their assigned sector's jobs and candidates
- **Recruiter/Interviewer**: Standard access based on assigned sector

**Access Control:**
- Super admins can create/edit jobs in any sector
- Sector admins can only manage jobs in their assigned sector
- All actions are logged in the audit trail

### 3. Required vs Preferred Skills

**Job Posting Enhancement:**
- **Required Skills**: Must-have skills for the position (weighted 60% in matching)
- **Preferred Skills**: Nice-to-have skills (weighted 20% in matching)
- Skills are stored as JSON arrays for flexible querying

**Example:**
```json
{
  "title": "Senior Software Engineer",
  "required_skills": ["Python", "JavaScript", "PostgreSQL"],
  "preferred_skills": ["React", "Docker", "AWS"],
  "min_experience": 5
}
```

### 4. Automatic Candidate-Job Matching

**How it Works:**
1. When a candidate's resume is uploaded, their skills are extracted
2. When a job posting is created, matching is triggered automatically
3. The system calculates match scores for all candidate-job combinations
4. Match score formula:
   - Required skills match: 60%
   - Preferred skills match: 20%
   - Experience requirement: 20%

**Matching Details:**
- Candidates are matched to ALL active job postings
- Results stored in `candidate_job_matches` table
- Each candidate gets a "best match" job assignment
- Match confidence score (0-100) indicates quality of fit

### 5. Comprehensive Audit Trail

**What is Logged:**
- Job creation, updates, deletions
- Candidate updates
- User creation and role changes
- Email sends with sender information
- Sector management actions

**Audit Log Fields:**
- User ID and email (who performed the action)
- Action type (create_job, send_email, etc.)
- Entity type and ID (what was affected)
- Detailed information (JSON)
- IP address and user agent
- Timestamp

## Database Schema Changes

### New Tables

#### `sectors`
```sql
- id: PRIMARY KEY
- name: Sector name (unique)
- description: Sector description
- email: Sector-specific email (e.g., eng@company.com)
- created_at, updated_at
```

#### `candidate_job_matches`
```sql
- id: PRIMARY KEY
- candidate_id: Foreign key to candidates
- job_id: Foreign key to job_descriptions
- match_score: 0-100 matching score
- required_skills_matched, required_skills_total
- preferred_skills_matched, preferred_skills_total
- experience_match: Boolean
- matching_details: JSON with full breakdown
```

#### `audit_logs`
```sql
- id: PRIMARY KEY
- user_id: Who performed the action
- user_email: Email of the user
- action: Action type (e.g., 'create_job')
- entity_type: Type of entity affected
- entity_id: ID of the entity
- details: JSON with additional context
- ip_address, user_agent
- created_at
```

### Enhanced Tables

#### `users`
- Added: `sector_id` (link to sectors)
- Added: `is_super_admin` (boolean flag)

#### `job_descriptions`
- Added: `sector_id` (link to sectors)
- Added: `required_skills_json` (JSONB array)
- Added: `preferred_skills_json` (JSONB array)
- Added: `status` ('active', 'closed', 'draft')
- Added: `created_by` (user who created the job)

#### `candidates`
- Added: `job_id` (manually assigned job)
- Added: `parsed_skills_json` (JSONB array)
- Added: `auto_matched_job_id` (best matching job)
- Added: `match_confidence` (0-100 confidence score)

#### `email_logs`
- Added: `sender_email` (who sent the email)
- Added: `sent_by_user_id` (user ID of sender)
- Added: `sector_id` (sector context)

## API Endpoints

### Sector Management

#### GET `/api/sectors`
Get all sectors (authenticated users)

#### POST `/api/sectors`
Create a new sector (super admin only)
```json
{
  "name": "Engineering",
  "description": "Software Development and Engineering roles",
  "email": "eng@company.com"
}
```

#### PUT `/api/sectors/:id`
Update a sector (super admin only)

#### DELETE `/api/sectors/:id`
Delete a sector (super admin only)

#### GET `/api/sectors/:id/stats`
Get statistics for a sector (sector admin or super admin)

### Enhanced Job Postings

#### GET `/api/jobs/enhanced`
Get all jobs with candidate counts
- Super admins see all jobs
- Sector admins see only their sector's jobs

Response includes:
- Job details
- Sector name and email
- Applied candidates count
- Matched candidates count
- Average match score

#### POST `/api/jobs/enhanced`
Create a new job posting
```json
{
  "title": "Senior Software Engineer",
  "description": "We are looking for...",
  "required_skills": ["Python", "JavaScript", "PostgreSQL"],
  "preferred_skills": ["React", "Docker", "AWS"],
  "min_experience": 5,
  "department": "Engineering",
  "location": "Remote",
  "sector_id": 1,
  "status": "active"
}
```

#### PUT `/api/jobs/enhanced/:id`
Update an existing job posting
- Automatically triggers re-matching if skills change

#### GET `/api/jobs/:id/candidates/matches`
Get all candidates matched to a specific job, sorted by match score

Response includes:
- Candidate details
- Match score
- Required skills matched/total
- Preferred skills matched/total
- Experience match status
- Detailed matching breakdown

#### GET `/api/candidates/:id/matches`
Get all jobs matched to a specific candidate, sorted by match score

### Candidate Matching

#### POST `/api/matching/trigger`
Manually trigger re-matching of all candidates to all jobs (admin only)

Returns statistics:
```json
{
  "candidates_processed": 150,
  "matches_created": 750
}
```

### Audit Logs

#### GET `/api/admin/audit-logs`
Get audit logs with optional filtering (admin only)

Query parameters:
- `limit`: Max number of logs (default: 100)
- `user_id`: Filter by user ID
- `action`: Filter by action type
- `entity_type`: Filter by entity type

## Matching Algorithm

### Score Calculation

```
Match Score = (
  Required Skills Match % × 0.6 +
  Preferred Skills Match % × 0.2 +
  Experience Score × 0.2
)
```

### Required Skills Match
- Count how many required skills the candidate has
- Percentage = (matched / total required) × 100
- Example: 3 out of 5 required skills = 60%

### Preferred Skills Match
- Count how many preferred skills the candidate has
- Percentage = (matched / total preferred) × 100
- If no preferred skills specified, defaults to 100%

### Experience Score
- If candidate meets minimum experience: 100%
- If candidate has less: (candidate_years / required_years) × 100

### Example Calculation

**Job Posting:**
- Required: Python, JavaScript, PostgreSQL (3 skills)
- Preferred: React, Docker (2 skills)
- Min Experience: 5 years

**Candidate:**
- Skills: Python, JavaScript, React, Go
- Experience: 6 years

**Calculation:**
- Required match: 2/3 = 66.67%
- Preferred match: 1/2 = 50%
- Experience: 6 >= 5 = 100%
- **Final Score**: (66.67 × 0.6) + (50 × 0.2) + (100 × 0.2) = **70.0**

## Migration Guide

### Running the Migration

1. Backup your database
2. Run the migration script:
```bash
psql $DATABASE_URL -f database/migrations/add_sectors_and_enhanced_job_postings.sql
```

### Post-Migration Steps

1. **Create Sectors**
   - Use the POST `/api/sectors` endpoint to create your organization's sectors
   - Default sectors (Engineering, Sales, Marketing, etc.) are auto-created

2. **Assign Users to Sectors**
   - Update existing users with their sector_id
   - Set is_super_admin = true for system administrators

3. **Update Job Postings**
   - Add sector_id to existing job postings
   - Populate required_skills_json and preferred_skills_json
   - Set status field ('active' by default)

4. **Trigger Initial Matching**
   - Call POST `/api/matching/trigger` to match existing candidates to jobs

## Frontend Integration

### Displaying Sector-Based Jobs

```javascript
// Fetch jobs for current user's sector
const response = await fetch('/api/jobs/enhanced', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
const { data: jobs } = await response.json();

// Each job includes:
// - sector_name, sector_email
// - required_skills_json, preferred_skills_json
// - applied_candidates_count, matched_candidates_count
```

### Creating Job with Skills

```javascript
const jobData = {
  title: "Senior Software Engineer",
  required_skills: ["Python", "JavaScript", "PostgreSQL"],
  preferred_skills: ["React", "Docker"],
  min_experience: 5,
  sector_id: 1
};

await fetch('/api/jobs/enhanced', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(jobData)
});
```

### Viewing Candidate Matches

```javascript
// Get candidates for a job, sorted by match score
const response = await fetch(`/api/jobs/${jobId}/candidates/matches`, {
  headers: { 'Authorization': `Bearer ${token}` }
});
const { data: matches } = await response.json();

// Display match details:
matches.forEach(match => {
  console.log(`${match.name}: ${match.match_score}% match`);
  console.log(`Required: ${match.required_skills_matched}/${match.required_skills_total}`);
  console.log(`Preferred: ${match.preferred_skills_matched}/${match.preferred_skills_total}`);
});
```

## Best Practices

1. **Sector Assignment**
   - Assign all users to appropriate sectors
   - Keep super admin count minimal for security

2. **Skills Management**
   - Use consistent skill names (e.g., "JavaScript" not "JS" or "javascript")
   - Keep skill lists concise and relevant
   - Review and update skills regularly

3. **Matching Frequency**
   - Automatic matching runs on job creation/update
   - Manual re-matching can be triggered for bulk updates
   - Consider running periodic re-matching for accuracy

4. **Audit Logs**
   - Review audit logs regularly for security
   - Use for debugging and compliance
   - Set up alerts for sensitive actions

5. **Performance**
   - GIN indexes on JSONB columns for fast skill queries
   - Materialized views for frequently accessed statistics
   - Consider caching match results for large datasets

## Troubleshooting

### Matching Not Working
- Check that candidates have parsed_skills_json populated
- Verify job postings have required_skills_json set
- Trigger manual matching via `/api/matching/trigger`

### Access Denied Errors
- Verify user has correct sector_id assigned
- Check is_super_admin flag for privileged operations
- Review role field (admin, interviewer, proctor)

### Slow Queries
- Ensure GIN indexes are created on JSONB columns
- Use EXPLAIN ANALYZE to identify bottlenecks
- Consider read replicas for analytics queries

## Future Enhancements

1. **AI-Powered Matching**
   - Use semantic similarity for skill matching
   - Consider job descriptions and resume text
   - Learn from successful hires

2. **Email Automation**
   - Auto-send notifications when candidates match jobs
   - Sector-specific email templates
   - Bulk email operations

3. **Advanced Analytics**
   - Sector performance dashboards
   - Matching accuracy metrics
   - Time-to-hire by sector

4. **Candidate Self-Service**
   - Candidates can view their matches
   - Apply directly to matched jobs
   - Track application status
