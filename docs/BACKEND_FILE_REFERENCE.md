# Backend File Reference

Complete reference for all backend Python files and their functions.

---

## File Overview

### Route Files

| File | Lines | Purpose |
|------|-------|---------|
| `app.py` | ~1,080 | Main Flask application, blueprints, resume endpoints |
| `auth.py` | ~390 | JWT authentication blueprint |
| `admin_routes.py` | ~1,815 | Admin dashboard API (users, jobs, sectors, analytics) |
| `interviewer_routes.py` | ~770 | Interviewer dashboard API |
| `interviewee_routes.py` | ~1,220 | Candidate assessment API |
| `proctor_routes.py` | ~340 | Proctoring API |
| `job_routes.py` | ~660 | Job listings and matching API |

### Database Layer

> **Note:** `db_helpers.py` was split into focused domain modules in May 2026.
> It is now a thin re-export hub — all existing imports continue to work unchanged.

| File | Functions | Purpose |
|------|-----------|---------|
| `db_helpers.py` | re-exports all | Backward-compatible re-export hub |
| `user_db.py` | 3 | User auth queries (`create_user`, `get_user_by_email`, `get_user_by_id`) |
| `candidate_db.py` | 6 | Candidate CRUD (`insert_candidate`, `get_candidate_by_id`, `get_all_candidates`, etc.) |
| `assessment_db.py` | 25 | Assessments, responses, scoring, scheduling, token access |
| `proctoring_db.py` | 4 | Violation recording (`record_proctoring_violation`, `count_violations_for_assessment`, etc.) |
| `email_db.py` | 2 | Email log reads/writes (`log_email`, `get_candidate_emails`) |
| `db_config.py` | — | PostgreSQL connection via `DATABASE_URL` |

### Services & Utilities

| File | Lines | Purpose |
|------|-------|---------|
| `resume_analyzer.py` | ~545 | OpenAI resume analysis (pros/cons, match scoring) |
| `resume_parser.py` | ~150 | PDF/DOCX text extraction (PyPDF2, python-docx) |
| `email_service.py` | ~800 | Email notifications (Resend API + SMTP fallback) |
| `ai_question_generator.py` | ~810 | GPT-4o-mini question generation for assessments |
| `job_matcher.py` | ~400 | Rule-based + AI job-candidate matching |
| `questions_bank.py` | ~200 | Static fallback question bank |
| `websocket_server.py` | ~350 | Socket.IO signaling server for WebRTC proctoring |
| `rate_limiter.py` | — | Per-endpoint rate limiting (Flask-Limiter) |
| `security_headers.py` | — | HTTP security header middleware |
| `request_logger.py` | — | Request logging middleware |

---

## app.py

Main Flask application entry point.

### Initialization

```python
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

app = Flask(__name__)
CORS(app)
jwt = JWTManager(app)
```

### Blueprint Registration

```python
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp
from admin_routes import admin_bp
from proctor_routes import proctor_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')
app.register_blueprint(interviewee_bp, url_prefix='/api/interviewee')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(proctor_bp, url_prefix='/api/proctor')
```

### Key Routes

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/api/health` | GET | `health_check()` | Server health status |
| `/api/resume/upload` | POST | `upload_resume()` | Upload resume with AI analysis |
| `/api/assessment/start` | POST | `start_assessment()` | Start assessment session |
| `/api/assessment/mcq/submit` | POST | `submit_mcq()` | Submit MCQ answer |
| `/api/assessment/code/submit` | POST | `submit_code()` | Submit code solution |
| `/api/assessment/psychometric/submit` | POST | `submit_psychometric()` | Submit psychometric response |
| `/api/assessment/complete` | POST | `complete_assessment()` | Complete and score assessment |

### Resume Upload Function

```python
@app.route('/api/resume/upload', methods=['POST'])
def upload_resume():
    """Handle resume upload with AI analysis"""
    # 1. Validate file
    file = request.files.get('file')
    
    # 2. Save file
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    # 3. Extract text
    resume_text = extract_text_from_file(file_path)
    
    # 4. Parse resume data
    parsed_data = parse_resume(resume_text)
    
    # 5. AI analysis
    ai_analysis = analyze_resume(resume_text, parsed_data)
    
    # 6. Save to database
    candidate_id = create_candidate(...)
    
    return jsonify({...})
```

---

## auth.py

JWT authentication blueprint.

### Routes

| Route | Method | Function | Auth Required |
|-------|--------|----------|---------------|
| `/register` | POST | `register()` | No |
| `/login` | POST | `login()` | No |
| `/me` | GET | `get_current_user()` | Yes |
| `/verify` | GET | `verify_token()` | Yes |

### Key Functions

```python
@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    
    # Validate
    if not all([data.get('email'), data.get('password'), 
                data.get('role'), data.get('name')]):
        return error_response('Missing fields', 400)
    
    # Hash password
    password_hash = bcrypt.hashpw(
        data['password'].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Create user
    user_id = create_user(
        email=data['email'],
        password_hash=password_hash,
        role=data['role'],
        name=data['name']
    )
    
    return success_response({'user_id': user_id}, 201)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return JWT"""
    data = request.json
    
    # Get user
    user = get_user_by_email(data['email'])
    if not user:
        return error_response('Invalid credentials', 401)
    
    # Verify password
    if not bcrypt.checkpw(data['password'].encode(), 
                          user['password_hash'].encode()):
        return error_response('Invalid credentials', 401)
    
    # Create token with claims
    access_token = create_access_token(
        identity=user['id'],
        additional_claims={
            'role': user['role'],
            'name': user['name']
        }
    )
    
    return success_response({
        'access_token': access_token,
        'user': {...}
    })
```

---

## interviewer_routes.py

Interviewer dashboard API.

### Routes

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/candidates` | GET | `get_candidates()` | List all candidates |
| `/candidates/<id>` | GET | `get_candidate()` | Candidate details |
| `/candidates/<id>/reject` | POST | `reject_candidate()` | Reject candidate |
| `/candidates/<id>/schedule` | POST | `schedule_assessment()` | Schedule assessment |
| `/assessments/<id>` | GET | `get_assessment()` | Assessment results |
| `/assessments/<id>/final-decision` | POST | `final_decision()` | Make hiring decision |
| `/dashboard/stats` | GET | `get_stats()` | Dashboard statistics |

### Key Functions

```python
@interviewer_bp.route('/candidates/<int:id>/schedule', methods=['POST'])
@jwt_required()
def schedule_assessment(id):
    """Schedule assessment for candidate"""
    claims = get_jwt()
    if claims.get('role') != 'interviewer':
        return error_response('Access denied', 403)
    
    data = request.json
    scheduled_time = data.get('scheduled_time')
    
    # Create scheduled assessment with token
    token = secrets.token_urlsafe(32)
    scheduled_id = create_scheduled_assessment(
        candidate_id=id,
        interviewer_id=get_jwt_identity(),
        scheduled_time=scheduled_time,
        assessment_token=token
    )
    
    # Update candidate status
    update_candidate_status(id, 'under_review')
    
    # Send invitation email
    candidate = get_candidate_by_id(id)
    send_assessment_invitation(
        candidate_email=candidate['email'],
        candidate_name=candidate['name'],
        assessment_link=f"{FRONTEND_URL}/assessment/{token}",
        scheduled_time=scheduled_time
    )
    
    return success_response({
        'scheduled_assessment_id': scheduled_id,
        'assessment_token': token
    }, 201)
```

---

## interviewee_routes.py

Candidate assessment API.

### Routes

| Route | Method | Function | Description |
|-------|--------|----------|-------------|
| `/my-assessment/<id>` | GET | `get_my_assessment()` | Check assessment status |
| `/assessment/verify/<token>` | GET | `verify_assessment_token()` | Verify token validity |
| `/assessment/start/<id>` | POST | `start_assessment()` | Start by candidate ID |
| `/assessment/start-by-token/<token>` | POST | `start_by_token()` | Start by token |
| `/assessment/<id>/complete` | POST | `complete_assessment()` | Complete assessment |
| `/proctor/report-violation` | POST | `report_violation()` | Report proctoring event |

### Key Functions

```python
@interviewee_bp.route('/assessment/verify/<token>', methods=['GET'])
def verify_assessment_token(token):
    """Verify assessment token and time window"""
    # Get scheduled assessment
    scheduled = get_scheduled_assessment_by_token(token)
    if not scheduled:
        return error_response('Invalid token', 404)
    
    # Check time window
    current_time = datetime.utcnow()
    scheduled_time = datetime.fromisoformat(scheduled['scheduled_time'])
    
    window_start = scheduled_time - timedelta(minutes=30)
    window_end = scheduled_time + timedelta(minutes=30)
    
    can_start = window_start <= current_time <= window_end
    
    return success_response({
        'valid': True,
        'can_start': can_start,
        'scheduled_time': scheduled['scheduled_time'],
        'candidate_name': scheduled['candidate_name']
    })

@interviewee_bp.route('/assessment/start-by-token/<token>', methods=['POST'])
def start_by_token(token):
    """Start assessment using token"""
    # Verify token
    scheduled = get_scheduled_assessment_by_token(token)
    if not scheduled:
        return error_response('Invalid token', 404)
    
    # Check time window
    is_valid, _, message = check_assessment_time_valid(
        scheduled['candidate_id'],
        datetime.utcnow().isoformat()
    )
    
    if not is_valid:
        return error_response(message, 403)
    
    # Create assessment
    assessment_id = create_assessment(scheduled['candidate_id'])
    
    # Get questions
    mcq_questions = get_random_mcq_questions(10)
    coding_problem = get_random_coding_problem()
    psychometric_scenarios = get_psychometric_scenarios()
    
    return success_response({
        'assessment_id': assessment_id,
        'mcq_questions': mcq_questions,
        'coding_problem': coding_problem,
        'psychometric_scenarios': psychometric_scenarios
    }, 201)
```

---

## db_helpers.py

Database operations module.

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
def create_assessment(candidate_id):
    """Create new assessment session"""
    ...

def get_assessment_by_id(assessment_id):
    """Get assessment by ID"""
    ...

def update_assessment_scores(assessment_id, mcq_score, coding_score,
                             technical_score, psychometric_score, overall_score):
    """Update assessment scores"""
    ...

def complete_assessment(assessment_id, decision, rationale):
    """Mark assessment as complete"""
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
    """Extract text from PDF using PyPDF2"""
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
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

## init_db.py

Database initialization script.

```python
def init_database():
    """Initialize database with schema"""
    conn = get_db_connection()
    
    # Read and execute schema
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    conn.executescript(schema)
    conn.commit()
    conn.close()
    
    print("Database initialized successfully")

def seed_default_users():
    """Create default admin and interviewer"""
    import bcrypt
    
    # Admin user
    admin_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
    create_user('admin@company.com', admin_hash, 'admin', 'Admin User')
    
    # Default interviewer
    interviewer_hash = bcrypt.hashpw(b'password123', bcrypt.gensalt()).decode()
    create_user('interviewer@company.com', interviewer_hash, 
                'interviewer', 'Default Interviewer')

if __name__ == '__main__':
    init_database()
    seed_default_users()
```

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
| `create_assessment(candidate_id, job_id)` | `int` | Create in-progress assessment |
| `get_assessment_by_id(assessment_id)` | `dict \| None` | Fetch assessment record |
| `get_assessment_by_candidate_id(candidate_id)` | `dict \| None` | Most recent assessment for a candidate |
| `update_assessment_scores(assessment_id, technical_score, psychometric_score, decision, rationale)` | — | Finalize scores and mark completed |

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
| `record_proctoring_violation(assessment_id, violation_type, description, severity, screenshot_url)` | `int` | Record violation, return violation ID |
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

- [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) - System architecture
- [API_DOCS.md](API_DOCS.md) - API reference
- [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) - Database structure

---

*Last Updated: May 2026*
