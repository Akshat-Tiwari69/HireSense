# Frontend Guide

Complete documentation for the CYGNUSA Elite-Hire React frontend application.

---

## Overview

The frontend is built with modern React using Vite for fast development and builds. It uses Tailwind CSS for styling and Shadcn UI for accessible, customizable components.

### Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI Framework |
| Vite | 5.x | Build tool & dev server |
| Tailwind CSS | 3.x | Utility-first CSS |
| Shadcn UI | Latest | Component library |
| Lucide React | Latest | Icon library |
| Axios | 1.x | HTTP client |
| React Router | 6.x | Client-side routing |

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ui/                   # Shadcn UI components
│   │   │   ├── accordion.jsx
│   │   │   ├── alert.jsx
│   │   │   ├── badge.jsx
│   │   │   ├── button.jsx
│   │   │   ├── card.jsx
│   │   │   ├── dialog.jsx
│   │   │   ├── dropdown-menu.jsx
│   │   │   ├── input.jsx
│   │   │   ├── label.jsx
│   │   │   ├── progress.jsx
│   │   │   ├── select.jsx
│   │   │   ├── separator.jsx
│   │   │   ├── skeleton.jsx
│   │   │   ├── switch.jsx
│   │   │   ├── table.jsx
│   │   │   ├── tabs.jsx
│   │   │   ├── textarea.jsx
│   │   │   ├── toast.jsx
│   │   │   ├── toaster.jsx
│   │   │   └── tooltip.jsx
│   │   └── Logo.jsx              # App branding
│   │
│   ├── pages/
│   │   ├── LandingPage.jsx       # Home page
│   │   ├── LoginPage.jsx         # Authentication
│   │   ├── ApplyPage.jsx         # Candidate application
│   │   ├── InterviewerDashboardPage.jsx  # Recruiter dashboard
│   │   ├── AssessmentPage.jsx    # Full assessment interface
│   │   ├── AdminDashboardPage.jsx # Admin panel
│   │   └── ProctorDashboardPage.jsx # Proctoring monitor
│   │
│   ├── services/
│   │   └── api.js                # Axios instance + interceptors
│   │
│   ├── hooks/
│   │   └── use-toast.js          # Toast notifications hook
│   │
│   ├── lib/
│   │   └── utils.js              # Utility functions (cn)
│   │
│   ├── data/
│   │   └── mock.js               # Mock data for development
│   │
│   ├── App.jsx                   # Main app + routing
│   ├── App.css                   # App-specific styles
│   ├── index.css                 # Global styles + Tailwind
│   └── main.jsx                  # React entry point
│
├── public/                       # Static assets
├── index.html                    # HTML template
├── vite.config.js                # Vite configuration
├── tailwind.config.js            # Tailwind configuration
├── postcss.config.cjs            # PostCSS configuration
└── package.json                  # Dependencies & scripts
```

---

## Getting Started

### Installation

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Development server runs at: http://localhost:5173

### Build for Production

```bash
# Build
npm run build

# Preview production build
npm run preview
```

---

## Configuration

### Environment Variables

Create `.env` file in frontend directory:

```bash
# API Base URL (default: localhost:5000)
VITE_API_BASE_URL=http://localhost:5000

# For production
VITE_API_BASE_URL=https://api.your-domain.com
```

### Tailwind Configuration

```javascript
// tailwind.config.js
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{js,jsx}',
    './components/**/*.{js,jsx}',
    './app/**/*.{js,jsx}',
    './src/**/*.{js,jsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... more colors
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

---

## Page Components

### LandingPage.jsx

The home page with role selection for candidates and recruiters.

**Features:**
- Hero section with app branding
- Role selector cards (Candidate / Recruiter)
- Feature highlights
- Navigation to Apply or Login

**Key Components:**
```jsx
<Card onClick={() => navigate('/apply')}>
  <User className="h-8 w-8" />
  <h3>I'm a Candidate</h3>
  <p>Apply for positions and take assessments</p>
</Card>

<Card onClick={() => navigate('/login')}>
  <Briefcase className="h-8 w-8" />
  <h3>I'm a Recruiter</h3>
  <p>Manage candidates and make hiring decisions</p>
</Card>
```

---

### LoginPage.jsx

Authentication page for interviewers, admins, and proctors.

**Features:**
- Email/password form
- JWT token storage
- Role-based redirect
- Error handling with toast notifications

**Flow:**
```javascript
const handleLogin = async (e) => {
  e.preventDefault();
  const response = await api.post('/api/auth/login', { email, password });
  
  if (response.data.status === 'success') {
    localStorage.setItem('token', response.data.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.data.user));
    
    // Role-based redirect
    const role = response.data.data.user.role;
    if (role === 'admin') navigate('/admin');
    else if (role === 'proctor') navigate('/proctor');
    else navigate('/dashboard');
  }
};
```

---

### ApplyPage.jsx

Candidate application form with resume upload.

**Features:**
- Personal information form
- Drag & drop resume upload
- PDF/DOCX file validation
- AI analysis loading state
- Success confirmation

**Form Fields:**
- Full Name (required)
- Email (required)
- Phone (required)
- Resume File (PDF/DOCX, max 10MB)

**File Upload:**
```jsx
<input
  type="file"
  accept=".pdf,.doc,.docx"
  onChange={(e) => setResumeFile(e.target.files[0])}
/>
```

**API Call:**
```javascript
const handleSubmit = async () => {
  const formData = new FormData();
  formData.append('file', resumeFile);
  formData.append('name', formData.name);
  formData.append('email', formData.email);
  formData.append('phone', formData.phone);
  
  const response = await api.post('/api/resume/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};
```

---

### InterviewerDashboardPage.jsx

Recruiter dashboard for managing candidates.

**Features:**
- Candidate list with AI scores
- Filter by status
- Sort by name/date/score
- Candidate detail modal
- Schedule assessment
- Reject candidate
- View assessment results
- Make final decision

**Dashboard Stats:**
```jsx
<div className="grid grid-cols-4 gap-4">
  <StatCard title="Total" value={stats.total} icon={Users} />
  <StatCard title="Pending" value={stats.pending} icon={Clock} />
  <StatCard title="In Review" value={stats.under_review} icon={FileText} />
  <StatCard title="Hired" value={stats.hired} icon={CheckCircle} />
</div>
```

**Candidate Card:**
```jsx
<Card>
  <CardHeader>
    <h3>{candidate.name}</h3>
    <Badge variant={getStatusVariant(candidate.status)}>
      {candidate.status}
    </Badge>
  </CardHeader>
  <CardContent>
    <MatchScoreBar score={candidate.match_score} />
    <div className="pros">
      {candidate.pros?.map(pro => <p key={pro}>✓ {pro}</p>)}
    </div>
    <div className="cons">
      {candidate.cons?.map(con => <p key={con}>⚠ {con}</p>)}
    </div>
  </CardContent>
  <CardFooter>
    <Button onClick={() => scheduleAssessment(candidate.id)}>
      Schedule
    </Button>
    <Button variant="destructive" onClick={() => reject(candidate.id)}>
      Reject
    </Button>
  </CardFooter>
</Card>
```

---

### AssessmentPage.jsx

Full assessment interface for candidates.

**Features:**
- Token-based access
- Time window validation
- Proctoring (camera + face detection)
- MCQ section with timer
- Coding section with Monaco Editor
- Psychometric scenarios
- Progress tracking
- Auto-submit on completion

**Sections:**
1. **Camera Setup** - Verify webcam access
2. **MCQ Questions** - 10 questions with 30s timer each
3. **Coding Challenge** - Monaco editor with code execution
4. **Psychometric** - 3 scenarios with trait ratings
5. **Completion** - Submit and view results

**Proctoring Setup:**
```jsx
const setupCamera = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  videoRef.current.srcObject = stream;
  
  // Initialize face detection
  await faceapi.nets.tinyFaceDetector.loadFromUri('/models');
  startFaceDetection();
};

const startFaceDetection = () => {
  setInterval(async () => {
    const detections = await faceapi.detectAllFaces(
      videoRef.current, 
      new faceapi.TinyFaceDetectorOptions()
    );
    
    if (detections.length === 0) {
      reportViolation('no_face');
    } else if (detections.length > 1) {
      reportViolation('multiple_faces');
    }
  }, 1000);
};
```

**MCQ Component:**
```jsx
<Card>
  <CardHeader>
    <Progress value={(questionIndex + 1) / totalQuestions * 100} />
    <p>Question {questionIndex + 1} of {totalQuestions}</p>
    <Timer seconds={timeRemaining} />
  </CardHeader>
  <CardContent>
    <p className="text-lg">{question.question}</p>
    <RadioGroup value={selectedAnswer} onValueChange={setSelectedAnswer}>
      {question.options.map((option, i) => (
        <RadioGroupItem key={i} value={i} label={option} />
      ))}
    </RadioGroup>
  </CardContent>
  <CardFooter>
    <Button onClick={submitAnswer}>Next</Button>
  </CardFooter>
</Card>
```

**Coding Editor:**
```jsx
import Editor from '@monaco-editor/react';

<Editor
  height="400px"
  language={language}
  value={code}
  onChange={setCode}
  theme="vs-dark"
  options={{
    minimap: { enabled: false },
    fontSize: 14,
    lineNumbers: 'on',
    automaticLayout: true,
  }}
/>

<Select value={language} onValueChange={setLanguage}>
  <SelectItem value="python">Python</SelectItem>
  <SelectItem value="javascript">JavaScript</SelectItem>
  <SelectItem value="cpp">C++</SelectItem>
  <SelectItem value="java">Java</SelectItem>
</Select>

<Button onClick={runCode}>Run Code</Button>
<Button onClick={submitCode}>Submit</Button>
```

**Psychometric Section:**
```jsx
<Card>
  <p className="text-lg">{scenario.scenario}</p>
  
  {scenario.traits.map(trait => (
    <div key={trait}>
      <Label>{trait}</Label>
      <Slider
        min={1}
        max={10}
        value={[traitScores[trait] || 5]}
        onValueChange={(v) => updateTraitScore(trait, v[0])}
      />
    </div>
  ))}
  
  <Textarea
    placeholder="Describe how you would handle this situation..."
    value={responseText}
    onChange={(e) => setResponseText(e.target.value)}
  />
</Card>
```

---

### AdminDashboardPage.jsx

Admin panel for system management.

**Features:**
- User management (CRUD)
- Job description management
- System statistics
- Role-based user creation

**User Management:**
```jsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Email</TableHead>
      <TableHead>Role</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {users.map(user => (
      <TableRow key={user.id}>
        <TableCell>{user.name}</TableCell>
        <TableCell>{user.email}</TableCell>
        <TableCell>
          <Badge>{user.role}</Badge>
        </TableCell>
        <TableCell>
          <Button onClick={() => editUser(user)}>Edit</Button>
          <Button variant="destructive" onClick={() => deleteUser(user.id)}>
            Delete
          </Button>
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

---

### ProctorDashboardPage.jsx

Real-time proctoring monitor.

**Features:**
- List of active assessments
- Live violation feed
- Violation count badges
- Flag assessment for review
- Assessment status indicators

**Active Assessments:**
```jsx
<div className="grid grid-cols-3 gap-4">
  {activeAssessments.map(assessment => (
    <Card key={assessment.id}>
      <CardHeader>
        <h3>{assessment.candidate_name}</h3>
        <Badge variant={assessment.violations > 3 ? 'destructive' : 'default'}>
          {assessment.violations} violations
        </Badge>
      </CardHeader>
      <CardContent>
        <p>Started: {formatTime(assessment.started_at)}</p>
        <p>Section: {assessment.current_section}</p>
      </CardContent>
      <CardFooter>
        <Button onClick={() => viewViolations(assessment.id)}>
          View Details
        </Button>
        <Button 
          variant="destructive"
          onClick={() => flagAssessment(assessment.id)}
        >
          Flag
        </Button>
      </CardFooter>
    </Card>
  ))}
</div>
```

---

## API Service

### Configuration (api.js)

```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 
  (import.meta.env.DEV ? 'http://localhost:5000' : '');

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### API Calls

```javascript
// Authentication
export const login = (email, password) => 
  api.post('/api/auth/login', { email, password });

export const getCurrentUser = () => 
  api.get('/api/auth/me');

// Candidates
export const getCandidates = (params) => 
  api.get('/api/interviewer/candidates', { params });

export const getCandidate = (id) => 
  api.get(`/api/interviewer/candidates/${id}`);

export const rejectCandidate = (id, reason) => 
  api.post(`/api/interviewer/candidates/${id}/reject`, { reason });

export const scheduleAssessment = (id, scheduledTime) => 
  api.post(`/api/interviewer/candidates/${id}/schedule`, { 
    scheduled_time: scheduledTime 
  });

// Assessments
export const verifyToken = (token) => 
  api.get(`/api/interviewee/assessment/verify/${token}`);

export const startAssessment = (token) => 
  api.post(`/api/interviewee/assessment/start-by-token/${token}`);

export const submitMCQ = (assessmentId, questionId, answer, timeTaken) => 
  api.post('/api/assessment/mcq/submit', {
    assessment_id: assessmentId,
    question_id: questionId,
    answer,
    time_taken: timeTaken
  });

export const submitCode = (assessmentId, problemId, code, language) => 
  api.post('/api/assessment/code/submit', {
    assessment_id: assessmentId,
    problem_id: problemId,
    code,
    language
  });

export const completeAssessment = (assessmentId) => 
  api.post(`/api/assessment/complete`, { assessment_id: assessmentId });
```

---

## Routing

### App.jsx

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/apply" element={<ApplyPage />} />
        
        {/* Assessment Routes */}
        <Route path="/assessment" element={<AssessmentPage />} />
        <Route path="/assessment/:token" element={<AssessmentPage />} />
        
        {/* Protected Routes */}
        <Route path="/dashboard" element={
          <ProtectedRoute roles={['interviewer']}>
            <InterviewerDashboardPage />
          </ProtectedRoute>
        } />
        
        <Route path="/admin" element={
          <ProtectedRoute roles={['admin']}>
            <AdminDashboardPage />
          </ProtectedRoute>
        } />
        
        <Route path="/proctor" element={
          <ProtectedRoute roles={['proctor']}>
            <ProctorDashboardPage />
          </ProtectedRoute>
        } />
        
        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  );
}
```

### Protected Route Component

```jsx
function ProtectedRoute({ children, roles }) {
  const user = JSON.parse(localStorage.getItem('user'));
  const token = localStorage.getItem('token');
  
  if (!token || !user) {
    return <Navigate to="/login" />;
  }
  
  if (roles && !roles.includes(user.role)) {
    return <Navigate to="/" />;
  }
  
  return children;
}
```

---

## Styling

### Tailwind Utilities

```jsx
// Common patterns used across components

// Card with hover effect
<div className="p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow">

// Gradient button
<button className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg">

// Status badges
<span className="px-2 py-1 text-xs font-medium rounded-full bg-green-100 text-green-800">

// Form input
<input className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">

// Table row hover
<tr className="hover:bg-gray-50 transition-colors">
```

### Color Scheme

```css
/* index.css - CSS Variables */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --muted: 210 40% 96.1%;
  --accent: 210 40% 96.1%;
  --destructive: 0 84.2% 60.2%;
  --border: 214.3 31.8% 91.4%;
  --ring: 222.2 84% 4.9%;
}
```

---

## Toast Notifications

### Usage

```jsx
import { useToast } from '@/hooks/use-toast';

function MyComponent() {
  const { toast } = useToast();
  
  const handleSuccess = () => {
    toast({
      title: "Success!",
      description: "Your changes have been saved.",
      variant: "default",
    });
  };
  
  const handleError = () => {
    toast({
      title: "Error",
      description: "Something went wrong. Please try again.",
      variant: "destructive",
    });
  };
}
```

---

## Testing

### Running Tests

```bash
# Unit tests
npm test

# E2E tests
npm run test:e2e
```

### Testing Utilities

```javascript
// Example test
import { render, screen, fireEvent } from '@testing-library/react';

test('login form submits correctly', async () => {
  render(<LoginPage />);
  
  fireEvent.change(screen.getByLabelText(/email/i), {
    target: { value: 'test@example.com' }
  });
  
  fireEvent.change(screen.getByLabelText(/password/i), {
    target: { value: 'password123' }
  });
  
  fireEvent.click(screen.getByRole('button', { name: /login/i }));
  
  await screen.findByText(/dashboard/i);
});
```

---

## Build & Deployment

### Vite Configuration

```javascript
// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:5000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
```

### Production Build

```bash
# Build for production
npm run build

# Output in dist/ directory
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   └── index-[hash].css
└── favicon.ico
```

### Deployment to Netlify/Vercel

```bash
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

## Related Documentation

- [PROJECT_ARCHITECTURE.md](PROJECT_ARCHITECTURE.md) - System overview
- [API_DOCS.md](API_DOCS.md) - Backend API reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment

---

*Last Updated: January 2026*
*Version: 1.0*
