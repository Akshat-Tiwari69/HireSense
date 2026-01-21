# Quick Start: Using the AI Resume Analyzer

## ⚡ Fast Setup (5 Minutes)

### Step 1: Get OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)

### Step 2: Configure Backend
```bash
cd backend

# Set environment variable (Windows PowerShell)
$env:OPENAI_API_KEY="sk-your-key-here"

# Or create .env file
echo OPENAI_API_KEY=sk-your-key-here > .env
```

### Step 3: Install Dependencies
```bash
pip install openai
```

### Step 4: Test It
```bash
# Run the test function
python resume_analyzer.py
```

**Expected output:**
```
Testing Resume Analyzer...
============================================================

📊 Analysis Results:

✅ Pros (3):
  1. Strong full-stack expertise with 5 years proven experience
  2. Solid alignment with required tech stack
  3. Leadership experience demonstrated
  ...

✅ Test completed successfully!
```

### Step 5: Start the Server
```bash
python app.py
```

The AI analyzer is now integrated! Every resume upload will include AI analysis.

---

## 🧪 Testing with Postman/cURL

```bash
curl -X POST http://localhost:5000/api/resume/upload \
  -F "file=@resume.pdf" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "phone=1234567890"
```

**Check the response for:**
- `ai_analysis.pros` - List of strengths
- `ai_analysis.cons` - List of weaknesses  
- `ai_analysis.recommendation` - Match level
- `ai_analysis.enhanced_match_score` - AI score

---

## 💰 Cost Information

**Using GPT-4o-mini (current configuration):**
- **~$0.0002 per resume** (extremely affordable)
- 5,000 resumes = ~$1
- 50,000 resumes = ~$10

**Want better quality?**
Change to GPT-4o in `resume_analyzer.py`:
```python
self.model = "gpt-4o"  # More expensive but better
```

---

## ❓ Troubleshooting

### "OpenAI API key not found"
```bash
# Check if set
echo $env:OPENAI_API_KEY

# Set it
$env:OPENAI_API_KEY="sk-your-key"
```

### AI returns fallback mode
- Check API key is valid
- Verify internet connection
- Check OpenAI service status

### Still having issues?
See full guide: `docs/AI_ANALYZER_GUIDE.md`

---

## 📊 What You Get

For every resume, AI provides:
- ✅ 3-5 specific pros (strengths)
- ⚠️ 2-4 constructive cons
- 📝 Overall assessment
- 🎯 Recommendation (Strong/Good/Moderate/Weak Match)
- 💯 Confidence score
- 📈 Enhanced match score
- 🌟 Key highlights
- 📌 Areas for improvement

---

## 🚀 Next Steps for Team

### Shaivi (Frontend):
Display AI analysis in:
- Interviewer dashboard
- Candidate detail view
- Use `recommendation` for color coding
- Show pros/cons as bullet lists

### Akshat (Backend):
- Configure OpenAI API key in production
- Monitor API usage and costs
- Implement caching for re-uploads
- Add to email notifications

---

**Created:** January 21, 2026  
**Quick Reference for:** CYGNUSA Elite-Hire Team
