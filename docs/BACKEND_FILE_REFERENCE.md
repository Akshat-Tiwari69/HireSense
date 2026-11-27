# Backend File Reference

Reference for every backend Python file and its main functions. Line counts are
approximate (November 2026).

---

## File Overview

### Application and Routes

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~300 | Flask app setup, JWT config and revocation, blueprint registration, error handlers, health routes |
| `run.py` | ~20 | Development server entry point (`python run.py`) |
| `websocket_server.py` | ~470 | Socket.IO server for authenticated WebRTC signaling; exposes `app_with_socketio` |
| `auth.py` | ~290 | Login, demo login, current user, token verification |
| `resume_routes.py` | ~390 | Public application upload (`POST /api/resume/upload`) |
| `interviewer_routes.py` | ~950 | Hiring review API (interviewer, recruiter, sector admin) |
| `job_routes.py` | ~1,290 | Sectors, job postings, candidate-job matching, audit log |
| `proctor_routes.py` | ~630 | Proctor dashboard API, violations, evidence, statistics |
| `admin_routes.py` | ~30 | Parent admin blueprint that registers the four admin sub-blueprints |
| `admin_users.py` | ~330 | Staff user CRUD |
| `admin_candidates.py` | ~340 | Candidate list/edit/delete, status reset, missing details |
| `admin_content.py` | ~890 | Bulk ZIP upload, AI enhance, question banks |
| `admin_analytics.py` | ~140 | Analytics, database stats, email logs |
| `admin_middleware.py` | ~40 | `require_admin_role`, `require_super_admin_role` |
| `interviewee_routes.py` | ~30 | Parent candidate blueprint that registers the three sub-blueprints |
| `interviewee_session.py` | ~430 | Token verification, start/resume, remaining time |
| `interviewee_answers.py` | ~590 | Answer submission, code runs, completion and scoring |
| `interviewee_monitoring.py` | ~270 | Violation reports (with screenshot evidence) and time sync |

### Database Layer

> **Note:** The former `db_helpers.py` was split into focused domain modules. Callers now import those modules directly.

| File | Lines | Purpose |
|------|-------|---------|
| `db_config.py` | ~310 | `ThreadedConnectionPool`, TLS and production role checks, statement timeout |
| `user_db.py` | ~100 | User queries (`create_user`, `get_user_by_email`, `get_user_by_id`, `user_auth_version`) |
| `candidate_db.py` | ~310 | Candidate CRUD (`insert_candidate`, `get_candidate_by_id`, `get_all_candidates`, etc.) |
| `assessment_db.py` | ~1,520 | Assessments, responses, scoring, scheduling, token access |
| `proctoring_db.py` | ~220 | Violation recording and counts |
| `email_db.py` | ~100 | Email log reads/writes (`log_email`, `get_candidate_emails`) |

### Services and Utilities

| File | Lines | Purpose |
|------|-------|---------|
| `resume_analyzer.py` | ~640 | OpenAI resume analysis (pros/cons, match scoring) with rule-based fallback |
| `resume_parser.py` | ~80 | PDF/DOCX text extraction (pypdf, python-docx) |
| `email_service.py` | ~910 | Email notifications (Resend API or SMTP, chosen by `EMAIL_PROVIDER`) |
| `ai_question_generator.py` | ~1,060 | OpenAI question generation for assessments |
| `job_matcher.py` | ~460 | Rule-based scoring plus AI re-ranking of the top 5 matches |
| `questions_bank.py` | ~170 | Static fallback question bank |
| `code_runner_config.py` | ~35 | `code_runner_enabled()`, `code_runner_endpoint()` (Piston) |
| `storage_config.py` | ~70 | Private upload root (`get_upload_root`, `get_upload_subdirectory`, `is_within_upload_root`) |
| `demo_mode.py` | ~20 | `demo_mode_enabled()` and the demo account emails |
| `datetime_utils.py` | ~20 | `parse_client_datetime()` for timezone-aware input |
| `rate_limiter.py` | ~110 | Per-endpoint limits (Flask-Limiter, Redis when `REDIS_URL` is set) |
| `security_headers.py` | ~160 | HTTP security headers and CORS origin validation |
| `request_logger.py` | ~90 | Request logging with timing |

### Scripts

| File | Purpose |
|------|---------|
| `scripts/run_migration.py` | Apply the fresh schema (`--schema`) or reconcile an existing database (`--reconcile`) |
| `scripts/send_test_email.py` | Manual check that email delivery is configured |
| `scripts/_bootstrap.py` | Adds `backend/` to `sys.path` for the scripts |

---

## app.py

Creates the Flask app, loads `local.env` (if present) or `.env`, and configures:

- **JWT:** `JWT_SECRET_KEY` (required, validated), HS256, header-only tokens,
  lifetime from `JWT_ACCESS_TOKEN_MINUTES` (default 60). `_is_staff_token_revoked()`
  rejects tokens whose user was deleted, changed role, or was updated since login.
- **Middleware:** CORS, security headers, request logging, rate limiting.
- **Body limit:** 11 MB (`MAX_REQUEST_BODY_MB`), rejected early by `reject_oversized_request()`.

### Blueprint Registration

```python
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')
app.register_blueprint(interviewee_bp, url_prefix='/api/interviewee')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(proctor_bp, url_prefix='/api/proctor')
app.register_blueprint(jobs_bp, url_prefix='/api/jobs')
app.register_blueprint(resume_bp, url_prefix='/api')
```

### Routes

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/` | GET | `root()` | API info |
| `/api/health` | GET | `health_check()` | Liveness and `demo_mode` flag |
| `/api/health/ready` | GET | `readiness_check()` | PostgreSQL readiness and code-runner status |

---

## auth.py

| Route | Method | Function | Auth |
|-------|--------|----------|------|
| `/api/auth/login` | POST | `login()` | No |
| `/api/auth/demo-login` | POST | `demo_login()` | No (only when `DEMO_MODE=true`) |
| `/api/auth/me` | GET | `get_current_user()` | JWT |
| `/api/auth/verify` | GET | `verify_token()` | JWT |

Passwords are hashed with Werkzeug (`hash_password()`, `verify_password()`).
`login()` compares against a dummy hash for unknown emails so response time does
not reveal whether an account exists. There is no registration route; admins
create users through `admin_users.py`.

---

## resume_routes.py

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/api/resume/upload` | POST | `upload_resume()` | Validate and store a PDF/DOCX (max 10 MB), parse it, run AI analysis, and create the candidate |

The public response contains only the candidate ID, application status, and
the selected job; the analysis is visible to hiring staff only.

---

## interviewer_routes.py

All routes require a hiring-review role (`interviewer`, `recruiter`,
`sector_admin`) via `require_interviewer_role`, plus an assignment or sector
check.

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/candidates` | GET | `get_candidates()` | List candidates the reviewer can see |
| `/candidates/<id>` | GET | `get_candidate_details()` | Candidate details |
| `/candidates/<id>/resume` | GET | `download_resume()` | Download the stored resume |
| `/candidates/<id>/reject` | POST | `reject_candidate()` | Reject and send email |
| `/candidates/<id>/schedule` | POST | `schedule_assessment()` | Schedule, generate questions, email the link |
| `/assessments/<candidate_id>` | GET | `get_assessment_results()` | Assessment results |
| `/assessments/<id>/final-decision` | POST | `make_final_decision()` | Record hire/no-hire and email the candidate |

`_generate_assessment_questions()` generates MCQ, coding (technical roles only),
and psychometric questions in parallel. Scheduling a technical assessment fails
while `code_runner_enabled()` is false.

---

## interviewee_session.py, interviewee_answers.py, interviewee_monitoring.py

Registered under `/api/interviewee` by `interviewee_routes.py`. Every route
authenticates with the `X-Assessment-Token` header.

| Route | Method | Function | File |
|-------|--------|----------|------|
| `/assessment/verify` | GET | `verify_assessment_token()` | `interviewee_session.py` |
| `/assessment/start` | POST | `start_assessment_with_token()` | `interviewee_session.py` |
| `/assessment/<id>/remaining-time` | GET | `get_remaining_time()` | `interviewee_session.py` |
| `/assessment/<id>/submit-answer` | POST | `submit_answer()` | `interviewee_answers.py` |
| `/run-code` | POST | `run_code()` | `interviewee_answers.py` |
| `/assessment/<id>/complete` | POST | `complete_assessment()` | `interviewee_answers.py` |
| `/assessment/<id>/violation` | POST | `report_violation()` | `interviewee_monitoring.py` |
| `/assessment/<id>/sync-time` | POST | `sync_assessment_time()` | `interviewee_monitoring.py` |

Starting is allowed within ±30 minutes of the scheduled time. Scores are
computed server-side: MCQ answers against stored keys, coding by running the
stored test cases through Piston, and psychometric traits from the stored
scenarios.

---

## Admin sub-blueprints

Registered under `/api/admin` by `admin_routes.py`; all require
`require_admin_role`.

| File | Routes |
|------|--------|
| `admin_users.py` | `GET/POST /users`, `PUT/DELETE /users/<id>` (privileged accounts need `super_admin`) |
| `admin_candidates.py` | `GET /candidates`, `PUT/DELETE /candidates/<id>`, `POST /reset-candidate-status/<id>`, `GET /absence-of-details` |
| `admin_content.py` | `POST /bulk-upload`, `POST /ai-enhance`, `POST /question-bank/upload`, `GET /question-bank`, `GET/DELETE /question-bank/<id>`, `PATCH /question-bank/<id>/toggle` |
| `admin_analytics.py` | `GET /analytics`, `GET /db/stats`, `GET /email-logs` |

---

## job_routes.py and proctor_routes.py

See [API.md](API.md) for the full route lists. `job_routes.py` defines
`ROLE_HIERARCHY` and `require_role(min_role)`; `proctor_routes.py` restricts
every route to the `proctor` role and to assessments assigned to the proctor
or still unassigned.

---

## Database domain APIs

Historical combined reference for operations now implemented by `user_db.py`, `candidate_db.py`, `assessment_db.py`, `proctoring_db.py`, and `email_db.py`.

### User Operations

```python
def create_user(email, password_hash, role, name):
    """Create new user"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (email, password_hash, role, name)
        VALUES (?, ?, ?, ?)
    ''', (email, password_hash, role, name))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_user_by_email(email):
    """Get user by email"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id):
    """Get user by ID"""
    ...
```

### Candidate Operations

```python
def create_candidate(name, email, phone, resume_path, skills, 
                     experience, education, match_score, pros, cons):
    """Create new candidate"""
    ...

def get_candidate_by_id(candidate_id):
    """Get candidate by ID"""
    ...

def get_all_candidates(status=None, sort=None, order=None):
    """Get all candidates with optional filtering"""
    ...

def update_candidate_status(candidate_id, status):
    """Update candidate status"""
    ...

def update_candidate_analysis(candidate_id, pros, cons, 
                              overall_assessment, recommendation):
    """Update AI analysis results"""
    ...
```

### Assessment Operations

```python
def get_assessment_by_id(assessment_id):
    """Get assessment by ID"""
    ...

def finalize_assessment(assessment_id):
    """Atomically score and complete an assessment"""
    ...
```

### Scheduled Assessment Operations

```python
def create_scheduled_assessment(candidate_id, interviewer_id, 
                                scheduled_time, assessment_token):
    """Create scheduled assessment"""
    ...

def get_scheduled_assessment_by_token(token):
    """Get scheduled assessment by token"""
    ...

def check_assessment_time_valid(candidate_id, current_time, window_minutes=30):
    """Check if current time is within assessment window"""
    scheduled = get_scheduled_assessment_by_candidate(candidate_id)
    if not scheduled:
        return False, None, "No assessment scheduled"
    
    scheduled_time = datetime.fromisoformat(scheduled['scheduled_time'])
    current = datetime.fromisoformat(current_time)
    
    diff = abs((current - scheduled_time).total_seconds() / 60)
    
    if diff <= window_minutes:
        return True, scheduled_time, "Within window"
    else:
        return False, scheduled_time, f"Assessment is {int(diff)} minutes away"
```

### Score Calculation

```python
def calculate_mcq_score(assessment_id):
    """Calculate MCQ score percentage"""
    responses = get_mcq_responses(assessment_id)
    correct = sum(1 for r in responses if r['is_correct'])
    total = len(responses)
    return (correct / total * 100) if total > 0 else 0

def calculate_coding_score(assessment_id):
    """Calculate coding score from test results"""
    submissions = get_coding_submissions(assessment_id)
    if not submissions:
        return 0
    latest = submissions[-1]
    return latest['score']

def calculate_psychometric_score(assessment_id):
    """Calculate psychometric score from trait ratings"""
    responses = get_psychometric_responses(assessment_id)
    all_scores = []
    for r in responses:
        trait_scores = json.loads(r['trait_scores'])
        all_scores.extend(trait_scores.values())
    avg = sum(all_scores) / len(all_scores) if all_scores else 0
    return avg * 10  # Convert 1-10 scale to 0-100
```

---

## resume_analyzer.py

OpenAI-powered resume analysis.

### Class: ResumeAnalyzer

```python
class ResumeAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"
    
    def generate_pros_cons(self, resume_text, parsed_data, job_requirements):
        """Generate pros and cons using GPT"""
        prompt = self._build_prompt(resume_text, parsed_data, job_requirements)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert HR recruiter..."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return self._parse_response(response.choices[0].message.content)
    
    def enhance_match_score(self, resume_text, parsed_data, job_requirements):
        """Calculate AI-enhanced match score"""
        ...
```

### Convenience Function

```python
def analyze_resume(resume_text, parsed_data, job_requirements=None, 
                   api_key=None, enhance_score=True):
    """Main function to analyze resume"""
    try:
        analyzer = ResumeAnalyzer(api_key)
        result = analyzer.generate_pros_cons(
            resume_text, parsed_data, job_requirements
        )
        
        if enhance_score:
            result['enhanced_match_score'] = analyzer.enhance_match_score(
                resume_text, parsed_data, job_requirements
            )
        
        return result
    except Exception as e:
        # Return fallback analysis
        return generate_fallback_analysis(parsed_data)
```

---

## resume_parser.py

Resume text extraction.

### Functions

```python
def extract_text_from_pdf(file_path):
    """Extract text from PDF using pypdf"""
    text = ""
    with open(file_path, 'rb') as file:
        reader = pypdf.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(file_path):
    """Extract text from DOCX using python-docx"""
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_file(file_path):
    """Extract text based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def parse_resume(resume_text):
    """Parse resume text to extract structured data"""
    return {
        'skills': extract_skills(resume_text),
        'experience': extract_experience(resume_text),
        'education': extract_education(resume_text),
        'contact': extract_contact(resume_text)
    }
```

---

## email_service.py

Email notification service.

### Class: EmailService

```python
class EmailService:
    def __init__(self):
        self.resend_key = os.environ.get('RESEND_API_KEY')
        self.smtp_host = os.environ.get('SMTP_HOST')
        self.smtp_user = os.environ.get('SMTP_USER')
        self.smtp_pass = os.environ.get('SMTP_PASS')
    
    def send_email(self, to_email, subject, html_body, text_body):
        """Send email using Resend or SMTP"""
        if self.resend_key:
            return self._send_via_resend(to_email, subject, html_body)
        elif self.smtp_host:
            return self._send_via_smtp(to_email, subject, html_body, text_body)
        else:
            raise ValueError("No email service configured")
```

### Convenience Functions

```python
def send_rejection_email(candidate_email, candidate_name, reason=None):
    """Send rejection email"""
    ...

def send_assessment_invitation(candidate_email, candidate_name, 
                               assessment_link, scheduled_time, 
                               interviewer_name=None):
    """Send assessment invitation email"""
    ...

def send_final_decision_email(candidate_email, candidate_name, 
                              decision, rationale=None, 
                              next_steps=None, scores=None):
    """Send final hiring decision email"""
    ...
```

---

## questions_bank.py

Assessment questions storage.

### Structure

```python
MCQ_QUESTIONS = [
    {
        "id": 1,
        "question": "Question text",
        "options": ["A", "B", "C", "D"],
        "correct_answer": 0,  # Index of correct option
        "category": "Category",
        "difficulty": "easy|medium|hard"
    },
    ...
]

CODING_PROBLEMS = [
    {
        "id": 1,
        "title": "Problem Title",
        "description": "Problem description",
        "example": "Example input/output",
        "test_cases": [
            {"input": "...", "expected": "..."},
            ...
        ],
        "difficulty": "easy|medium|hard",
        "time_limit": 30  # minutes
    },
    ...
]

PSYCHOMETRIC_SCENARIOS = [
    {
        "id": 1,
        "scenario": "Scenario description",
        "traits": ["trait1", "trait2"],
        "expected_behaviors": ["behavior1", "behavior2"]
    },
    ...
]
```

### Functions

```python
def get_random_mcq_questions(count=10):
    """Get random MCQ questions"""
    return random.sample(MCQ_QUESTIONS, min(count, len(MCQ_QUESTIONS)))

def get_random_coding_problem():
    """Get random coding problem"""
    return random.choice(CODING_PROBLEMS)

def get_psychometric_scenarios():
    """Get all psychometric scenarios"""
    return PSYCHOMETRIC_SCENARIOS
```

---

## scripts/run_migration.py

The database entry point has two explicit modes:

```bash
# Fresh, empty PostgreSQL database
python scripts/run_migration.py --schema

# Existing HireSense database with a legacy schema
python scripts/run_migration.py --reconcile
```

The script reads `DATABASE_URL`, serializes concurrent schema work with a
PostgreSQL advisory lock, performs mode-specific preflight checks, runs the
canonical SQL transactionally, and verifies required tables and columns before
committing. It does not create default accounts or embed default passwords.

---

## Database Domain Modules

> Added in May 2026. Previously all of this lived in `db_helpers.py`.

### user_db.py

Authentication and user lookup. All other modules import `DatabaseError` from here.

| Function | Returns | Description |
|----------|---------|-------------|
| `create_user(email, password_hash, role, name)` | `int` | Insert user, return new user ID |
| `get_user_by_email(email)` | `dict \| None` | Cached lookup by email (LRU 128) |
| `get_user_by_id(user_id)` | `dict \| None` | Cached lookup by ID (LRU 256) |

### candidate_db.py

Candidate CRUD operations.

| Function | Returns | Description |
|----------|---------|-------------|
| `get_candidate_by_email(email)` | `dict \| None` | Case-insensitive email lookup |
| `insert_candidate(name, email, phone, resume_path, parsed_data, pros, cons, status)` | `int` | Insert candidate, return ID |
| `get_candidate_by_id(candidate_id)` | `dict \| None` | Fetch candidate with parsed skills list |
| `get_all_candidates()` | `list[dict]` | All candidates ordered by created_at DESC |
| `update_candidate_shortlist(candidate_id, status, score)` | — | Update shortlist status and match score |
| `update_candidate_status(candidate_id, status, pros, cons)` | `bool` | Update status, optionally update pros/cons |

### assessment_db.py

Assessment lifecycle, response tracking, scoring, scheduling, and token access.

**Core assessment:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_assessment_by_id(assessment_id)` | `dict \| None` | Fetch assessment record |
| `get_assessment_by_candidate_id(candidate_id)` | `dict \| None` | Most recent assessment for a candidate |
| `finalize_assessment(assessment_id)` | `dict` | Atomically score, complete, and synchronize linked lifecycle rows |
| `record_final_decision(assessment_id, decision, rationale)` | `dict \| None` | Store the human outcome separately from automated recommendations |

**Response tracking:**

| Function | Returns | Description |
|----------|---------|-------------|
| `save_mcq_response(assessment_id, question_id, selected_answer, is_correct, time_spent)` | — | Upsert MCQ answer |
| `get_saved_mcq_answers(assessment_id)` | `dict` | `{question_id: selected_answer}` |
| `save_coding_submission(assessment_id, problem_id, language, code, test_cases_passed, total_test_cases)` | — | Upsert coding submission |
| `get_saved_coding_submission(assessment_id)` | `dict \| None` | Latest coding submission |
| `save_psychometric_response(assessment_id, question_id, trait, score, scenario_response)` | — | Upsert psychometric response |
| `get_saved_psychometric_answers(assessment_id)` | `dict` | `{question_id: selected_option_index}` |

**Scoring:**

| Function | Returns | Description |
|----------|---------|-------------|
| `get_mcq_score(assessment_id)` | `float` | Percentage correct (0-100) |
| `get_coding_score(assessment_id)` | `float` | Test cases passed percentage |
| `get_psychometric_scores(assessment_id)` | `dict` | `{trait: avg_score}` |

**Scheduling:**

| Function | Returns | Description |
|----------|---------|-------------|
| `create_scheduled_assessment(candidate_id, interviewer_id, scheduled_time, is_technical_role, questions_data)` | `int` | Schedule an assessment, return ID |
| `get_scheduled_assessment(candidate_id)` | `dict \| None` | Scheduled assessment for a candidate |
| `update_scheduled_assessment_status(scheduled_assessment_id, status, assessment_id)` | `bool` | Update status (scheduled/in_progress/completed) |
| `check_assessment_time_valid(candidate_id, current_time, window_minutes)` | `tuple(bool, str, str)` | Check ±30 min window validity |

**Token access:**

| Function | Returns | Description |
|----------|---------|-------------|
| `generate_assessment_token()` | `str` | Secure random URL-safe token |
| `set_assessment_token(scheduled_assessment_id, token)` | `bool` | Assign token to scheduled assessment |
| `get_assessment_by_token(token)` | `dict \| None` | Fetch assessment and candidate info by token |
| `start_assessment_by_token(token)` | `bool` | Mark as in_progress and record start time |

**Questions and time:**

| Function | Returns | Description |
|----------|---------|-------------|
| `save_assessment_questions(assessment_id, questions_data)` | — | Store pre-generated questions |
| `get_assessment_questions(assessment_id)` | `dict \| None` | Retrieve stored questions |
| `update_assessment_time_elapsed(assessment_id, time_elapsed_seconds)` | — | Update elapsed time |
| `get_assessment_time_elapsed(assessment_id)` | `int` | Seconds elapsed since started_at |

### proctoring_db.py

Proctoring event logging and violation tracking.

| Function | Returns | Description |
|----------|---------|-------------|
| `log_proctoring_event(assessment_id, event_type, severity, details)` | — | Log event and increment violation counter |
| `record_proctoring_violation(assessment_id, violation_type, description, severity, screenshot_path)` | `int` | Record violation with an optional private evidence path |
| `get_violations_for_assessment(assessment_id)` | `list[dict]` | All violations ordered by timestamp DESC |
| `count_violations_for_assessment(assessment_id)` | `int` | Total violation count |

### email_db.py

Email log persistence (used by `email_service.py`).

| Function | Returns | Description |
|----------|---------|-------------|
| `log_email(recipient_email, recipient_name, email_type, subject, status, error_message)` | `int` | Insert email log entry, return ID |
| `get_candidate_emails(candidate_email)` | `list[dict]` | All emails sent to a candidate, newest first |

---

## Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [API.md](API.md) - API reference
- [DATABASE.md](DATABASE.md) - Database structure

---

*Last Updated: May 2026*
