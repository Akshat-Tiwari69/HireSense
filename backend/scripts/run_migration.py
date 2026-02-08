"""Run the job postings / sectors / RBAC migration."""
import os
import sys
import psycopg2

db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

migration_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "database", "migrations",
    "add_job_postings_sectors_rbac.sql"
)

with open(migration_path, "r") as f:
    sql = f.read()

print("Connecting to database...")
conn = psycopg2.connect(db_url)
conn.autocommit = False
cur = conn.cursor()

try:
    print("Running migration...")
    cur.execute(sql)
    conn.commit()
    print("Migration completed successfully!")

    # Verify new tables
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' "
        "AND table_name IN ('sectors','candidate_job_matches','audit_log','sector_email_configs') "
        "ORDER BY table_name"
    )
    tables = [r[0] for r in cur.fetchall()]
    print(f"Verified new tables: {tables}")

    # Check sectors seeded
    cur.execute("SELECT COUNT(*) FROM sectors")
    count = cur.fetchone()[0]
    print(f"Sectors seeded: {count}")

    # Verify new columns on job_descriptions
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'job_descriptions' "
        "AND column_name IN ('sector_id','status','preferred_skills','salary_range',"
        "'employment_type','experience_level','closes_at','created_by','max_experience') "
        "ORDER BY column_name"
    )
    cols = [r[0] for r in cur.fetchall()]
    print(f"New job_descriptions columns: {cols}")

    # Verify new columns on users
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' "
        "AND column_name IN ('sector_id','permissions') "
        "ORDER BY column_name"
    )
    ucols = [r[0] for r in cur.fetchall()]
    print(f"New users columns: {ucols}")

    # Verify new columns on candidates
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'candidates' "
        "AND column_name IN ('parsed_skills_json','best_match_job_id','sector_id') "
        "ORDER BY column_name"
    )
    ccols = [r[0] for r in cur.fetchall()]
    print(f"New candidates columns: {ccols}")

except Exception as e:
    conn.rollback()
    print(f"Migration FAILED: {e}")
    sys.exit(1)
finally:
    cur.close()
    conn.close()
