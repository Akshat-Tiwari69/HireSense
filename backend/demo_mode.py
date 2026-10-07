"""
Public demo mode.

DEMO_MODE=true turns a deployment into a shareable sandbox: visitors can sign in
as a seeded demo account per role, and outgoing email is recorded in email_logs
instead of being delivered. Never enable it on a deployment holding real
candidate data — every visitor gets staff access to whatever is in the database.
"""

import os

# Seeded by database/seed_demo.py. Visitors pick a role; the password is never used.
DEMO_ACCOUNTS = {
    'admin': 'demo.admin@hiresense.demo',
    'interviewer': 'demo.interviewer@hiresense.demo',
    'proctor': 'demo.proctor@hiresense.demo',
}


def demo_mode_enabled():
    return os.environ.get('DEMO_MODE', '').strip().lower() == 'true'
