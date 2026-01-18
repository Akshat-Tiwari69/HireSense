# 🚀 CYGNUSA Elite-Hire - AI-Enabled HR Evaluation System

> **Team:** Akshat (Backend) | Shaivi (Frontend) | Prashanth (Database)  
> **Hackathon:** SRM Innovation Hackathon - Edition 1  

---

## 📊 Project Progress Overview

### **Overall Completion:** 🟢⬜⬜⬜⬜⬜⬜⬜⬜⬜ 10%

| Phase | Status | Owner | Completion |
|-------|--------|-------|------------|
| 🏗️ Infrastructure | 🟡 In Progress | Prashanth | 33% |
| 📄 Resume System | 🟡 In Progress | Akshat | 15% |
| 📝 Assessment Engine | ⬜ Not Started | Akshat + Shaivi | 0% |
| 👁️ Proctoring | ⬜ Not Started | Shaivi + Akshat | 0% |
| 🤖 AI Decision Engine | ⬜ Not Started | Akshat | 0% |
| 🎨 UI/UX | ⬜ Not Started | Shaivi | 0% |
| 🧪 Integration | ⬜ Not Started | All | 0% |

**Legend:** 🟢 Done | 🟡 In Progress | 🔴 Blocked | ⬜ Not Started

---

## 🗓️ 3-Day Battle Plan

### **Day 1:** Foundation (Database + Resume + Basic UI)
### **Day 2:** Core Features (Assessment + Proctoring + AI)
### **Day 3:** Polish (Integration + Testing + Demo Prep)

---

# 📋 TASK BREAKDOWN

---

## 💾 PRASHANTH - DATABASE ARCHITECT

### **PHASE 1: Database Foundation** 🟡

#### ✅ Task 1.1: Database Connection (COMPLETED)
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get database up and running

**What you need:**
- [x] Choose: SQLite (easier) or PostgreSQL (production-ready)
- [x] Create `backend/db_config.py`
- [x] Write a `get_connection()` function
- [x] Write a `test_connection()` function that prints success/failure

**Hints:**
- SQLite: `import sqlite3`, then `sqlite3.connect('filename.db')`
- PostgreSQL: `import psycopg2`, needs connection params
- Test by running the file directly: `python db_config.py`

**Success criteria:** Running the file prints "Database connected!" ✅

**Commit message:** `db: setup database connection`

**Status:** ✅ COMPLETED - Database connection working!

---

#### ✅ Task 1.2: Create Database Tables
**Time:** 1-2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Design and create all tables for the system

**Tables you need:**
- [ ] `candidates` - Store resume data and match scores
- [ ] `job_descriptions` - Store JD requirements  
- [ ] `assessments` - Track each candidate's test
- [ ] `mcq_responses` - Store MCQ answers
- [ ] `coding_submissions` - Store code submissions
- [ ] `proctoring_events` - Log suspicious activities
- [ ] `psychometric_responses` - Store personality test data

**Hints:**
- Create `database/schema.sql` with CREATE TABLE statements
- Think about: What fields? What data types? What's the primary key?
- Use FOREIGN KEYs to link tables (e.g., assessment links to candidate)
- Create `backend/init_db.py` that reads schema.sql and executes it
- Candidates need: id, name, email, resume_path, parsed_skills (JSON/TEXT), match_score
- Assessments need: id, candidate_id, technical_score, psychometric_score, decision, rationale

**Success criteria:** Running `python init_db.py` creates all tables without errors

**Commit message:** `db: create database schema with all tables`

---

#### ✅ Task 1.3: Database Helper Functions
**Time:** 2-3 hours | **Priority:** 🔥 CRITICAL

**Goal:** Create reusable functions for database operations

**Create `backend/db_helpers.py` with these functions:**

**Candidate functions:**
- [ ] `insert_candidate(name, email, phone, resume_path, parsed_data)` → returns candidate_id
- [ ] `get_candidate_by_id(id)` → returns candidate dict
- [ ] `get_all_candidates()` → returns list of all candidates
- [ ] `update_candidate_shortlist(id, status, score)` → updates match score

**Assessment functions:**
- [ ] `create_assessment(candidate_id)` → returns assessment_id
- [ ] `update_assessment_scores(assessment_id, scores, decision, rationale)`
- [ ] `get_assessment_by_id(id)` → returns assessment details

**Response tracking:**
- [ ] `save_mcq_response(assessment_id, question_id, answer, is_correct, time)`
- [ ] `save_coding_submission(assessment_id, problem_id, code, passed, total)`
- [ ] `log_proctoring_event(assessment_id, event_type, severity, details)`
- [ ] `save_psychometric_response(assessment_id, trait, score)`

**Score calculation:**
- [ ] `get_mcq_score(assessment_id)` → returns percentage
- [ ] `get_coding_score(assessment_id)` → returns percentage  
- [ ] `get_psychometric_scores(assessment_id)` → returns trait scores

**Hints:**
- Use `cursor.execute()` for SQL queries
- Use `cursor.lastrowid` to get ID of inserted row
- Use `cursor.fetchone()` for single result, `cursor.fetchall()` for multiple
- Always `conn.commit()` after INSERT/UPDATE
- Store lists/dicts as JSON strings: `json.dumps()` and `json.loads()`
- Add try-except blocks for error handling

**Success criteria:** Create a test file that inserts a candidate, creates an assessment, and retrieves it

**Commit message:** `db: add database helper functions`

---

### 📌 PRASHANTH'S DELIVERABLES CHECKLIST
- [x] Database connection working ✅
- [ ] All 7 tables created
- [ ] Helper functions written and tested
- [ ] Can insert and retrieve data successfully
- [ ] Pull Request created to merge into `dev`
- [ ] Akshat confirms he can use your functions

---

## 🔧 AKSHAT - BACKEND ARCHITECT

### **PHASE 1: API Foundation** 🟡

#### ✅ Task 2.1: Flask API Setup
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get Flask server running with basic endpoint

**What to do:**
- [x] Update `backend/requirements.txt` with: flask, flask-cors, PyPDF2, python-docx
- [x] Run `pip install -r requirements.txt`
- [x] Create basic Flask app in `app.py`
- [x] Enable CORS (so frontend can call your APIs)
- [x] Create `/api/health` endpoint that returns `{"status": "ok"}`
- [x] Create `uploads/` folder for resume storage

**Hints:**
- Import Flask and CORS
- `app = Flask(__name__)` and `CORS(app)`
- Use `@app.route()` decorator for endpoints
- Run with `app.run(debug=True, port=5000)`
- Test by visiting `http://localhost:5000/api/health` in browser

**Success criteria:** Browser shows your JSON response

**Commit message:** `feat: setup Flask API with health check`

---

#### ✅ Task 2.2: Resume Upload Endpoint
**Time:** 1 hour | **Priority:** 🔥 CRITICAL

**Goal:** Accept resume files from frontend

**Create endpoint: `POST /api/resume/upload`**

**What it should do:**
- [ ] Accept file upload (PDF/DOCX only)
- [ ] Accept form data: name, email, phone
- [ ] Validate: file exists, correct type, name and email provided
- [ ] Generate unique filename (hint: use `uuid`)
- [ ] Save file to `uploads/` folder
- [ ] Return success response with file path

**Hints:**
- Use `request.files['file']` to get uploaded file
- Use `request.form.get('name')` for form data
- Check file extension: `filename.endswith('.pdf')`
- Save with: `file.save(filepath)`
- Use `werkzeug.utils.secure_filename()` for security
- Return JSON with status and file path

**Success criteria:** Can upload a file using Postman/curl and see it in uploads folder

**Commit message:** `feat: add resume upload endpoint`

---

#### ✅ Task 2.3: Resume Parsing Engine
**Time:** 3-4 hours | **Priority:** 🔥 CRITICAL

**Goal:** Extract meaningful data from resumes

**Create `backend/resume_parser.py` with:**

**Text extraction:**
- [ ] `extract_text_from_pdf(filepath)` → returns text string
- [ ] `extract_text_from_docx(filepath)` → returns text string

**Data extraction:**
- [ ] `extract_skills(text)` → returns list of skills found
- [ ] `extract_experience(text)` → returns years as integer
- [ ] `extract_education(text)` → returns degree string

**Matching logic:**
- [ ] `calculate_match_score(candidate_skills, candidate_exp, jd_skills, jd_min_exp)` → returns score 0-100
- [ ] `get_shortlist_status(score)` → returns "High Match" / "Potential" / "Reject"

**Main function:**
- [ ] `parse_resume(filepath, job_description)` → returns dict with all parsed data

**Hints:**
- For PDF: Use `PyPDF2.PdfReader`, loop through pages, extract text
- For DOCX: Use `python-docx`, loop through paragraphs
- For skills: Create a list of common skills, search for them in text (case-insensitive)
- For experience: Use regex to find patterns like "X years of experience"
- For education: Search for keywords like "B.Tech", "M.Tech", "Bachelor", "Master"
- Match score: Weight skills (70%) + experience (30%)
- High Match: 70+, Potential: 40-69, Reject: <40

**Integration:**
- [ ] Update upload endpoint to call `parse_resume()` after saving file
- [ ] Use Prashanth's `insert_candidate()` to save parsed data to database
- [ ] Return parsed data in API response

**Success criteria:** Upload resume → Get JSON with skills, experience, education, match score

**Commit message:** `feat: add resume parsing and matching logic`

---

### **PHASE 2: Assessment Engine** ⬜

#### ✅ Task 2.4: Assessment APIs
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Create these endpoints:**

**Start assessment:**
- [ ] `POST /api/assessment/start` - Takes candidate_id, creates assessment, returns questions

**Submit answers:**
- [ ] `POST /api/assessment/mcq/submit` - Save MCQ answer, return if correct
- [ ] `POST /api/assessment/code/submit` - Run code, return test results
- [ ] `POST /api/assessment/psychometric/submit` - Save slider/scenario responses

**Complete assessment:**
- [ ] `POST /api/assessment/complete` - Calculate final scores, return decision

**Hints:**
- Use Prashanth's helper functions to save/retrieve data
- For code execution: Research `subprocess` or Docker (be careful with security!)
- Store MCQ questions in a Python list/dict (or separate JSON file)
- Calculate technical score from MCQ + coding
- Calculate psychometric score from trait averages

**Commit message:** `feat: add assessment submission endpoints`

---

#### ✅ Task 2.5: Code Execution Sandbox
**Time:** 2-3 hours | **Priority:** 🟡 MEDIUM

**Goal:** Safely run candidate's code and test it

**Create `backend/grading_engine.py`:**

**What it needs:**
- [ ] `execute_code(code, language, test_cases)` → returns pass/fail for each test
- [ ] Timeout protection (5 seconds max)
- [ ] Test against hidden test cases
- [ ] Return execution time

**Hints:**
- Use `subprocess.run()` with timeout
- For Python: Write code to temp file, execute with `python tempfile.py`
- Capture stdout and compare with expected output
- Handle errors gracefully (syntax errors, runtime errors)
- **Security warning:** Real sandbox needs Docker or isolated environment!

**Success criteria:** Submit code that solves a problem → Get test case results

**Commit message:** `feat: add code execution and grading`

---

#### ✅ Task 2.6: AI Decision Engine  
**Time:** 2 hours | **Priority:** 🔥 HIGH

**Goal:** Generate hire/no-hire decision with explanation

**Create `backend/decision_engine.py`:**

**What it needs:**
- [ ] `generate_decision(assessment_data)` → returns decision + rationale

**The function should:**
- [ ] Take technical score, psychometric scores, proctoring events
- [ ] Use Claude API or OpenAI to generate rationale
- [ ] Return "Hire" / "No-Hire" / "Maybe" with detailed explanation
- [ ] Include competency map (strengths/weaknesses)

**Hints:**
- Call Anthropic API: `https://api.anthropic.com/v1/messages`
- Prompt should include all scores and ask for hiring recommendation
- Parse AI response to extract decision and reasoning
- Consider proctoring flags in the decision
- Return structured JSON with decision, rationale, and competency breakdown

**Success criteria:** Given assessment scores → Get AI-generated hiring decision with rationale

**Commit message:** `feat: add AI-powered decision engine`

---

#### ✅ Task 2.7: Proctoring Event Handler
**Time:** 1 hour | **Priority:** 🟡 MEDIUM

**Goal:** Accept and log proctoring events from frontend

**Create endpoint: `POST /api/proctoring/log`**

**What it should do:**
- [ ] Accept assessment_id, event_type, severity, details
- [ ] Validate the data
- [ ] Use Prashanth's `log_proctoring_event()` to save
- [ ] Return success

**Event types to handle:**
- Multiple faces detected
- No face detected  
- Tab switched
- Copy-paste detected
- Keyboard shortcuts used

**Hints:**
- Simple endpoint, just save to database
- Frontend will call this whenever something suspicious happens
- Severity: "low", "medium", "high"

**Commit message:** `feat: add proctoring event logging`

---

### 📌 AKSHAT'S DELIVERABLES CHECKLIST
- [x] Flask server running
- [ ] Resume upload working
- [ ] Resume parsing extracting data correctly
- [ ] Assessment APIs created
- [ ] Code execution working (even if basic)
- [ ] AI decision engine generating rationale
- [ ] Proctoring endpoint logging events
- [ ] All endpoints tested with Postman
- [ ] Pull Request to merge into `dev`

---

## 🎨 SHAIVI - FRONTEND ARCHITECT

### **PHASE 1: UI Foundation** ⬜

#### ✅ Task 3.1: React Project Setup
**Time:** 30 mins | **Priority:** 🔥 CRITICAL

**Goal:** Get React app running

**What to do:**
- [ ] `cd frontend`
- [ ] Initialize React app: `npx create-react-app .` (or Vite for faster builds)
- [ ] Install dependencies: axios, react-router-dom, tailwindcss
- [ ] Setup Tailwind CSS
- [ ] Create folder structure: components/, pages/, services/
- [ ] Create basic routing (React Router)

**Routes you need:**
- `/` - Home/Upload page
- `/assessment/:candidateId` - Assessment interface
- `/dashboard` - Recruiter dashboard

**Success criteria:** React app runs on `localhost:3000`

**Commit message:** `feat: setup React project with routing`

---

#### ✅ Task 3.2: Resume Upload Page
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Goal:** Let candidates upload their resume

**Create `pages/UploadPage.jsx`:**

**What it needs:**
- [ ] File upload input (accept only PDF/DOCX)
- [ ] Form fields: Name, Email, Phone
- [ ] Submit button
- [ ] Loading state while uploading
- [ ] Show success message with match score after upload
- [ ] Show error message if upload fails

**Hints:**
- Use `<input type="file" accept=".pdf,.docx" />`
- Use FormData to send file + form data
- Use axios to POST to `/api/resume/upload`
- Show parsed data (skills, experience, match score) after successful upload
- Add validation (check if file selected, email format, etc.)

**Success criteria:** Upload resume → See parsed results on screen

**Commit message:** `feat: add resume upload page`

---

#### ✅ Task 3.3: Assessment Interface
**Time:** 4-5 hours | **Priority:** 🔥 CRITICAL

**Goal:** Complete assessment UI where candidates take tests

**Create `pages/AssessmentPage.jsx` with sections:**

**MCQ Section:**
- [ ] Display question with 4 options (A, B, C, D)
- [ ] Radio buttons to select answer
- [ ] Timer showing time spent
- [ ] Submit button
- [ ] Show next question after submit

**Coding Section:**
- [ ] Code editor (use Monaco Editor or simple textarea)
- [ ] Language selector (Python/JavaScript/Java)
- [ ] Problem description
- [ ] Run code button
- [ ] Submit button
- [ ] Show test case results after submission

**Text Response Section:**
- [ ] Question display
- [ ] Large text area for answer
- [ ] Word count
- [ ] Submit button

**Psychometric Section:**
- [ ] Scenario description
- [ ] Slider inputs (1-10) for traits like leadership, resilience
- [ ] Text area for scenario response
- [ ] Submit button

**Progress Indicator:**
- [ ] Show which section candidate is on
- [ ] Show number of questions completed
- [ ] Navigation between sections

**Hints:**
- Use state to track current question, current section
- Create separate components: MCQQuestion, CodeEditor, TextResponse, Slider
- Call respective APIs when submitting each answer
- Store assessment_id in state after starting assessment
- Use axios to communicate with backend

**Success criteria:** Can complete full assessment flow from MCQ to psychometric

**Commit message:** `feat: add complete assessment interface`

---

#### ✅ Task 3.4: Proctoring Integration
**Time:** 2-3 hours | **Priority:** 🟡 MEDIUM

**Goal:** Monitor candidate during assessment

**Add to AssessmentPage:**

**Webcam monitoring:**
- [ ] Request camera permission
- [ ] Show small webcam feed in corner
- [ ] Detect if no face (call proctoring API)
- [ ] Detect if multiple faces (call proctoring API)

**Tab switching detection:**
- [ ] Listen for `visibilitychange` event
- [ ] Log tab switch to backend

**Copy-paste detection:**
- [ ] Disable right-click in code editor
- [ ] Listen for Ctrl+C, Ctrl+V
- [ ] Log copy-paste attempts

**Warning banner:**
- [ ] Show warning if suspicious activity detected
- [ ] Count total violations

**Hints:**
- Use `navigator.mediaDevices.getUserMedia()` for webcam
- Use `document.addEventListener('visibilitychange')` for tab detection
- Use face detection library (e.g., face-api.js) or keep it simple
- Call `/api/proctoring/log` whenever event detected
- Store events locally and batch-send to reduce API calls

**Success criteria:** Switching tabs logs an event to backend

**Commit message:** `feat: add proctoring system`

---

#### ✅ Task 3.5: Recruiter Dashboard
**Time:** 3 hours | **Priority:** 🔥 HIGH

**Goal:** Show all candidates and their results

**Create `pages/DashboardPage.jsx`:**

**What it should show:**
- [ ] Table/list of all candidates
- [ ] Each row: Name, Email, Shortlist Status, Match Score
- [ ] Filter by status (High Match / Potential / Reject)
- [ ] Sort by match score
- [ ] Click candidate to see detailed view

**Detailed view modal/page:**
- [ ] Candidate info
- [ ] Technical score, Psychometric score, Overall score
- [ ] Hiring decision (Hire/No-Hire)
- [ ] AI-generated rationale
- [ ] Competency map (visual chart of strengths/weaknesses)
- [ ] Proctoring events timeline
- [ ] View submitted code

**Hints:**
- Call `GET /api/candidates/all` to get candidate list
- Use table component or map through list
- Use recharts or chart.js for competency visualization
- Make it look professional - this is what judges will see!

**Success criteria:** Dashboard shows all candidates with scores and decisions

**Commit message:** `feat: add recruiter dashboard`

---

#### ✅ Task 3.6: UI/UX Polish
**Time:** 2 hours | **Priority:** 🟡 MEDIUM

**Goal:** Make it look professional

**What to polish:**
- [ ] Consistent color scheme (use Tailwind)
- [ ] Loading spinners everywhere data is being fetched
- [ ] Error messages are user-friendly
- [ ] Smooth transitions between sections
- [ ] Responsive design (looks good on laptop)
- [ ] Add logo/branding
- [ ] Clean typography

**Hints:**
- Create reusable components: Button, Card, Modal, Loading
- Use Tailwind's utility classes consistently
- Add hover effects on buttons
- Use icons (lucide-react or heroicons)
- Make assessment feel like a real test platform

**Success criteria:** UI looks polished and professional

**Commit message:** `ui: polish design and user experience`

---

### 📌 SHAIVI'S DELIVERABLES CHECKLIST
- [ ] React app running
- [ ] Resume upload page working
- [ ] Complete assessment interface (MCQ, Code, Text, Psychometric)
- [ ] Proctoring detecting tab switches
- [ ] Recruiter dashboard showing candidates
- [ ] All pages styled and responsive
- [ ] All API calls working (test with Akshat's backend)
- [ ] Pull Request to merge into `dev`

---

## 🧪 INTEGRATION & TESTING (ALL THREE)

### **Final Integration Tasks** ⬜

#### ✅ Everyone: End-to-End Testing
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Test the complete flow:**
- [ ] Upload resume → See parsed data and match score ✅
- [ ] Start assessment → Complete all sections ✅
- [ ] Submit answers → Saved to database ✅
- [ ] Complete assessment → Get AI decision ✅
- [ ] View in dashboard → See all data correctly ✅
- [ ] Proctoring events → Logged and visible ✅

**Bug fixing:**
- [ ] Fix any errors that come up
- [ ] Handle edge cases
- [ ] Add error messages

**Commit message:** `fix: resolve integration bugs`

---

#### ✅ Everyone: Demo Preparation
**Time:** 2 hours | **Priority:** 🔥 CRITICAL

**Prepare for judges:**
- [ ] Create sample resumes (3-4 test candidates)
- [ ] Prepare demo script (what to show in what order)
- [ ] Practice the demo (5-7 minutes)
- [ ] Prepare to answer questions about architecture
- [ ] Each person knows their part inside-out

**Demo flow:**
1. Show resume upload + parsing + scoring (30 sec)
2. Show assessment interface (1 min)
3. Show proctoring in action (30 sec)
4. Show AI decision with rationale (1 min)
5. Show recruiter dashboard (1 min)
6. Explain architecture briefly (1 min)

---

## 📊 JUDGING CRITERIA MAPPING

Remember what judges care about:

| Criteria | Weight | Who Owns This | How to Win |
|----------|--------|---------------|------------|
| **Architectural Depth** | 30% | All | Clean code structure, good API design, proper data flow |
| **Grading Accuracy** | 20% | Akshat + Prashanth | Resume parser catches skills correctly, code execution works |
| **Logic Transparency** | 20% | Akshat | AI rationale is detailed and makes sense |
| **Security & Anti-Cheat** | 15% | Shaivi + Akshat | Proctoring actually works, can't easily bypass |
| **User Experience** | 15% | Shaivi | Clean UI, intuitive flow, looks professional |

---

## 🎯 MINIMUM VIABLE PRODUCT (MVP)

**If time is tight, MUST HAVE these:**
- ✅ Resume upload + parsing + match score
- ✅ Basic MCQ assessment
- ✅ Simple coding assessment (even if manual grading)
- ✅ AI decision with rationale
- ✅ Dashboard showing candidates
- ✅ Some proctoring (at least tab detection)

**NICE TO HAVE (if time permits):**
- Full proctoring with webcam
- Psychometric assessment
- Advanced code execution sandbox
- Beautiful UI animations
- Detailed competency charts

---

## 💬 DAILY STANDUPS

**Every morning (5 mins):**
1. What did you finish yesterday?
2. What are you working on today?
3. Any blockers?

**Every evening (5 mins):**
1. What got done?
2. What's blocking you?
3. Plan for tomorrow

---

## 🆘 WHEN YOU'RE STUCK

**Check in this order:**
1. Google the exact error message
2. Ask your teammates (maybe they faced it)
3. Ask Claude (me!) - share the error
4. Check the original README for API contracts

**Don't waste more than 30 minutes stuck on one thing!**

---

## ✅ FINAL SUBMISSION CHECKLIST

**Before submitting:**
- [ ] All code pushed to GitHub
- [ ] README.md updated with setup instructions
- [ ] .env files not committed (check .gitignore)
- [ ] All team members can run the project locally
- [ ] Demo script prepared
- [ ] Screenshots/demo video ready (if required)
- [ ] Each person can explain their part

---

## 🏆 LET'S WIN THIS!

**Remember:**
- **Day 1:** Get the foundation solid
- **Day 2:** Build features fast
- **Day 3:** Make it shine

**Communication is key!** Use your group chat actively.

**Questions?** Come back to me anytime. I'll help with:
- Debugging errors
- Architecture decisions  
- Logic clarification
- Code review

Now go build something amazing! 💪🚀

---

**Current Status:** Setup complete, ready to code!

**Next Step:** Each person tackles their Task 1.1 and checks it off!
