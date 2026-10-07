"""
HireSense demo data seeder.

Fills a dedicated demo database with demo staff accounts, open roles, and
candidates at every hiring stage. It drives the real API through Flask's test
client, so resume parsing, scoring, assessments, and decisions all run through
the application's own code paths.

Usage (repository root, backend environment configured as for the server):
    python database/seed_demo.py           # seed an empty demo database
    python database/seed_demo.py --reset   # delete existing demo data, then seed

On a server, run it as the backend service user so resume files land in
UPLOAD_FOLDER. Pair the deployment with DEMO_MODE=true.
"""

import argparse
import io
import os
import secrets
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))
# Seeding sends invitations and decisions; record them, never email anyone.
os.environ["DEMO_MODE"] = "true"

from docx import Document  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

from app import app  # noqa: E402
from assessment_db import get_assessment_questions  # noqa: E402
from db_config import db_connection  # noqa: E402
from demo_mode import DEMO_ACCOUNTS  # noqa: E402
from interviewee_answers import _resolve_correct_answer  # noqa: E402

DEMO_EMAIL_SUFFIX = "@hiresense.demo"
# Deleted children-first so foreign keys never block the reset.
DEMO_TABLES = (
    "audit_log", "email_logs", "custom_question_bank", "candidate_job_matches",
    "proctoring_violations", "mcq_responses", "coding_submissions",
    "psychometric_responses", "assessments", "scheduled_assessments",
    "candidates", "job_descriptions", "users",
)

STAFF = {
    "admin": "Asha Verma",
    "interviewer": "Dev Malhotra",
    "proctor": "Ira Sen",
}

JOBS = [
    {
        "title": "Senior Backend Engineer", "sector": "Engineering", "department": "Platform",
        "description": "Design and own the Flask and PostgreSQL services behind our hiring workflows.",
        "required_skills": ["Python", "Flask", "PostgreSQL", "REST APIs"],
        "preferred_skills": ["Docker", "Redis"],
        "min_experience": 4, "max_experience": 9, "experience_level": "senior",
        "work_mode": "Remote", "salary_range": "INR 28-40 LPA",
    },
    {
        "title": "Frontend Engineer", "sector": "Engineering", "department": "Product Engineering",
        "description": "Build accessible React interfaces used by recruiters every day.",
        "required_skills": ["React", "JavaScript", "TypeScript", "Tailwind CSS"],
        "preferred_skills": ["Vite", "Testing Library"],
        "min_experience": 2, "max_experience": 6, "experience_level": "mid",
        "work_mode": "Hybrid", "salary_range": "INR 16-26 LPA",
    },
    {
        "title": "Data Analyst", "sector": "Data Science", "department": "Analytics",
        "description": "Turn hiring-funnel data into dashboards and decisions.",
        "required_skills": ["SQL", "Python", "Tableau", "Statistics"],
        "preferred_skills": ["Power BI"],
        "min_experience": 0, "max_experience": 3, "experience_level": "junior",
        "work_mode": "On-Site", "salary_range": "INR 8-12 LPA",
    },
    {
        "title": "Product Designer", "sector": "Design", "department": "Design",
        "description": "Shape the end-to-end candidate and recruiter experience.",
        "required_skills": ["Figma", "User Research", "Prototyping", "Design Systems"],
        "preferred_skills": ["Accessibility"],
        "min_experience": 2, "max_experience": 7, "experience_level": "mid",
        "work_mode": "Hybrid", "salary_range": "INR 18-28 LPA",
    },
    {
        "title": "Sales Development Representative", "sector": "Sales", "department": "Growth",
        "description": "Open conversations with talent teams evaluating HireSense.",
        "required_skills": ["Salesforce", "Lead Generation", "Communication", "CRM"],
        "preferred_skills": ["Cold Calling"],
        "min_experience": 0, "max_experience": 3, "experience_level": "junior",
        "work_mode": "On-Site", "salary_range": "INR 6-9 LPA + incentives",
    },
]

# stage: applied | screen_reject | upcoming | completed | hired | no_hire
# accuracy: share of assessment answers the candidate gets right.
CANDIDATES = [
    ("Ananya Iyer", 0, ["Python", "Flask", "PostgreSQL", "REST APIs", "Docker", "Redis"], 6,
     "B.Tech Computer Science, IIT Madras", "hired", 0.9, []),
    ("Rohan Mehta", 0, ["Python", "Django", "PostgreSQL", "Docker"], 5,
     "B.E. Information Technology, Pune University", "completed", 0.7,
     [("tab_switch", "medium", "Switched to another browser tab"),
      ("copy_paste", "low", "Pasted text into an answer field")]),
    ("Kabir Singh", 0, ["Java", "Spring Boot", "MySQL"], 3,
     "B.Tech Electronics, VIT Vellore", "screen_reject", 0, []),
    ("Sara Thomas", 0, ["Python", "Flask", "REST APIs"], 4,
     "M.Sc Computer Science, Christ University", "applied", 0, []),
    ("Meera Nair", 1, ["React", "TypeScript", "JavaScript", "Tailwind CSS", "Vite"], 3,
     "B.Tech Computer Science, NIT Calicut", "completed", 0.85, []),
    ("Arjun Reddy", 1, ["React", "JavaScript", "CSS"], 2,
     "Bachelor of Computer Applications, Osmania University", "upcoming", 0, []),
    ("Liam Fernandes", 1, ["Angular", "JavaScript", "HTML"], 1,
     "B.Sc Information Technology, Mumbai University", "applied", 0, []),
    ("Priya Das", 2, ["SQL", "Python", "Tableau", "Statistics", "Excel"], 1,
     "B.Sc Statistics, Presidency University", "no_hire", 0.35,
     [("tab_switch", "medium", "Switched to another browser tab"),
      ("tab_switch", "medium", "Switched to another browser tab"),
      ("multiple_faces", "high", "A second face was detected on camera"),
      ("no_face", "medium", "No face detected for 12 seconds")]),
    ("Vikram Joshi", 2, ["SQL", "Excel", "Power BI"], 2,
     "MBA Business Analytics, NMIMS", "applied", 0, []),
    ("Zoya Khan", 3, ["Figma", "Prototyping", "User Research", "Design Systems"], 4,
     "Bachelor of Design, NID Ahmedabad", "upcoming", 0, []),
    ("Neha Kulkarni", 3, ["Figma", "Illustrator"], 1,
     "Bachelor of Fine Arts, JJ School of Art", "applied", 0, []),
    ("Aditya Rao", 4, ["CRM", "Communication", "Lead Generation"], 1,
     "Bachelor of Commerce, Delhi University", "applied", 0, []),
]


class Api:
    def __init__(self, client):
        self.client = client

    def call(self, method, path, token=None, expect=(200, 201), headers=None, **kwargs):
        headers = dict(headers or {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = getattr(self.client, method)(path, headers=headers, **kwargs)
        if response.status_code not in expect:
            raise SystemExit(f"{method.upper()} {path} -> {response.status_code}: {response.get_data(as_text=True)[:300]}")
        return (response.get_json(silent=True) or {}).get("data")

    def demo_token(self, role):
        return self.call("post", "/api/auth/demo-login", json={"role": role})["access_token"]


def reset():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email NOT LIKE %s", (f"%{DEMO_EMAIL_SUFFIX}",))
        if cursor.fetchone():
            raise SystemExit("Refusing to reset: this database has non-demo staff accounts.")
        cursor.execute("SELECT resume_path FROM candidates")
        resume_paths = [row[0] for row in cursor.fetchall()]
        for table in DEMO_TABLES:
            cursor.execute(f"DELETE FROM {table}")  # noqa: S608 - fixed table names
        conn.commit()
    for path in resume_paths:
        Path(path).unlink(missing_ok=True)
    print(f"Reset: removed demo data and {len(resume_paths)} resume files.")


def create_staff():
    with db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users LIMIT 1")
        if cursor.fetchone():
            raise SystemExit("The database already has staff accounts. Use --reset on a demo database.")
        for role, email in DEMO_ACCOUNTS.items():
            # Demo accounts sign in through /api/auth/demo-login; nobody knows this password.
            cursor.execute(
                "INSERT INTO users (email, password_hash, role, name) VALUES (%s, %s, %s, %s)",
                (email, generate_password_hash(secrets.token_urlsafe(32)), role, STAFF[role]),
            )
        conn.commit()


def resume_docx(name, email, skills, years, education, job_title):
    document = Document()
    for line in (
        name,
        f"{email} | +91 98{secrets.randbelow(10**8):08d}",
        f"Applying for {job_title}",
        f"Skills: {', '.join(skills)}",
        f"Experience: {years} years of professional experience",
        education,
    ):
        document.add_paragraph(line)
    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


def take_assessment(api, access_token, accuracy, violations):
    headers = {"X-Assessment-Token": access_token}
    assessment_id = api.call("post", "/api/interviewee/assessment/start", headers=headers)["assessment_id"]
    questions = get_assessment_questions(assessment_id)
    letters = ("A", "B", "C", "D")

    mcqs = questions.get("mcq_questions", [])
    for index, question in enumerate(mcqs):
        correct = _resolve_correct_answer(int(question["id"]), mcqs)
        right = index < round(accuracy * len(mcqs))
        answer = correct if right else letters[(letters.index(correct) + 1) % 4]
        api.call("post", f"/api/interviewee/assessment/{assessment_id}/submit-answer", headers=headers,
                 json={"type": "mcq", "questionId": question["id"], "answer": answer, "timeSpent": 40 + index * 7})

    scenarios = questions.get("psychometric_scenarios", [])
    for index, scenario in enumerate(scenarios):
        optimal = int(scenario["optimal_choice"])
        right = index < round(accuracy * len(scenarios))
        choice = optimal if right else (optimal + 1) % len(scenario["options"])
        api.call("post", f"/api/interviewee/assessment/{assessment_id}/submit-answer", headers=headers,
                 json={"type": "psychometric", "questionId": scenario["id"], "selectedOption": choice})

    for violation_type, severity, description in violations:
        api.call("post", f"/api/interviewee/assessment/{assessment_id}/violation", headers=headers,
                 json={"violation_type": violation_type, "severity": severity, "description": description})

    api.call("post", f"/api/interviewee/assessment/{assessment_id}/complete", headers=headers)
    return assessment_id


def seed():
    for limiter in app.extensions.get("limiter", ()):
        limiter.enabled = False  # seeding is a burst of legitimate requests
    api = Api(app.test_client())
    create_staff()
    admin, interviewer, proctor = (api.demo_token(role) for role in ("admin", "interviewer", "proctor"))

    sectors = {sector["name"]: sector["id"] for sector in api.call("get", "/api/jobs/sectors")}
    job_ids = []
    for job in JOBS:
        payload = {key: value for key, value in job.items() if key != "sector"}
        payload["sector_id"] = sectors.get(job["sector"])
        job_ids.append(api.call("post", "/api/jobs/postings", token=admin, json=payload)["id"])

    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=5, minute=0, second=0, microsecond=0)  # 10:30 IST
    for index, (name, job_index, skills, years, education, stage, accuracy, violations) in enumerate(CANDIDATES):
        email = f"{name.lower().replace(' ', '.')}@example.com"
        resume = resume_docx(name, email, skills, years, education, JOBS[job_index]["title"])
        candidate_id = api.call("post", "/api/resume/upload", data={
            "file": (resume, f"{name.replace(' ', '_')}_Resume.docx"),
            "job_id": str(job_ids[job_index]), "name": name, "email": email,
        }, content_type="multipart/form-data")["candidate_id"]

        if stage == "screen_reject":
            api.call("post", f"/api/interviewer/candidates/{candidate_id}/reject", token=interviewer,
                     json={"reason": "Core backend stack does not match the role requirements."})
        elif stage == "upcoming":
            schedule = api.call("post", f"/api/interviewer/candidates/{candidate_id}/schedule", token=interviewer,
                                json={"scheduled_time": (tomorrow + timedelta(hours=index % 3)).isoformat(),
                                      "is_technical_role": False})
            api.call("post", "/api/proctor/assign-assessment", token=proctor,
                     json={"scheduled_assessment_id": schedule["scheduled_assessment_id"]})
        elif stage in {"completed", "hired", "no_hire"}:
            schedule = api.call("post", f"/api/interviewer/candidates/{candidate_id}/schedule", token=interviewer,
                                json={"scheduled_time": (now + timedelta(minutes=1)).isoformat(),
                                      "is_technical_role": False})
            api.call("post", "/api/proctor/assign-assessment", token=proctor,
                     json={"scheduled_assessment_id": schedule["scheduled_assessment_id"]})
            access_token = schedule["assessment_link"].split("#token=", 1)[1]
            assessment_id = take_assessment(api, access_token, accuracy, violations)
            if stage != "completed":
                api.call("post", f"/api/interviewer/assessments/{assessment_id}/final-decision", token=interviewer,
                         json={"decision": "hire" if stage == "hired" else "no-hire",
                               "rationale": ("Strong system design and clear communication." if stage == "hired"
                                             else "Assessment results and integrity flags do not support an offer.")})
        print(f"  {stage:<13} {name}")

    print(f"\nSeeded {len(JOBS)} roles and {len(CANDIDATES)} candidates.")
    print("Open /login on a DEMO_MODE=true deployment and pick a role.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete existing demo data before seeding")
    if parser.parse_args().reset:
        reset()
    seed()
