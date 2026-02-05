# Database Schema

The application uses **PostgreSQL** with the following schema structure.

## 📊 Entity Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ INTERVIEWS : conducts
    CANDIDATES ||--o{ ASSESSMENTS : takes
    CANDIDATES ||--o{ INTERVIEWS : attends
    ASSESSMENTS ||--o{ ASSESSMENT_LOGS : generates

    USERS {
        uuid id PK
        string email
        string password_hash
        string role "admin, interviewer, proctor"
        string name
        timestamp created_at
    }

    CANDIDATES {
        uuid id PK
        string email
        string full_name
        text resume_text
        jsonb skills
        float ai_score
        string status "new, screening, interviewed, hired"
    }

    ASSESSMENTS {
        uuid id PK
        uuid candidate_id FK
        string status "scheduled, in_progress, completed"
        float score
        jsonb technical_answers
        int warning_count
        timestamp start_time
        timestamp end_time
    }

    INTERVIEWS {
        uuid id PK
        uuid candidate_id FK
        uuid interviewer_id FK
        timestamp scheduled_at
        text meet_link
        string status
    }
```

## 🗄️ Tables Reference

### `users`
System users with access to dashboards.
- **role**: Determines access level (`admin`, `interviewer`, `proctor`).

### `candidates`
Applicants who have submitted their resumes.
- **resume_text**: Full text extracted from PDF/DOCX.
- **ai_score**: Initial ranking score (0-100) based on resume analysis.

### `assessments`
Technical tests taken by candidates.
- **warning_count**: Number of proctoring flags (e.g., Tab focus lost).
- **technical_answers**: JSON object storing question-answer pairs.

### `email_logs`
Audit log of all system-sent emails.
- **status**: `sent`, `failed`.
- **metadata**: API response from email provider.
