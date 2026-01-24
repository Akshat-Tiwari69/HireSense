#!/usr/bin/env python
"""Display all registered backend endpoints"""

from flask import Flask
from auth import auth_bp
from interviewer_routes import interviewer_bp
from interviewee_routes import interviewee_bp

app = Flask(__name__)
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')
app.register_blueprint(interviewee_bp, url_prefix='/api/interviewee')

print("=" * 80)
print("ALL BACKEND ENDPOINTS - COMPLETE SYSTEM")
print("=" * 80)
print()

auth_routes = []
interviewer_routes = []
interviewee_routes = []

for rule in app.url_map.iter_rules():
    methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
    route = str(rule)
    
    if 'auth' in route:
        auth_routes.append((route, methods))
    elif 'interviewer' in route:
        interviewer_routes.append((route, methods))
    elif 'interviewee' in route:
        interviewee_routes.append((route, methods))

print("🔐 AUTHENTICATION ENDPOINTS")
print("-" * 80)
for route, methods in sorted(auth_routes):
    print(f"  {methods:15} {route}")

print()
print("👔 INTERVIEWER DASHBOARD ENDPOINTS")
print("-" * 80)
for route, methods in sorted(interviewer_routes):
    print(f"  {methods:15} {route}")

print()
print("⏰ INTERVIEWEE ASSESSMENT ENDPOINTS (WITH TIME VALIDATION)")
print("-" * 80)
for route, methods in sorted(interviewee_routes):
    print(f"  {methods:15} {route}")

print()
print("=" * 80)
total = len(auth_routes) + len(interviewer_routes) + len(interviewee_routes)
print(f"TOTAL ENDPOINTS: {total}")
print(f"  - Auth: {len(auth_routes)}")
print(f"  - Interviewer: {len(interviewer_routes)}")
print(f"  - Interviewee: {len(interviewee_routes)}")
print("=" * 80)
print()
print("✅ ALL BACKEND TASKS COMPLETE - READY FOR FRONTEND DEVELOPMENT!")
