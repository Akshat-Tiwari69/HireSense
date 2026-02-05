"""
Candidate-Job Matching Module
Automatically matches candidates to job postings based on skills and experience
"""

import json
import logging
from typing import Dict, List, Tuple, Optional
from db_config import get_connection, return_connection

logger = logging.getLogger(__name__)


class CandidateJobMatcher:
    """
    Handles automatic matching of candidates to job postings based on:
    - Required skills vs candidate skills
    - Preferred skills vs candidate skills
    - Experience requirements vs candidate experience
    """
    
    def __init__(self):
        pass
    
    def calculate_match_score(
        self,
        candidate_skills: List[str],
        candidate_experience: int,
        required_skills: List[str],
        preferred_skills: List[str],
        min_experience: int
    ) -> Tuple[float, Dict]:
        """
        Calculate matching score between a candidate and a job posting
        
        Args:
            candidate_skills: List of candidate's skills
            candidate_experience: Years of experience
            required_skills: List of required skills for the job
            preferred_skills: List of preferred skills for the job
            min_experience: Minimum years of experience required
        
        Returns:
            Tuple of (match_score, matching_details)
            match_score: 0-100 score
            matching_details: Dictionary with detailed breakdown
        """
        # Normalize skills to lowercase for case-insensitive matching
        candidate_skills_lower = [s.lower().strip() for s in candidate_skills if s]
        required_skills_lower = [s.lower().strip() for s in required_skills if s]
        preferred_skills_lower = [s.lower().strip() for s in preferred_skills if s]
        
        # Calculate required skills match
        required_skills_matched = 0
        matched_required = []
        missing_required = []
        
        for req_skill in required_skills_lower:
            if req_skill in candidate_skills_lower:
                required_skills_matched += 1
                matched_required.append(req_skill)
            else:
                missing_required.append(req_skill)
        
        required_skills_total = len(required_skills_lower)
        required_match_percentage = (
            (required_skills_matched / required_skills_total * 100)
            if required_skills_total > 0
            else 100  # If no required skills, consider it 100% match
        )
        
        # Calculate preferred skills match
        preferred_skills_matched = 0
        matched_preferred = []
        
        for pref_skill in preferred_skills_lower:
            if pref_skill in candidate_skills_lower:
                preferred_skills_matched += 1
                matched_preferred.append(pref_skill)
        
        preferred_skills_total = len(preferred_skills_lower)
        preferred_match_percentage = (
            (preferred_skills_matched / preferred_skills_total * 100)
            if preferred_skills_total > 0
            else 100  # If no preferred skills, consider it 100% match
        )
        
        # Calculate experience match
        experience_match = candidate_experience >= min_experience if min_experience else True
        
        # Calculate experience score (0-100)
        if experience_match:
            experience_score = 100
        elif min_experience > 0:
            experience_score = max(0, (candidate_experience / min_experience * 100))
        else:
            experience_score = 0
        
        # Calculate overall match score
        # Weights: Required skills (60%), Preferred skills (20%), Experience (20%)
        match_score = (
            required_match_percentage * 0.6 +
            preferred_match_percentage * 0.2 +
            experience_score * 0.2
        )
        
        # Build detailed matching information
        matching_details = {
            'required_skills_matched': required_skills_matched,
            'required_skills_total': required_skills_total,
            'required_match_percentage': round(required_match_percentage, 2),
            'matched_required_skills': matched_required,
            'missing_required_skills': missing_required,
            'preferred_skills_matched': preferred_skills_matched,
            'preferred_skills_total': preferred_skills_total,
            'preferred_match_percentage': round(preferred_match_percentage, 2),
            'matched_preferred_skills': matched_preferred,
            'experience_match': experience_match,
            'candidate_experience': candidate_experience,
            'min_experience_required': min_experience,
            'experience_score': round(experience_score, 2)
        }
        
        return round(match_score, 2), matching_details
    
    def match_candidate_to_jobs(self, candidate_id: int) -> List[Dict]:
        """
        Match a single candidate to all active job postings
        
        Args:
            candidate_id: ID of the candidate to match
        
        Returns:
            List of matching results with scores
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get candidate details
            cursor.execute("""
                SELECT parsed_skills, parsed_skills_json, years_experience
                FROM candidates
                WHERE id = %s
            """, (candidate_id,))
            
            candidate_row = cursor.fetchone()
            if not candidate_row:
                logger.error(f"Candidate {candidate_id} not found")
                return []
            
            # Parse candidate skills - try JSON first, fallback to text
            candidate_skills = []
            if candidate_row[1]:  # parsed_skills_json
                try:
                    candidate_skills = json.loads(candidate_row[1]) if isinstance(candidate_row[1], str) else candidate_row[1]
                except:
                    pass
            
            if not candidate_skills and candidate_row[0]:  # parsed_skills
                try:
                    candidate_skills = json.loads(candidate_row[0])
                except:
                    candidate_skills = [s.strip() for s in candidate_row[0].split(',') if s.strip()]
            
            candidate_experience = candidate_row[2] or 0
            
            # Get all active job postings
            cursor.execute("""
                SELECT id, title, required_skills, required_skills_json,
                       preferred_skills_json, min_experience, sector_id, department
                FROM job_descriptions
                WHERE status = 'active' OR status IS NULL
            """)
            
            jobs = cursor.fetchall()
            matches = []
            
            for job in jobs:
                job_id = job[0]
                title = job[1]
                
                # Parse required skills
                required_skills = []
                if job[3]:  # required_skills_json
                    try:
                        required_skills = json.loads(job[3]) if isinstance(job[3], str) else job[3]
                    except:
                        pass
                
                if not required_skills and job[2]:  # required_skills (text)
                    try:
                        required_skills = json.loads(job[2])
                    except:
                        required_skills = [s.strip() for s in job[2].split(',') if s.strip()]
                
                # Parse preferred skills
                preferred_skills = []
                if job[4]:  # preferred_skills_json
                    try:
                        preferred_skills = json.loads(job[4]) if isinstance(job[4], str) else job[4]
                    except:
                        pass
                
                min_experience = job[5] or 0
                sector_id = job[6]
                department = job[7]
                
                # Calculate match score
                match_score, matching_details = self.calculate_match_score(
                    candidate_skills,
                    candidate_experience,
                    required_skills,
                    preferred_skills,
                    min_experience
                )
                
                matches.append({
                    'job_id': job_id,
                    'job_title': title,
                    'sector_id': sector_id,
                    'department': department,
                    'match_score': match_score,
                    'matching_details': matching_details
                })
            
            # Sort by match score descending
            matches.sort(key=lambda x: x['match_score'], reverse=True)
            
            return matches
            
        except Exception as e:
            logger.error(f"Error matching candidate {candidate_id} to jobs: {str(e)}")
            return []
        finally:
            if conn:
                return_connection(conn)
    
    def save_candidate_job_matches(self, candidate_id: int, matches: List[Dict]) -> bool:
        """
        Save candidate-job matching results to database
        
        Args:
            candidate_id: ID of the candidate
            matches: List of matching results from match_candidate_to_jobs
        
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Delete existing matches for this candidate
            cursor.execute("DELETE FROM candidate_job_matches WHERE candidate_id = %s", (candidate_id,))
            
            # Insert new matches
            for match in matches:
                details = match['matching_details']
                cursor.execute("""
                    INSERT INTO candidate_job_matches (
                        candidate_id, job_id, match_score,
                        required_skills_matched, required_skills_total,
                        preferred_skills_matched, preferred_skills_total,
                        experience_match, matching_details
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    candidate_id,
                    match['job_id'],
                    match['match_score'],
                    details['required_skills_matched'],
                    details['required_skills_total'],
                    details['preferred_skills_matched'],
                    details['preferred_skills_total'],
                    details['experience_match'],
                    json.dumps(details)
                ))
            
            # Update candidate's auto_matched_job_id with best match
            if matches:
                best_match = matches[0]
                cursor.execute("""
                    UPDATE candidates
                    SET auto_matched_job_id = %s, match_confidence = %s
                    WHERE id = %s
                """, (best_match['job_id'], best_match['match_score'], candidate_id))
            
            conn.commit()
            logger.info(f"Saved {len(matches)} job matches for candidate {candidate_id}")
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error saving matches for candidate {candidate_id}: {str(e)}")
            return False
        finally:
            if conn:
                return_connection(conn)
    
    def auto_match_all_candidates(self) -> Dict[str, int]:
        """
        Automatically match all candidates to active job postings
        
        Returns:
            Dictionary with statistics (candidates_processed, matches_created)
        """
        conn = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            
            # Get all candidate IDs
            cursor.execute("SELECT id FROM candidates")
            candidate_ids = [row[0] for row in cursor.fetchall()]
            
            candidates_processed = 0
            total_matches_created = 0
            
            for candidate_id in candidate_ids:
                matches = self.match_candidate_to_jobs(candidate_id)
                if self.save_candidate_job_matches(candidate_id, matches):
                    candidates_processed += 1
                    total_matches_created += len(matches)
            
            logger.info(f"Auto-matched {candidates_processed} candidates, created {total_matches_created} matches")
            
            return {
                'candidates_processed': candidates_processed,
                'matches_created': total_matches_created
            }
            
        except Exception as e:
            logger.error(f"Error in auto_match_all_candidates: {str(e)}")
            return {'candidates_processed': 0, 'matches_created': 0}
        finally:
            if conn:
                return_connection(conn)
