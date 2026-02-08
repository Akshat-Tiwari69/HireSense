"""
AI Resume Analyzer Module
"""

import os
import json
import httpx
from typing import Dict, List, Optional, Tuple


class ResumeAnalyzer:
    """
    Generates pros, cons, and enhanced match analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Resume Analyzer
        
        Args:
        """
        
        if not self.api_key:
            raise ValueError(
                "or pass api_key parameter"
            )
        
        try:
            from openai import OpenAI
            http_client = httpx.Client()
            self.client = OpenAI(api_key=self.api_key, http_client=http_client)
        except TypeError as e:
            # Older/newer client versions may not accept implicit proxies; build httpx client explicitly
            if "proxies" in str(e):
                proxy = (
                    os.environ.get("HTTPS_PROXY")
                    or os.environ.get("https_proxy")
                    or os.environ.get("HTTP_PROXY")
                    or os.environ.get("http_proxy")
                )
                http_client = httpx.Client(proxies=proxy) if proxy else httpx.Client()
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key, http_client=http_client)
            else:
                raise
        self.model = "gpt-4o-mini"  # Using cost-effective model, can upgrade to gpt-4o for better results
    
    def generate_pros_cons(
        self,
        resume_text: str,
        parsed_data: Dict,
        job_requirements: Dict
    ) -> Dict[str, any]:
        """
        Generate AI-powered pros and cons analysis for a candidate
        
        Args:
            resume_text: Raw text extracted from resume
            parsed_data: Structured data from resume parser (skills, experience, education)
            job_requirements: Job description with required skills and experience
        
        Returns:
            Dictionary with:
            - pros: List of strengths (3-5 points)
            - cons: List of weaknesses (2-4 points)
            - overall_assessment: Brief summary
            - recommendation: "Strong Match", "Good Match", "Moderate Match", "Weak Match"
            - confidence_score: 0-100 indicating AI's confidence in the assessment
        """
        try:
            # Build context-rich prompt
            prompt = self._build_analysis_prompt(resume_text, parsed_data, job_requirements)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert HR analyst and recruiter with 15+ years of experience evaluating candidates across all industries and roles. "
                            "The company is based in India. All evaluations should consider Indian industry standards, qualifications, and regulatory context. "
                            "Your role is to evaluate candidate resumes objectively against the SPECIFIC job role they applied for. "
                            "Do NOT penalize candidates for lacking skills irrelevant to their applied role (e.g., do not expect technical/coding skills from a lawyer). "
                            "Be honest but fair, focusing on both strengths and areas for improvement. "
                            "Provide responses in valid JSON format only."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,  # Balanced creativity and consistency
                max_tokens=1000,
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse response
            result_text = response.choices[0].message.content
            analysis = json.loads(result_text)
            
            # Validate and format response
            return self._validate_and_format_response(analysis, parsed_data)
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return self._generate_fallback_analysis(parsed_data, job_requirements)
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._generate_fallback_analysis(parsed_data, job_requirements)
    
    def _build_analysis_prompt(
        self,
        resume_text: str,
        parsed_data: Dict,
        job_requirements: Dict
    ) -> str:
        """Build a comprehensive prompt for AI analysis"""
        
        skills_str = ", ".join(parsed_data.get('skills', [])[:15])  # Top 15 skills
        experience_years = parsed_data.get('experience', 0)
        education = parsed_data.get('education', 'Not Specified')
        match_score = parsed_data.get('match_score', 0)
        
        required_skills = ", ".join(job_requirements.get('skills', []))
        min_experience = job_requirements.get('min_experience', 0)
        job_title = job_requirements.get('title', 'the applied position')
        department = job_requirements.get('department', '')
        role_context = f"{job_title} ({department})" if department else job_title
        
        return f"""
Analyze this candidate's resume for the role of **{role_context}** and provide a detailed evaluation.
The company is based in **India** — use Indian industry standards, laws, regulations, and qualifications as context.

**Job Requirements:**
- Position: {role_context}
- Required Skills/Qualifications: {required_skills}
- Minimum Experience: {min_experience} years

**Candidate Profile:**
- Skills/Qualifications: {skills_str}
- Years of Experience: {experience_years}
- Education: {education}
- Match Score (calculated): {match_score}%

**Resume Excerpt (first 500 chars):**
{resume_text[:500]}...

**Task:**
Provide a comprehensive analysis in the following JSON format:

{{
  "pros": [
    "Specific strength 1 with evidence",
    "Specific strength 2 with evidence",
    "Specific strength 3 with evidence"
  ],
  "cons": [
    "Specific concern 1 with constructive feedback",
    "Specific concern 2 with constructive feedback"
  ],
  "overall_assessment": "2-3 sentence summary of the candidate's fit",
  "recommendation": "Strong Match|Good Match|Moderate Match|Weak Match",
  "confidence_score": 85,
  "key_highlights": [
    "Most impressive qualification 1",
    "Most impressive qualification 2"
  ],
  "areas_for_improvement": [
    "Specific skill gap 1",
    "Specific skill gap 2"
  ]
}}

**Guidelines:**
1. Pros: Focus on demonstrated skills, relevant experience, and strong qualifications for THIS SPECIFIC ROLE (3-5 points)
2. Cons: Be constructive, identify skill gaps or concerns RELEVANT TO THE APPLIED ROLE (2-4 points, don't be overly negative)
3. Overall Assessment: Balanced summary considering both strengths and weaknesses for this role
4. Recommendation: Base on overall fit for the SPECIFIC role applied
5. Confidence Score: Your confidence in this assessment (0-100)
6. Be specific and evidence-based, avoid generic statements
7. ONLY evaluate skills relevant to the applied role — do NOT penalize for lacking unrelated skills (e.g., coding skills for a legal role)
8. Consider Indian industry standards and qualifications where applicable

Respond ONLY with valid JSON, no additional text.
"""
    
    def _validate_and_format_response(
        self,
        analysis: Dict,
        parsed_data: Dict
    ) -> Dict[str, any]:
        """Validate AI response and ensure proper formatting"""
        
        # Ensure required fields exist
        validated = {
            "pros": analysis.get("pros", [])[:5],  # Max 5 pros
            "cons": analysis.get("cons", [])[:4],  # Max 4 cons
            "overall_assessment": analysis.get("overall_assessment", "Candidate shows potential for the role."),
            "recommendation": analysis.get("recommendation", "Moderate Match"),
            "confidence_score": min(max(analysis.get("confidence_score", 75), 0), 100),  # Clamp 0-100
            "key_highlights": analysis.get("key_highlights", [])[:3],
            "areas_for_improvement": analysis.get("areas_for_improvement", [])[:3]
        }
        
        # Ensure at least some pros and cons
        if not validated["pros"]:
            validated["pros"] = [
                f"Possesses {len(parsed_data.get('skills', []))} relevant skills/qualifications",
                f"Has {parsed_data.get('experience', 0)} years of experience"
            ]
        
        if not validated["cons"]:
            validated["cons"] = ["Further assessment needed in interview"]
        
        # Validate recommendation
        valid_recommendations = ["Strong Match", "Good Match", "Moderate Match", "Weak Match"]
        if validated["recommendation"] not in valid_recommendations:
            # Default based on match score
            match_score = parsed_data.get('match_score', 0)
            if match_score >= 80:
                validated["recommendation"] = "Strong Match"
            elif match_score >= 60:
                validated["recommendation"] = "Good Match"
            elif match_score >= 40:
                validated["recommendation"] = "Moderate Match"
            else:
                validated["recommendation"] = "Weak Match"
        
        return validated
    
    def _generate_fallback_analysis(
        self,
        parsed_data: Dict,
        job_requirements: Dict
    ) -> Dict[str, any]:
        """
        Generate rule-based analysis when AI fails
        This ensures the system always returns something useful
        """
        
        skills = parsed_data.get('skills', [])
        experience = parsed_data.get('experience', 0)
        education = parsed_data.get('education', 'Not Specified')
        match_score = parsed_data.get('match_score', 0)
        
        required_skills = {s.lower() for s in job_requirements.get('skills', [])}
        candidate_skills = {s.lower() for s in skills}
        matching_skills = required_skills.intersection(candidate_skills)
        missing_skills = required_skills - candidate_skills
        
        # Generate pros
        pros = []
        if len(skills) >= 10:
            pros.append(f"Demonstrates broad expertise with {len(skills)} identified skills/qualifications")
        if experience >= job_requirements.get('min_experience', 0):
            pros.append(f"Meets experience requirement with {experience} years in the field")
        if matching_skills:
            pros.append(f"Strong alignment with required skills: {', '.join(sorted(matching_skills)[:3])}")
        if education and education != "Not Specified":
            pros.append(f"Educational background: {education}")
        if match_score >= 70:
            pros.append(f"High match score of {match_score}% indicates strong qualification fit")
        
        # Generate cons
        cons = []
        if experience < job_requirements.get('min_experience', 0):
            cons.append(f"Experience level ({experience} years) below requirement ({job_requirements.get('min_experience', 0)} years)")
        if missing_skills:
            cons.append(f"Missing some required skills: {', '.join(sorted(missing_skills)[:3])}")
        if match_score < 50:
            cons.append("Match score suggests significant skill gaps that need to be addressed")
        if not cons:
            cons.append("Further assessment recommended in interview")
        
        # Determine recommendation
        if match_score >= 80 and experience >= job_requirements.get('min_experience', 0):
            recommendation = "Strong Match"
        elif match_score >= 60:
            recommendation = "Good Match"
        elif match_score >= 40:
            recommendation = "Moderate Match"
        else:
            recommendation = "Weak Match"
        
        return {
            "pros": pros[:5],
            "cons": cons[:4],
            "overall_assessment": f"Candidate demonstrates {len(matching_skills)} of {len(required_skills)} required skills with {experience} years of experience. Match score: {match_score}%.",
            "recommendation": recommendation,
            "confidence_score": 65,  # Lower confidence for fallback
            "key_highlights": pros[:2],
            "areas_for_improvement": cons[:2],
        }
    
    def extract_resume_data(
        self,
        resume_text: str
    ) -> Dict[str, any]:
        """
        Use AI to extract structured data from resume text including contact info,
        skills, experience, and education.
        
        Args:
            resume_text: Raw text extracted from resume
        
        Returns:
            Dictionary with extracted data: name, email, phone, skills, experience, education
        """
        try:
            prompt = f"""
Analyze this resume text and extract structured information.

**Resume Text:**
{resume_text[:2000]}...

**Task:**
Extract the following information and respond ONLY with valid JSON:

{{
  "name": "Full name of the candidate",
  "email": "Email address",
  "phone": "Phone number in standard format",
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "experience_years": 5,
  "education": "Highest degree and field",
  "summary": "One-sentence professional summary"
}}

**Instructions:**
1. Extract contact information from anywhere in the resume
2. For phone: normalize to digits with country code if present (e.g., "+12345678900" or "2345678900")
3. For skills: identify technical and professional skills (max 20)
4. For experience_years: calculate total years of professional experience
5. For education: provide the highest degree mentioned
6. If any field cannot be found, use null for strings or 0 for numbers
7. Be accurate and specific

Respond ONLY with valid JSON, no additional text.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract information accurately and respond only in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate and normalize
            return {
                "name": result.get("name"),
                "email": result.get("email"),
                "phone": result.get("phone"),
                "skills": result.get("skills", [])[:20],  # Max 20 skills
                "experience": max(result.get("experience_years", 0), 0),
                "education": result.get("education", "Not Specified"),
                "summary": result.get("summary", "")
            }
            
        except Exception as e:
            print(f"AI extraction error: {e}")
            return None
    
    def enhance_match_score(
        self,
        resume_text: str,
        parsed_data: Dict,
        job_requirements: Dict
    ) -> int:
        """
        Use AI to provide a more nuanced match score
        Considers context, soft skills, and implicit qualifications
        
        Returns:
            Enhanced match score (0-100)
        """
        try:
            prompt = f"""
Evaluate this candidate's match for the role of **{job_requirements.get('title', 'the applied position')}** and provide a match score.
The company is based in **India** — consider Indian industry standards.

**Job Requirements:**
- Position: {job_requirements.get('title', 'the applied position')}
- Skills/Qualifications: {', '.join(job_requirements.get('skills', []))}
- Experience: {job_requirements.get('min_experience', 0)}+ years

**Candidate:**
- Skills: {', '.join(parsed_data.get('skills', [])[:15])}
- Experience: {parsed_data.get('experience', 0)} years
- Education: {parsed_data.get('education', 'Not Specified')}

**Resume Excerpt:**
{resume_text[:400]}

Provide a match score (0-100) considering:
1. Skill/qualification alignment with the SPECIFIC role (40%)
2. Experience level match (30%)
3. Implicit qualifications from resume context (20%)
4. Education and certifications relevant to the role (10%)

IMPORTANT: Only evaluate skills relevant to the applied role. Do NOT penalize for lacking unrelated skills.

Respond ONLY with valid JSON:
{{
  "match_score": 75,
  "reasoning": "Brief explanation in one sentence"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert recruiter based in India evaluating candidates for specific roles. Respond only in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            enhanced_score = result.get("match_score", parsed_data.get('match_score', 0))
            
            # Ensure score is in valid range
            return min(max(enhanced_score, 0), 100)
            
        except Exception as e:
            print(f"Enhanced scoring error: {e}")
            # Return original match score on error
            return parsed_data.get('match_score', 0)


# Convenience function for easy integration
def analyze_resume(
    resume_text: str,
    parsed_data: Dict,
    job_requirements: Dict,
    api_key: Optional[str] = None,
    enhance_score: bool = True
) -> Dict[str, any]:
    """
    Analyze a resume and generate AI-powered insights
    
    Args:
        resume_text: Raw text from resume
        parsed_data: Structured data from parser
        job_requirements: Job requirements dict
        enhance_score: Whether to use AI to enhance the match score
    
    Returns:
        Complete analysis dictionary with pros, cons, and recommendations
    """
    analyzer = ResumeAnalyzer(api_key)
    analysis = analyzer.generate_pros_cons(resume_text, parsed_data, job_requirements)
    
    # Optionally enhance match score
    if enhance_score:
        enhanced_score = analyzer.enhance_match_score(resume_text, parsed_data, job_requirements)
        analysis['enhanced_match_score'] = enhanced_score
    
    return analysis


# Test function
def test_analyzer():
    """Test the analyzer with sample data"""
    
    sample_resume_text = """
    John Doe - Senior Software Engineer
    
    Experience:
    - 5 years at Tech Corp as Full Stack Developer
    - Built scalable microservices using Python and React
    - Led team of 4 developers
    
    Skills: Python, JavaScript, React, Node.js, AWS, Docker, PostgreSQL
    
    Education: B.S. Computer Science, Stanford University
    """
    
    sample_parsed_data = {
        'skills': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS', 'Docker', 'PostgreSQL'],
        'experience': 5,
        'education': 'Bachelor of Science in Computer Science',
        'match_score': 75
    }
    
    sample_job_requirements = {
        'skills': ['Python', 'JavaScript', 'React', 'AWS'],
        'min_experience': 3
    }
    
    print("Testing Resume Analyzer...")
    print("=" * 60)
    
    try:
        result = analyze_resume(
            sample_resume_text,
            sample_parsed_data,
            sample_job_requirements
        )
        
        print("\n Analysis Results:")
        print(f"\n Pros ({len(result['pros'])}):")
        for i, pro in enumerate(result['pros'], 1):
            print(f"  {i}. {pro}")
        
        print(f"\n Cons ({len(result['cons'])}):")
        for i, con in enumerate(result['cons'], 1):
            print(f"  {i}. {con}")
        
        print(f"\n Overall Assessment:")
        print(f"  {result['overall_assessment']}")
        
        print(f"\n Recommendation: {result['recommendation']}")
        print(f" Confidence Score: {result['confidence_score']}%")
        
        if 'enhanced_match_score' in result:
            print(f" Enhanced Match Score: {result['enhanced_match_score']}%")
        
        print("\n" + "=" * 60)
        print(" Test completed successfully!")
        
    except Exception as e:
        print(f"\n Test failed: {e}")


if __name__ == "__main__":
    test_analyzer()
