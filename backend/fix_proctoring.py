#!/usr/bin/env python
# Fix proctoring_enabled column issue

with open('db_helpers.py', 'r') as f:
    content = f.read()

# Remove sa.proctoring_enabled from SELECT
content = content.replace(
    "sa.status, sa.assessment_id, sa.started_at, sa.proctoring_enabled,",
    "sa.status, sa.assessment_id, sa.started_at,"
)

# Fix the return dict to set proctoring_enabled to True and fix row indexes
old_return = """'started_at': row[6],
                'proctoring_enabled': row[7],
                'candidate_name': row[8],
                'candidate_email': row[9]"""

new_return = """'started_at': row[6],
                'proctoring_enabled': True,
                'candidate_name': row[7],
                'candidate_email': row[8]"""

content = content.replace(old_return, new_return)

with open('db_helpers.py', 'w') as f:
    f.write(content)

print('✓ Fixed get_assessment_by_token() - removed sa.proctoring_enabled')
