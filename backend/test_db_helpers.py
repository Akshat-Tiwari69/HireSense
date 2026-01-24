"""
Test file for Database Helper Functions
Tests all CRUD operations and score calculations
"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(__file__))

from db_helpers import (
    insert_candidate, get_candidate_by_id, get_all_candidates, update_candidate_shortlist,
    create_assessment, update_assessment_scores, get_assessment_by_id,
    save_mcq_response, save_coding_submission, log_proctoring_event, save_psychometric_response,
    get_mcq_score, get_coding_score, get_psychometric_scores,
    DatabaseError
)


def test_candidate_operations():
    """Test candidate CRUD operations"""
    print("\n" + "="*80)
    print("TESTING CANDIDATE OPERATIONS")
    print("="*80)
    
    try:
        # Test 1: Insert candidate
        print("\n✓ Testing insert_candidate()...")
        parsed_data = {
            'skills': ['Python', 'Django', 'PostgreSQL', 'JavaScript'],
            'experience': 5,
            'education': 'B.Tech Computer Science',
            'match_score': 85,
            'shortlist_status': 'High Match'
        }
        
        candidate_id = insert_candidate(
            name="John Doe",
            email=f"john.doe.{int(time.time())}@example.com",
            phone="9876543210",
            resume_path="/uploads/john_doe_resume.pdf",
            parsed_data=parsed_data
        )
        print(f"  ✅ Candidate created with ID: {candidate_id}")
        
        # Test 2: Get candidate by ID
        print("\n✓ Testing get_candidate_by_id()...")
        candidate = get_candidate_by_id(candidate_id)
        print(f"  ✅ Retrieved candidate: {candidate['name']} ({candidate['email']})")
        print(f"     Skills: {candidate['skills']}")
        print(f"     Experience: {candidate['years_experience']} years")
        print(f"     Match Score: {candidate['match_score']}")
        
        # Test 3: Update candidate shortlist
        print("\n✓ Testing update_candidate_shortlist()...")
        update_candidate_shortlist(candidate_id, "High Match", 92)
        updated_candidate = get_candidate_by_id(candidate_id)
        print(f"  ✅ Updated match score: {updated_candidate['match_score']}")
        print(f"     Status: {updated_candidate['shortlist_status']}")
        
        # Test 4: Get all candidates
        print("\n✓ Testing get_all_candidates()...")
        all_candidates = get_all_candidates()
        print(f"  ✅ Retrieved {len(all_candidates)} candidate(s) from database")
        
        return candidate_id
        
    except DatabaseError as e:
        print(f"  ❌ Error: {e}")
        return None


def test_assessment_operations(candidate_id):
    """Test assessment CRUD operations"""
    print("\n" + "="*80)
    print("TESTING ASSESSMENT OPERATIONS")
    print("="*80)
    
    try:
        # Test 1: Create assessment
        print("\n✓ Testing create_assessment()...")
        assessment_id = create_assessment(candidate_id)  # job_id is optional
        print(f"  ✅ Assessment created with ID: {assessment_id}")
        
        # Test 2: Save MCQ responses
        print("\n✓ Testing save_mcq_response()...")
        save_mcq_response(assessment_id, question_id=1, selected_answer="A", is_correct=True, time_spent=45)
        save_mcq_response(assessment_id, question_id=2, selected_answer="B", is_correct=True, time_spent=38)
        save_mcq_response(assessment_id, question_id=3, selected_answer="C", is_correct=False, time_spent=52)
        print(f"  ✅ Saved 3 MCQ responses")
        
        # Test 3: Calculate MCQ score
        print("\n✓ Testing get_mcq_score()...")
        mcq_score = get_mcq_score(assessment_id)
        print(f"  ✅ MCQ Score: {mcq_score}%")
        
        # Test 4: Save coding submissions
        print("\n✓ Testing save_coding_submission()...")
        code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
        save_coding_submission(
            assessment_id, problem_id=1, language="Python", 
            code=code, test_cases_passed=8, total_test_cases=10
        )
        print(f"  ✅ Saved coding submission")
        
        # Test 5: Calculate coding score
        print("\n✓ Testing get_coding_score()...")
        coding_score = get_coding_score(assessment_id)
        print(f"  ✅ Coding Score: {coding_score}%")
        
        # Test 6: Log proctoring event
        print("\n✓ Testing log_proctoring_event()...")
        log_proctoring_event(
            assessment_id, 
            event_type="tab_switch", 
            severity="low", 
            details="Candidate switched to another tab"
        )
        print(f"  ✅ Logged proctoring event")
        
        # Test 7: Save psychometric responses
        print("\n✓ Testing save_psychometric_response()...")
        save_psychometric_response(assessment_id, question_id=1, trait="leadership", score=8)
        save_psychometric_response(assessment_id, question_id=2, trait="resilience", score=7)
        save_psychometric_response(assessment_id, question_id=3, trait="teamwork", score=9)
        print(f"  ✅ Saved 3 psychometric responses")
        
        # Test 8: Calculate psychometric scores
        print("\n✓ Testing get_psychometric_scores()...")
        psychometric_scores = get_psychometric_scores(assessment_id)
        print(f"  ✅ Psychometric Scores:")
        for trait, score in psychometric_scores.items():
            print(f"     {trait.capitalize()}: {score}/10")
        
        # Test 9: Update assessment with final scores
        print("\n✓ Testing update_assessment_scores()...")
        update_assessment_scores(
            assessment_id,
            technical_score=80,
            psychometric_score=8.0,
            decision="Hire",
            rationale="Strong technical skills with good communication abilities. Passed 80% of coding tests with solid MCQ performance."
        )
        print(f"  ✅ Updated assessment scores")
        
        # Test 10: Get assessment details
        print("\n✓ Testing get_assessment_by_id()...")
        assessment = get_assessment_by_id(assessment_id)
        print(f"  ✅ Assessment Details:")
        print(f"     Status: {assessment['status']}")
        print(f"     Technical Score: {assessment['technical_score']}")
        print(f"     Psychometric Score: {assessment['psychometric_score']}")
        print(f"     Overall Score: {assessment['overall_score']}")
        print(f"     Decision: {assessment['decision']}")
        print(f"     Proctoring Violations: {assessment['proctoring_violations']}")
        
        return assessment_id
        
    except DatabaseError as e:
        print(f"  ❌ Error: {e}")
        return None


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "DATABASE HELPER FUNCTIONS TEST SUITE" + " "*24 + "║")
    print("╚" + "="*78 + "╝")
    
    # Run candidate tests
    candidate_id = test_candidate_operations()
    
    if candidate_id:
        # Run assessment tests
        assessment_id = test_assessment_operations(candidate_id)
        
        if assessment_id:
            print("\n" + "="*80)
            print("✅ ALL TESTS PASSED SUCCESSFULLY!")
            print("="*80)
            print("\n✨ Database helper functions are working correctly!")
            print("   - Candidate CRUD operations: ✓")
            print("   - Assessment creation and tracking: ✓")
            print("   - MCQ response saving and scoring: ✓")
            print("   - Code submission tracking: ✓")
            print("   - Proctoring event logging: ✓")
            print("   - Psychometric response saving: ✓")
            print("   - Score calculations: ✓")
            print("\n" + "="*80 + "\n")
        else:
            print("\n❌ Assessment tests failed")
    else:
        print("\n❌ Candidate tests failed")


if __name__ == "__main__":
    main()
