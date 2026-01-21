# AI Resume Analyzer Guide

## Overview
The AI Resume Analyzer uses OpenAI's GPT models to provide intelligent, context-aware analysis of candidate resumes. It generates pros, cons, and recommendations that go beyond simple keyword matching.

---

## Features

### 🎯 Core Capabilities

1. **Intelligent Pros Generation (3-5 points)**
   - Evidence-based strengths
   - Context-aware skill assessment
   - Experience and qualification highlights

2. **Constructive Cons Identification (2-4 points)**
   - Skill gaps with specific feedback
   - Areas for improvement
   - Constructive, actionable insights

3. **Overall Assessment**
   - Comprehensive summary of candidate fit
   - Balanced evaluation
   - Recommendation classification

4. **Recommendation Levels**
   - **Strong Match**: 80%+ score, meets all requirements
   - **Good Match**: 60-79% score, most requirements met
   - **Moderate Match**: 40-59% score, some gaps present
   - **Weak Match**: <40% score, significant gaps

5. **Enhanced Match Scoring**
   - AI-enhanced scoring beyond keyword matching
   - Context and implicit qualification consideration
   - More nuanced evaluation than rule-based systems

6. **Confidence Scoring**
   - AI provides confidence level (0-100) for its assessment
   - Helps recruiters understand reliability of analysis

---

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install openai
```

The `openai` package has been added to `requirements.txt`.

### 2. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Go to API Keys section
4. Create a new API key
5. Copy the key (starts with `sk-`)

### 3. Configure Environment

Create or update `.env` file in backend directory:

```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**For Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

**For Linux/Mac:**
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

---

## Usage

### Integrated with Resume Upload

The AI analyzer is automatically integrated into the resume upload endpoint. When a resume is uploaded:

1. Resume is parsed for structured data
2. AI analyzes the resume content
3. Pros, cons, and recommendations are generated
4. Enhanced match score is calculated
5. All data is stored in the database
6. Response includes AI analysis

**Example API Call:**

```bash
curl -X POST http://localhost:5000/api/resume/upload \
  -F "file=@resume.pdf" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "phone=1234567890"
```

**Response includes:**

```json
{
  "status": "success",
  "message": "Resume uploaded and analyzed successfully",
  "data": {
    "candidate_id": 1,
    "parsed_data": {
      "skills": ["Python", "React", "AWS"],
      "experience": 5,
      "education": "B.S. Computer Science",
      "match_score": 82
    },
    "ai_analysis": {
      "pros": [
        "Strong full-stack expertise with 5 years proven experience",
        "Solid alignment with core tech stack (Python, React, AWS)",
        "Leadership experience managing team of 4 developers"
      ],
      "cons": [
        "Limited experience with containerization (Docker/Kubernetes)",
        "No certifications mentioned for cloud platforms"
      ],
      "overall_assessment": "Strong candidate with excellent technical skills and relevant experience. Minor gaps in DevOps tools can be addressed through training.",
      "recommendation": "Strong Match",
      "confidence_score": 88,
      "enhanced_match_score": 85,
      "key_highlights": [
        "5 years of full-stack development",
        "Built scalable microservices"
      ],
      "areas_for_improvement": [
        "Container orchestration skills",
        "Cloud certifications"
      ]
    }
  }
}
```

### Standalone Usage

You can also use the analyzer independently:

```python
from resume_analyzer import analyze_resume

# Your data
resume_text = "Your resume content here..."
parsed_data = {
    'skills': ['Python', 'React', 'AWS'],
    'experience': 5,
    'education': 'Bachelor of Science in Computer Science',
    'match_score': 75
}
job_requirements = {
    'skills': ['Python', 'React', 'AWS', 'Docker'],
    'min_experience': 3
}

# Analyze
result = analyze_resume(
    resume_text=resume_text,
    parsed_data=parsed_data,
    job_requirements=job_requirements,
    enhance_score=True  # Enable AI-enhanced scoring
)

# Access results
print("Pros:", result['pros'])
print("Cons:", result['cons'])
print("Recommendation:", result['recommendation'])
print("Enhanced Score:", result.get('enhanced_match_score', 'N/A'))
```

---

## How It Works

### 1. Context-Rich Prompting

The analyzer builds a comprehensive prompt including:
- Job requirements and role type
- Candidate skills and experience
- Education background
- Resume excerpt for context
- Current match score

### 2. AI Analysis

Uses OpenAI's GPT-4o-mini model (cost-effective):
- Temperature: 0.7 (balanced creativity)
- Max tokens: 1000
- JSON-structured responses
- Explicit HR expert persona

**Model Selection:**
- `gpt-4o-mini`: Cost-effective, good quality (current)
- `gpt-4o`: Premium model for better results (configurable)

### 3. Response Validation

All AI responses are validated:
- JSON structure verification
- Field existence checks
- Data type validation
- Content sanitization
- Fallback for missing data

### 4. Fallback Mechanism

If AI fails, rule-based analysis is used:
- Ensures system always returns results
- Uses parsed data for basic analysis
- Marks response as `fallback_mode: true`

---

## Configuration

### Model Selection

Change the model in `resume_analyzer.py`:

```python
class ResumeAnalyzer:
    def __init__(self, api_key: Optional[str] = None):
        # ...
        self.model = "gpt-4o-mini"  # Change to "gpt-4o" for better results
```

### Temperature Control

Adjust creativity vs consistency:

```python
response = self.client.chat.completions.create(
    model=self.model,
    temperature=0.7,  # 0.0 = consistent, 1.0 = creative
    # ...
)
```

### Custom Job Requirements

Pass different requirements per position:

```python
# In app.py upload_resume function
job_description = {
    'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Docker'],
    'min_experience': 3
}
```

---

## Testing

### Run the Test Function

The analyzer includes a built-in test:

```bash
cd backend
python resume_analyzer.py
```

**Expected Output:**
```
Testing Resume Analyzer...
============================================================

📊 Analysis Results:

✅ Pros (3):
  1. Strong full-stack expertise with 5 years proven experience
  2. Solid alignment with required tech stack
  3. Leadership experience demonstrated

⚠️ Cons (2):
  1. Could benefit from additional cloud certifications
  2. Experience with CI/CD pipelines not explicitly mentioned

📝 Overall Assessment:
  Strong candidate with excellent technical skills...

🎯 Recommendation: Good Match
💯 Confidence Score: 85%
📈 Enhanced Match Score: 82%

============================================================
✅ Test completed successfully!
```

### Integration Testing

Test with actual resume upload:

```bash
# 1. Start the Flask server
python app.py

# 2. Upload a test resume
curl -X POST http://localhost:5000/api/resume/upload \
  -F "file=@test_resume.pdf" \
  -F "name=Test Candidate" \
  -F "email=test@example.com"

# 3. Check the response for ai_analysis field
```

---

## Database Integration

### Storage Format

AI analysis is stored in the `candidates` table:

```sql
-- Pros stored as newline-separated string
pros TEXT,

-- Cons stored as newline-separated string  
cons TEXT,

-- Status based on recommendation
status TEXT DEFAULT 'pending'
```

### Status Mapping

| AI Recommendation | Database Status |
|------------------|-----------------|
| Strong Match | `under_review` |
| Good Match | `pending` |
| Moderate Match | `pending` |
| Weak Match | `pending` |

### Retrieval

Pros and cons are stored as text with newlines:

```python
# In database
pros = "Strength 1\nStrength 2\nStrength 3"

# Convert to list
pros_list = pros.split('\n')
```

---

## Cost Optimization

### Current Configuration

- Model: `gpt-4o-mini`
- Max tokens: 1000
- Temperature: 0.7

**Estimated Cost per Resume:**
- Input: ~500 tokens (resume + prompt)
- Output: ~300 tokens (analysis)
- **Total: ~$0.0002 per resume** (as of Jan 2026)

### Tips to Reduce Costs

1. **Use gpt-4o-mini**: Already configured
2. **Limit resume text**: Send first 500-1000 chars
3. **Batch processing**: Analyze multiple resumes in one call (future enhancement)
4. **Cache results**: Store analysis to avoid re-processing
5. **Conditional analysis**: Only analyze high-match candidates

### Upgrade to GPT-4o

For better quality (at higher cost):

```python
self.model = "gpt-4o"  # ~10x more expensive, better results
```

---

## Error Handling

### Types of Errors

1. **Missing API Key**
   ```
   ValueError: OpenAI API key not found
   ```
   **Fix**: Set `OPENAI_API_KEY` environment variable

2. **API Rate Limits**
   ```
   openai.error.RateLimitError
   ```
   **Fix**: Add retry logic or upgrade OpenAI plan

3. **JSON Parsing Error**
   ```
   json.JSONDecodeError
   ```
   **Fix**: Automatic fallback to rule-based analysis

4. **Network Errors**
   ```
   openai.error.APIConnectionError
   ```
   **Fix**: Check internet connection, retry with exponential backoff

### Fallback Behavior

When AI fails, the system:
1. Logs the error
2. Generates rule-based analysis
3. Returns structured response
4. Marks as `fallback_mode: true`
5. Sets confidence_score to 65

---

## Best Practices

### 1. API Key Security

- **Never commit API keys to Git**
- Use environment variables
- Rotate keys periodically
- Use separate keys for dev/prod

### 2. Error Monitoring

```python
# Add monitoring in app.py
if ai_analysis.get('fallback_mode'):
    app.logger.warning(f"AI analysis failed for candidate {candidate_id}")
```

### 3. Rate Limiting

OpenAI has rate limits:
- Free tier: 3 RPM (requests per minute)
- Tier 1: 500 RPM
- Tier 2+: 5000+ RPM

Implement request queuing for high volume:

```python
import time
from threading import Lock

analysis_lock = Lock()

def analyze_with_rate_limit(resume_text, ...):
    with analysis_lock:
        result = analyze_resume(...)
        time.sleep(0.2)  # 5 requests per second max
        return result
```

### 4. Caching

Avoid re-analyzing the same resume:

```python
# Store analysis hash
import hashlib

resume_hash = hashlib.md5(resume_text.encode()).hexdigest()
# Check cache before calling AI
```

---

## Troubleshooting

### Issue: "OpenAI API key not found"

**Solution:**
```bash
# Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Or create .env file
echo "OPENAI_API_KEY=sk-your-key-here" >> backend/.env
```

### Issue: AI always returns fallback

**Diagnosis:**
```bash
# Check API key is valid
python -c "import os; print(os.environ.get('OPENAI_API_KEY', 'NOT SET'))"

# Test connection
python resume_analyzer.py
```

**Common causes:**
- Invalid API key
- Expired API key
- No internet connection
- OpenAI service outage

### Issue: Generic or poor quality analysis

**Solutions:**
1. Upgrade to GPT-4o: `self.model = "gpt-4o"`
2. Increase max_tokens: `max_tokens=1500`
3. Adjust temperature: `temperature=0.5` (more focused)
4. Improve prompt engineering

### Issue: Slow response times

**Solutions:**
1. Use streaming responses (future enhancement)
2. Implement async processing
3. Cache common analyses
4. Use gpt-4o-mini (faster)

---

## Future Enhancements

### Planned Features

1. **Batch Analysis**: Analyze multiple resumes in parallel
2. **Async Processing**: Non-blocking AI calls
3. **Response Caching**: Store and reuse analyses
4. **Custom Prompts**: Per-role prompt templates
5. **Sentiment Analysis**: Tone and communication style evaluation
6. **Red Flags Detection**: Identify concerning patterns
7. **Comparison Mode**: Compare multiple candidates
8. **Multi-language Support**: Analyze resumes in different languages

### Integration Points

1. **Email Notifications**: Include AI insights in emails
2. **Interviewer Dashboard**: Display AI recommendations
3. **Search & Filter**: Filter by AI recommendation
4. **Analytics**: Track AI accuracy over time

---

## API Reference

### `ResumeAnalyzer` Class

```python
class ResumeAnalyzer:
    """AI-powered resume analyzer"""
    
    def __init__(self, api_key: Optional[str] = None)
    def generate_pros_cons(resume_text, parsed_data, job_requirements) -> Dict
    def enhance_match_score(resume_text, parsed_data, job_requirements) -> int
```

### `analyze_resume()` Function

```python
def analyze_resume(
    resume_text: str,
    parsed_data: Dict,
    job_requirements: Dict,
    api_key: Optional[str] = None,
    enhance_score: bool = True
) -> Dict[str, any]
```

**Returns:**
```python
{
    'pros': List[str],
    'cons': List[str],
    'overall_assessment': str,
    'recommendation': str,  # "Strong Match" | "Good Match" | "Moderate Match" | "Weak Match"
    'confidence_score': int,  # 0-100
    'key_highlights': List[str],
    'areas_for_improvement': List[str],
    'enhanced_match_score': int,  # If enhance_score=True
    'fallback_mode': bool  # Present only if AI failed
}
```

---

## Support & Documentation

- **OpenAI Docs**: https://platform.openai.com/docs
- **GPT Models**: https://platform.openai.com/docs/models
- **Pricing**: https://openai.com/pricing
- **Rate Limits**: https://platform.openai.com/docs/guides/rate-limits

---

**Created:** January 21, 2026  
**Task:** A6 - AI Resume Analyzer  
**Author:** Akshat  
**Model:** GPT-4o-mini (OpenAI)
