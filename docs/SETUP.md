# Setup & Installation Guide

This guide details how to set up the Cygnusa Elite Hire development environment.

## 📋 Prerequisites

- **Python** 3.9 or higher
- **Node.js** 16.0 or higher
- **PostgreSQL** database (Local or Supabase)

## 🔧 Backend Setup

1.  **Navigate to Backend Directory**
    ```bash
    cd backend
    ```

2.  **Create Virtual Environment**
    ```bash
    python -m venv venv
    
    # Windows
    venv\Scripts\activate
    
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Configuration**
    Create a `.env` file in the `backend/` directory:
    
    ```properties
    # Database Configuration
    DATABASE_URL=postgresql://postgres:password@db.supabase.co:5432/postgres
    
    # Security
    SECRET_KEY=your_super_secret_flask_key
    JWT_SECRET_KEY=your_jwt_signing_key
    
    # Supabase (Optional if using direct DB connection)
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your_anon_key
    
    # OpenAI (For AI Features)
    OPENAI_API_KEY=sk-your-openai-key
    
    # Email Service (SMTP)
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USERNAME=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    ```

5.  **Database Initialization**
    Import the schema directly into your PostgreSQL database using the provided SQL file:
    
    ```bash
    # Using psql CLI
    psql "$DATABASE_URL" -f ../database/schema.sql
    ```

6.  **Run the Server**
    ```bash
    python app.py
    ```
    The API will be available at `http://localhost:5000`.

## 🎨 Frontend Setup

1.  **Navigate to Frontend Directory**
    ```bash
    cd frontend
    ```

2.  **Install Dependencies**
    ```bash
    npm install
    ```

3.  **Environment Configuration**
    Create a `.env` file in `frontend/` (if using Vite, use `.env.local`):
    
    ```properties
    VITE_API_BASE_URL=http://localhost:5000
    ```

4.  **Run Development Server**
    ```bash
    npm run dev
    ```
    The UI will be available at `http://localhost:5173`.

## ☁️ Deployment

The project is configured for cloud deployment (e.g., Railway, Render, Heroku).

- **Backend**: Uses `gunicorn` (via `Procfile`) or `python app.py` (via `nixpacks.toml`).
- **Frontend**: Standard Vite build process.

**Build Command**:
```bash
npm run build
```
The output will be in `frontend/dist`.
