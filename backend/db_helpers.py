"""
Database Helper Functions — re-export hub.

All functions now live in focused domain modules:
  user_db.py        — users and authentication
  candidate_db.py   — candidate CRUD
  assessment_db.py  — assessments, responses, scoring, scheduling, tokens
  proctoring_db.py  — proctoring events and violations
  email_db.py       — email logging

This file re-exports everything so all existing imports continue to work
without any changes to other files.
"""

from user_db import (
    DatabaseError,
    create_user,
    get_user_by_email,
    get_user_by_id,
)

from candidate_db import (
    get_candidate_by_email,
    insert_candidate,
    get_candidate_by_id,
    get_all_candidates,
    update_candidate_shortlist,
    update_candidate_status,
)

from assessment_db import (
    create_assessment,
    update_assessment_scores,
    get_assessment_by_id,
    get_assessment_by_candidate_id,
    save_mcq_response,
    get_saved_mcq_answers,
    save_psychometric_response,
    get_saved_psychometric_answers,
    save_coding_submission,
    get_saved_coding_submission,
    get_mcq_score,
    get_coding_score,
    get_psychometric_scores,
    create_scheduled_assessment,
    get_scheduled_assessment,
    get_scheduled_assessment_by_id,
    update_scheduled_assessment_status,
    check_assessment_time_valid,
    generate_assessment_token,
    set_assessment_token,
    get_assessment_by_token,
    start_assessment_by_token,
    verify_assessment_access_token,
    save_assessment_questions,
    get_assessment_questions,
    update_assessment_time_elapsed,
    get_assessment_time_elapsed,
)

from proctoring_db import (
    log_proctoring_event,
    record_proctoring_violation,
    get_violations_for_assessment,
    count_violations_for_assessment,
)

from email_db import (
    log_email,
    get_candidate_emails,
)
