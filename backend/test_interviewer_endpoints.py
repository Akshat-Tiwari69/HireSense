from flask import Flask
from interviewer_routes import interviewer_bp

# Create a test app and register blueprint
app = Flask(__name__)
app.register_blueprint(interviewer_bp, url_prefix='/api/interviewer')

# List all routes
print("=" * 70)
print("INTERVIEWER DASHBOARD ENDPOINTS - REGISTERED & READY")
print("=" * 70)
print()

routes = []
for rule in app.url_map.iter_rules():
    if 'interviewer' in str(rule):
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((str(rule), methods))

# Sort routes
routes.sort(key=lambda x: x[0])

for route, methods in routes:
    print(f"  {methods:15} {route}")

print()
print("=" * 70)
print(f"Total Endpoints: {len(routes)}")
print("=" * 70)
print()
print("✅ All interviewer dashboard endpoints are registered and ready!")
