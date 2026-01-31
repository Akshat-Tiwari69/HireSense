# Assessment System Guide

Complete documentation for the candidate assessment system including MCQ, coding challenges, and psychometric tests.

---

## Overview

The assessment system evaluates candidates through three distinct sections:

1. **MCQ Section** - 10 multiple choice questions testing technical knowledge
2. **Coding Section** - Programming challenge with automated code execution
3. **Psychometric Section** - 3 behavioral scenarios with trait ratings

---

## Assessment Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                    ASSESSMENT LIFECYCLE                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  1. SCHEDULING                                                     │
│     └── Interviewer schedules via POST /candidates/:id/schedule    │
│     └── Candidate receives email with token link                   │
│                                                                    │
│  2. VERIFICATION                                                   │
│     └── GET /assessment/verify/:token                              │
│     └── Check: token valid, time window (±30 min)                  │
│                                                                    │
│  3. CAMERA SETUP                                                   │
│     └── Enable webcam for proctoring                               │
│     └── Initialize face detection                                  │
│                                                                    │
│  4. MCQ SECTION (10 questions)                                     │
│     └── 30 seconds per question                                    │
│     └── POST /assessment/mcq/submit (per question)                 │
│                                                                    │
│  5. CODING SECTION (1 problem)                                     │
│     └── Monaco editor with language selection                      │
│     └── Run code via Piston API                                    │
│     └── POST /assessment/code/submit                               │
│                                                                    │
│  6. PSYCHOMETRIC SECTION (3 scenarios)                             │
│     └── Rate traits 1-10 for each scenario                         │
│     └── POST /assessment/psychometric/submit                       │
│                                                                    │
│  7. COMPLETION                                                     │
│     └── POST /assessment/complete                                  │
│     └── Calculate scores, generate recommendation                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Scoring System

### MCQ Scoring

```
MCQ Score = (Correct Answers / Total Questions) × 100

Example:
  7 correct out of 10 = 70%
```

### Coding Scoring

```
Coding Score = (Test Cases Passed / Total Test Cases) × 100

Example:
  5 passed out of 6 test cases = 83.33%
```

### Technical Score (Combined)

```
Technical Score = (MCQ Score × 0.4) + (Coding Score × 0.6)

Example:
  MCQ: 70%, Coding: 83.33%
  Technical = (70 × 0.4) + (83.33 × 0.6) = 28 + 50 = 78%
```

### Psychometric Score

```
Psychometric Score = Average of All Trait Ratings × 10

Example:
  Traits: leadership=8, communication=7, decision_making=9
  Average = (8 + 7 + 9) / 3 = 8
  Psychometric Score = 8 × 10 = 80%
```

### Overall Score

```
Overall Score = (Technical Score × 0.6) + (Psychometric Score × 0.4)

Example:
  Technical: 78%, Psychometric: 80%
  Overall = (78 × 0.6) + (80 × 0.4) = 46.8 + 32 = 78.8%
```

---

## Question Bank

### MCQ Questions (questions_bank.py)

```python
MCQ_QUESTIONS = [
    {
        "id": 1,
        "question": "What is the time complexity of binary search?",
        "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"],
        "correct_answer": 1,
        "category": "Algorithms",
        "difficulty": "medium"
    },
    {
        "id": 2,
        "question": "Which data structure uses LIFO?",
        "options": ["Queue", "Stack", "Array", "Tree"],
        "correct_answer": 1,
        "category": "Data Structures",
        "difficulty": "easy"
    },
    # ... more questions
]
```

### Coding Problems

```python
CODING_PROBLEMS = [
    {
        "id": 1,
        "title": "Two Sum",
        "description": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
        "example": "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].",
        "test_cases": [
            {"input": "[2,7,11,15], 9", "expected": "[0,1]"},
            {"input": "[3,2,4], 6", "expected": "[1,2]"},
            {"input": "[3,3], 6", "expected": "[0,1]"}
        ],
        "difficulty": "easy",
        "time_limit": 30  # minutes
    }
]
```

### Psychometric Scenarios

```python
PSYCHOMETRIC_SCENARIOS = [
    {
        "id": 1,
        "scenario": "You discover that a team member has been taking credit for your work in meetings. How would you handle this situation?",
        "traits": ["communication", "conflict_resolution", "professionalism"],
        "expected_behaviors": [
            "Address the issue directly with the colleague",
            "Document your contributions",
            "Maintain professional composure"
        ]
    },
    {
        "id": 2,
        "scenario": "Your manager assigns you a project with an unrealistic deadline. You know it cannot be completed on time without compromising quality. What do you do?",
        "traits": ["decision_making", "communication", "time_management"],
        "expected_behaviors": [
            "Communicate concerns proactively",
            "Propose alternatives",
            "Negotiate priorities"
        ]
    },
    {
        "id": 3,
        "scenario": "During a critical product launch, you discover a significant bug that wasn't caught in testing. The launch is in 2 hours. How do you proceed?",
        "traits": ["stress_management", "leadership", "problem_solving"],
        "expected_behaviors": [
            "Assess severity quickly",
            "Escalate appropriately",
            "Propose solutions"
        ]
    }
]
```

---

## API Endpoints

### Token Verification

```
GET /api/interviewee/assessment/verify/:token

Response (Success):
{
  "status": "success",
  "data": {
    "valid": true,
    "candidate_name": "John Doe",
    "scheduled_time": "2026-01-25T14:00:00",
    "can_start": true,
    "time_until_start": 0
  }
}

Response (Outside Window):
{
  "status": "error",
  "message": "Assessment not available. Scheduled for 2026-01-25 14:00",
  "data": {
    "minutes_away": 45,
    "allowed_window": 30
  }
}
```

### Start Assessment

```
POST /api/interviewee/assessment/start-by-token/:token

Response:
{
  "status": "success",
  "data": {
    "assessment_id": 42,
    "candidate_id": 1,
    "mcq_questions": [...],
    "coding_problem": {...},
    "psychometric_scenarios": [...]
  }
}
```

### Submit MCQ Answer

```
POST /api/assessment/mcq/submit
Content-Type: application/json

{
  "assessment_id": 42,
  "question_id": 1,
  "answer": 1,
  "time_taken": 15
}

Response:
{
  "status": "success",
  "data": {
    "is_correct": true,
    "correct_answer": 1
  }
}
```

### Submit Code Solution

```
POST /api/assessment/code/submit
Content-Type: application/json

{
  "assessment_id": 42,
  "problem_id": 1,
  "code": "def twoSum(nums, target):\n    seen = {}\n    for i, n in enumerate(nums):\n        if target - n in seen:\n            return [seen[target-n], i]\n        seen[n] = i",
  "language": "python"
}

Response:
{
  "status": "success",
  "data": {
    "test_results": [
      {"input": "[2,7,11,15], 9", "expected": "[0,1]", "actual": "[0,1]", "passed": true},
      {"input": "[3,2,4], 6", "expected": "[1,2]", "actual": "[1,2]", "passed": true},
      {"input": "[3,3], 6", "expected": "[0,1]", "actual": "[0,1]", "passed": true}
    ],
    "passed_count": 3,
    "total_count": 3,
    "score": 100
  }
}
```

### Submit Psychometric Response

```
POST /api/assessment/psychometric/submit
Content-Type: application/json

{
  "assessment_id": 42,
  "scenario_id": 1,
  "trait_scores": {
    "communication": 8,
    "conflict_resolution": 7,
    "professionalism": 9
  },
  "response_text": "I would first document my contributions, then schedule a private meeting with my colleague to discuss the issue professionally."
}

Response:
{
  "status": "success",
  "message": "Psychometric response saved"
}
```

### Complete Assessment

```
POST /api/assessment/complete
Content-Type: application/json

{
  "assessment_id": 42
}

Response:
{
  "status": "success",
  "data": {
    "assessment_id": 42,
    "scores": {
      "mcq": 70.0,
      "coding": 100.0,
      "technical": 88.0,
      "psychometric": 80.0,
      "overall": 84.8
    },
    "decision": "Recommend for Hire",
    "rationale": "Strong technical skills with excellent coding ability. Good interpersonal skills demonstrated in psychometric assessment.",
    "ai_recommendation": "Proceed to HR discussion"
  }
}
```

---

## Code Execution

### Piston API Integration

Code is executed securely using the Piston API:

```javascript
// Execute code via Piston
const executeCode = async (code, language) => {
  const languageMap = {
    'python': { language: 'python', version: '3.10' },
    'javascript': { language: 'javascript', version: '18.15.0' },
    'cpp': { language: 'cpp', version: '10.2.0' },
    'java': { language: 'java', version: '15.0.2' }
  };
  
  const response = await fetch('https://emkc.org/api/v2/piston/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      language: languageMap[language].language,
      version: languageMap[language].version,
      files: [{ content: code }]
    })
  });
  
  return response.json();
};
```

### Supported Languages

| Language | Version | File Extension |
|----------|---------|----------------|
| Python | 3.10 | .py |
| JavaScript | Node 18 | .js |
| C++ | GCC 10.2 | .cpp |
| Java | JDK 15 | .java |

---

## Frontend Implementation

### Assessment Page Structure

```jsx
// AssessmentPage.jsx
const [currentSection, setCurrentSection] = useState('setup'); // setup, mcq, coding, psychometric, complete
const [assessmentData, setAssessmentData] = useState(null);

// Sections
{currentSection === 'setup' && <CameraSetup onReady={() => setCurrentSection('mcq')} />}
{currentSection === 'mcq' && <MCQSection questions={mcqQuestions} onComplete={() => setCurrentSection('coding')} />}
{currentSection === 'coding' && <CodingSection problem={codingProblem} onComplete={() => setCurrentSection('psychometric')} />}
{currentSection === 'psychometric' && <PsychometricSection scenarios={scenarios} onComplete={() => setCurrentSection('complete')} />}
{currentSection === 'complete' && <CompletionScreen scores={scores} />}
```

### MCQ Section Component

```jsx
function MCQSection({ questions, assessmentId, onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  
  // Timer countdown
  useEffect(() => {
    const timer = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          handleSubmit(); // Auto-submit when time runs out
          return 30;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [currentIndex]);
  
  const handleSubmit = async () => {
    await api.post('/api/assessment/mcq/submit', {
      assessment_id: assessmentId,
      question_id: questions[currentIndex].id,
      answer: selectedAnswer,
      time_taken: 30 - timeLeft
    });
    
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setSelectedAnswer(null);
      setTimeLeft(30);
    } else {
      onComplete();
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <div className="flex justify-between">
          <span>Question {currentIndex + 1} of {questions.length}</span>
          <span className={timeLeft < 10 ? 'text-red-500' : ''}>
            {timeLeft}s
          </span>
        </div>
        <Progress value={(currentIndex + 1) / questions.length * 100} />
      </CardHeader>
      <CardContent>
        <p className="text-lg mb-4">{questions[currentIndex].question}</p>
        <RadioGroup value={selectedAnswer} onValueChange={setSelectedAnswer}>
          {questions[currentIndex].options.map((option, i) => (
            <div key={i} className="flex items-center space-x-2">
              <RadioGroupItem value={i} id={`option-${i}`} />
              <Label htmlFor={`option-${i}`}>{option}</Label>
            </div>
          ))}
        </RadioGroup>
      </CardContent>
      <CardFooter>
        <Button onClick={handleSubmit} disabled={selectedAnswer === null}>
          {currentIndex < questions.length - 1 ? 'Next' : 'Complete Section'}
        </Button>
      </CardFooter>
    </Card>
  );
}
```

### Coding Section Component

```jsx
import Editor from '@monaco-editor/react';

function CodingSection({ problem, assessmentId, onComplete }) {
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [output, setOutput] = useState('');
  const [testResults, setTestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  
  const runCode = async () => {
    setIsRunning(true);
    try {
      const result = await executeCode(code, language);
      setOutput(result.run?.output || result.run?.stderr || 'No output');
    } catch (error) {
      setOutput('Error executing code');
    }
    setIsRunning(false);
  };
  
  const submitCode = async () => {
    const response = await api.post('/api/assessment/code/submit', {
      assessment_id: assessmentId,
      problem_id: problem.id,
      code,
      language
    });
    setTestResults(response.data.data);
    
    // Allow review then proceed
    setTimeout(() => onComplete(), 3000);
  };
  
  return (
    <div className="grid grid-cols-2 gap-4">
      {/* Problem Description */}
      <Card>
        <CardHeader>
          <CardTitle>{problem.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{problem.description}</p>
          <pre className="bg-gray-100 p-4 mt-4 rounded">
            {problem.example}
          </pre>
        </CardContent>
      </Card>
      
      {/* Code Editor */}
      <div className="space-y-4">
        <Select value={language} onValueChange={setLanguage}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="python">Python</SelectItem>
            <SelectItem value="javascript">JavaScript</SelectItem>
            <SelectItem value="cpp">C++</SelectItem>
            <SelectItem value="java">Java</SelectItem>
          </SelectContent>
        </Select>
        
        <Editor
          height="400px"
          language={language}
          value={code}
          onChange={setCode}
          theme="vs-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 14
          }}
        />
        
        <div className="flex gap-2">
          <Button onClick={runCode} disabled={isRunning}>
            {isRunning ? 'Running...' : 'Run Code'}
          </Button>
          <Button onClick={submitCode} variant="default">
            Submit Solution
          </Button>
        </div>
        
        {/* Output */}
        <Card>
          <CardHeader>Output</CardHeader>
          <CardContent>
            <pre className="bg-gray-900 text-green-400 p-4 rounded">
              {output || 'Run your code to see output'}
            </pre>
          </CardContent>
        </Card>
        
        {/* Test Results */}
        {testResults && (
          <Card>
            <CardHeader>
              Test Results: {testResults.passed_count}/{testResults.total_count}
            </CardHeader>
            <CardContent>
              {testResults.test_results.map((test, i) => (
                <div key={i} className="flex items-center gap-2">
                  {test.passed ? '✅' : '❌'}
                  <span>Test {i + 1}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
```

---

## Decision Algorithm

### Recommendation Logic

```python
def generate_recommendation(scores):
    overall = scores['overall']
    technical = scores['technical']
    psychometric = scores['psychometric']
    
    if overall >= 80 and technical >= 75 and psychometric >= 70:
        decision = "Strong Hire"
        rationale = "Excellent performance across all areas"
    elif overall >= 70 and technical >= 65:
        decision = "Recommend for Hire"
        rationale = "Good technical skills with solid interpersonal abilities"
    elif overall >= 60:
        decision = "Consider for Hire"
        rationale = "Adequate performance, may need additional assessment"
    else:
        decision = "Not Recommended"
        rationale = "Performance below threshold in key areas"
    
    return decision, rationale
```

---

## Security

### Time Window Validation

```python
def validate_time_window(scheduled_time, current_time, window_minutes=30):
    scheduled = datetime.fromisoformat(scheduled_time)
    current = datetime.fromisoformat(current_time)
    
    window_start = scheduled - timedelta(minutes=window_minutes)
    window_end = scheduled + timedelta(minutes=window_minutes)
    
    return window_start <= current <= window_end
```

### Token Security

- Unique token generated per scheduled assessment
- Token invalidated after use
- Time-limited validity

---

## Related Documentation

- [PROCTOR_GUIDE.md](PROCTOR_GUIDE.md) - Proctoring system
- [ASSESSMENT_TIME_VALIDATION_GUIDE.md](ASSESSMENT_TIME_VALIDATION_GUIDE.md) - Time windows
- [API_DOCS.md](API_DOCS.md) - Complete API reference
- [FRONTEND_GUIDE.md](FRONTEND_GUIDE.md) - UI implementation

---

*Last Updated: January 2026*
*Version: 1.0*
