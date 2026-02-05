# Cygnusa Elite Hire

**Cygnusa Elite Hire** is an advanced, AI-powered recruitment and proctoring platform designed to streamline the hiring process for specialized roles. It combines resume analysis, automated skill assessments, and intelligent proctoring into a unified solution.

## 🚀 Features

### 🤖 AI-Powered Recruitment
- **Resume Parsing & Scoring**: Automatically extracts skills and experience from resumes to rank candidates against job descriptions using AI.
- **Automated Question Generation**: Dynamically generates technical interview questions based on the candidate's specific skill set and experience level.

### 👁️ Intelligent Proctoring
- **Real-time Monitoring**: Tracks candidate behavior during assessments including gaze detection and tab switching.
- **Fullscreen Enforcement**: Ensures assessment integrity by mandating fullscreen mode.
- **Automated Flagging**: Detects and logs suspicious activities for reviewer attention.

### 👥 Role-Based Portals
- **Admin Dashboard**: Comprehensive system overview, user management, and global analytics.
- **Interviewer Dashboard**: Manage candidates, schedule interviews, and review assessment scores.
- **Proctor Dashboard**: Monitor live assessments and review flagged incidents.
- **Candidate Portal**: Seamless experience for applicants to apply, take tests, and track status.

## 🛠️ Tech Stack

- **Frontend**: React.js, Vite, Tailwind CSS
- **Backend**: Python, Flask, Werkzeug
- **Database**: PostgreSQL (via Supabase)
- **Authentication**: JWT (JSON Web Tokens), Role-Based Access Control (RBAC)
- **AI Integration**: OpenAI API (GPT-4/3.5)
- **Infrastructure**: Supabase (Auth, Storage, Database)

## 📂 Documentation

Detailed documentation is available in the `docs/` directory:

- [**System Architecture**](docs/ARCHITECTURE.md) - High-level design and data flow.
- [**Setup & Installation**](docs/SETUP.md) - Instructions for local development setup.
- [**API Reference**](docs/API.md) - Backend API endpoints and usage.
- [**Database Schema**](docs/DATABASE.md) - Database structure and relationships.

## ⚡ Quick Start

### Prerequisites
- Node.js (v16+)
- Python (v3.9+)
- PostgreSQL / Supabase Project

### 1. Clone & Install
```bash
git clone <repo-url>
cd cygnusa-elite-hire
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

### 4. Configuration
Create a `.env` file in `backend/` consistent with `docs/SETUP.md`.

### 5. Run
**Backend**:
```bash
cd backend
python app.py
```
**Frontend**:
```bash
cd frontend
npm run dev
```

## 📄 License
Private and Confidential. © 2026 Cygnusa.
