# Database Schema and Code Fixes

## Issues Found and Fixed

### 1. **Missing `proctoring_enabled` Column** ❌ → ✅
- **Issue**: The code was trying to fetch a non-existent `proctoring_enabled` column from `scheduled_assessments`
- **Location**: `db_helpers.py::get_assessment_by_token()` (line 1262)
- **Fix**: 
  - Removed the column from the SELECT query
  - Set `proctoring_enabled` to `True` by default in the returned dict
  - This prevents 500 errors when verifying assessment tokens

### 2. **Wrong Table Name: `proctoring_events` vs `proctoring_violations`** ❌ → ✅
- **Issue**: Database has `proctoring_violations` table, but code tried to use `proctoring_events`
- **Affected Functions**:
  - `record_proctoring_violation()` (line 1356)
  - `get_violations_for_assessment()` (line 1385)
  - `count_violations_for_assessment()` (line 1433)
- **Fix**: Updated all queries to use `proctoring_violations` table
- **Note**: The schema file previously defined `proctoring_events` - this was removed as database uses `proctoring_violations`

### 3. **SQL Placeholder Syntax Error** ❌ → ✅
- **Issue**: Code used SQLite placeholders (`?`) instead of PostgreSQL placeholders (`%s`)
- **Affected Queries**:
  - `start_assessment_by_token()` - UPDATE query (line 1323)
  - `record_proctoring_violation()` - INSERT query (line 1364)
  - `get_violations_for_assessment()` - SELECT query (line 1397)
  - `count_violations_for_assessment()` - SELECT query (line 1440)
- **Fix**: Changed all `?` to `%s` for PostgreSQL compatibility

### 4. **Non-existent `resolved` Column** ❌ → ✅
- **Issue**: Code tried to fetch a `resolved` column that doesn't exist in `proctoring_violations`
- **Location**: `get_violations_for_assessment()` (line 1397)
- **Fix**: Removed `resolved` from the SELECT and from the returned dict

### 5. **React Hook Order Violation** ❌ → ✅
- **File**: `frontend/src/pages/AssessmentPage.jsx`
- **Issue**: `useEffect` hook was called inside a conditional `if (submitted)` block, violating React's Rules of Hooks
- **Fix**: 
  - Moved the auto-redirect `useEffect` to the top level of the component
  - Added `if (!submitted) return;` guard at the start of the effect to skip execution when not submitted
  - This prevents "Rendered more hooks than during the previous render" errors

## Database Structure Summary

### Actual Tables in Supabase
```
- assessments (3 rows)
- candidates (3 rows)
- coding_submissions (0 rows)
- email_logs (23 rows)
- job_descriptions (3 rows)
- mcq_responses (0 rows)
- proctoring_events (0 rows) - Legacy/alternative table
- proctoring_violations (4 rows) - ✅ PRIMARY VIOLATIONS TABLE
- psychometric_responses (0 rows)
- questions (0 rows)
- scheduled_assessments (1 row)
- users (3 rows)
```

### Key Columns in `scheduled_assessments`
```sql
- id (INTEGER)
- candidate_id (INTEGER)
- interviewer_id (INTEGER)
- scheduled_time (TIMESTAMP)
- status (TEXT)
- assessment_id (INTEGER)
- access_token (VARCHAR)
- started_at (TIMESTAMP)
- is_streaming (BOOLEAN)
- stream_started_at (TIMESTAMP)
- stream_ended_at (TIMESTAMP)
```

**Note**: No `proctoring_enabled` or `completed_at` columns exist.

### Key Columns in `proctoring_violations`
```sql
- id (INTEGER)
- assessment_id (INTEGER)
- violation_type (TEXT)
- description (TEXT)
- screenshot_url (TEXT)
- timestamp (TIMESTAMP)
- severity (TEXT)
```

**Note**: No `resolved` column exists.

## Files Modified

1. **`backend/db_helpers.py`**
   - Fixed `get_assessment_by_token()` to not query non-existent column
   - Fixed `start_assessment_by_token()` placeholder syntax
   - Fixed `record_proctoring_violation()` placeholder syntax
   - Fixed `get_violations_for_assessment()` - removed non-existent column
   - Fixed `count_violations_for_assessment()` placeholder syntax

2. **`database/schema_postgres.sql`**
   - Updated to match actual Supabase structure
   - Removed `proctoring_enabled` from `scheduled_assessments`
   - Added `is_streaming`, `stream_started_at`, `stream_ended_at` to `scheduled_assessments`
   - Updated `proctoring_violations` table definition with actual columns
   - Kept `proctoring_events` for legacy compatibility

3. **`frontend/src/pages/AssessmentPage.jsx`**
   - Fixed React hook order violation
   - Moved auto-redirect effect out of conditional block
   - Added guard clause to skip effect when not needed

## Testing

✅ All fixes verified against actual Supabase database structure
✅ No Python syntax errors in db_helpers.py
✅ No React errors in AssessmentPage.jsx (0 errors confirmed)

## Next Steps

1. Restart the backend with `DATABASE_URL` set to Supabase
2. Test the assessment verification endpoint: `GET /api/interviewee/assessment/verify/{token}`
3. Test violation reporting: `POST /api/interviewee/assessment/{id}/violation`
4. Verify assessment submission flow works end-to-end
