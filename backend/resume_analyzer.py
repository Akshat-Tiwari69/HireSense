"""
AI Resume Analyzer Module
Uses OpenAI API to generate intelligent pros/cons analysis for candidate resumes
"""

import os
import json
from openai import OpenAI
from typing import Dict, List, Optional, Tuple


class ResumeAnalyzer:
    """
    AI-powered resume analyzer using OpenAI's GPT models
    Generates pros, cons, and enhanced match analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Resume Analyzer
        
        Args:
            api_key: OpenAI API key (if not provided, reads from environment)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter"
            )
        
        self.client = OpenAI(api_key=self.api_key)
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
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert HR analyst and technical recruiter with 15+ years of experience. "
                            "Your role is to evaluate candidate resumes objectively and provide actionable insights. "
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
        
        prompt = f"""
Analyze this candidate's resume for a technical position and provide a detailed evaluation.

**Job Requirements:**
- Required Skills: {required_skills}
- Minimum Experience: {min_experience} years
- Role Type: Software Engineering / Technical Position

**Candidate Profile:**
- Skills: {skills_str}
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
1. Pros: Focus on demonstrated skills, relevant experience, and strong qualifications (3-5 points)
2. Cons: Be constructive, identify skill gaps or concerns (2-4 points, don't be overly negative)
3. Overall Assessment: Balanced summary considering both strengths and weaknesses
4. Recommendation: Base on overall fit for the role
5. Confidence Score: Your confidence in this assessment (0-100)
6. Be specific and evidence-based, avoid generic statements
7. Consider technical skills, experience level, and cultural fit indicators

Respond ONLY with valid JSON, no additional text.
"""
        return prompt
    
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
                f"Possesses {len(parsed_data.get('skills', []))} technical skills",
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
        
        required_skills = set(s.lower() for s in job_requirements.get('skills', []))
        candidate_skills = set(s.lower() for s in skills)
        matching_skills = required_skills.intersection(candidate_skills)
        missing_skills = required_skills - candidate_skills
        
        # Generate pros
        pros = []
        if len(skills) >= 10:
            pros.append(f"Demonstrates broad technical expertise with {len(skills)} identified skills")
        if experience >= job_requirements.get('min_experience', 0):
            pros.append(f"Meets experience requirement with {experience} years in the field")
        if matching_skills:
            pros.append(f"Strong alignment with required skills: {', '.join(list(matching_skills)[:3])}")
        if education and education != "Not Specified":
            pros.append(f"Educational background: {education}")
        if match_score >= 70:
            pros.append(f"High match score of {match_score}% indicates strong qualification fit")
        
        # Generate cons
        cons = []
        if experience < job_requirements.get('min_experience', 0):
            cons.append(f"Experience level ({experience} years) below requirement ({job_requirements.get('min_experience', 0)} years)")
        if missing_skills:
            cons.append(f"Missing some required skills: {', '.join(list(missing_skills)[:3])}")
        if match_score < 50:
            cons.append("Match score suggests significant skill gaps that need to be addressed")
        if not cons:
            cons.append("Further assessment recommended in technical interview")
        
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
            "fallback_mode": True  # Indicate this was generated without AI
        }
    
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
Evaluate this candidate's match for a technical role and provide a match score.

**Job Requirements:**
- Skills: {', '.join(job_requirements.get('skills', []))}
- Experience: {job_requirements.get('min_experience', 0)}+ years

**Candidate:**
- Skills: {', '.join(parsed_data.get('skills', [])[:15])}
- Experience: {parsed_data.get('experience', 0)} years
- Education: {parsed_data.get('education', 'Not Specified')}

**Resume Excerpt:**
{resume_text[:400]}

Provide a match score (0-100) considering:
1. Technical skill alignment (40%)
2. Experience level match (30%)
3. Implicit qualifications from resume context (20%)
4. Education and certifications (10%)

Respond ONLY with valid JSON:
{{
  "match_score": 75,
  "reasoning": "Brief explanation in one sentence"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert technical recruiter. Respond only in JSON format."},
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
        api_key: OpenAI API key (optional, reads from env if not provided)
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
        
        print("\n📊 Analysis Results:")
        print(f"\n✅ Pros ({len(result['pros'])}):")
        for i, pro in enumerate(result['pros'], 1):
            print(f"  {i}. {pro}")
        
        print(f"\n⚠️ Cons ({len(result['cons'])}):")
        for i, con in enumerate(result['cons'], 1):
            print(f"  {i}. {con}")
        
        print(f"\n📝 Overall Assessment:")
        print(f"  {result['overall_assessment']}")
        
        print(f"\n🎯 Recommendation: {result['recommendation']}")
        print(f"💯 Confidence Score: {result['confidence_score']}%")
        
        if 'enhanced_match_score' in result:
            print(f"📈 Enhanced Match Score: {result['enhanced_match_score']}%")
        
        print("\n" + "=" * 60)
        print("✅ Test completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nMake sure to set OPENAI_API_KEY environment variable:")
        print("  export OPENAI_API_KEY='your-api-key-here'")


if __name__ == "__main__":
    test_analyzer()
