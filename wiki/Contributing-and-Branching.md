# Contributing and Branching

## Branch Strategy
- `main`: production-stable
- `dev`: integration branch for active work

## Contribution Flow
1. Branch from `dev`
2. Implement scoped changes
3. Run checks
4. Open PR to `dev` (or to `main` per release process)

## Recommended Validation
- Frontend: `npm run check`
- Backend: `pytest`, `ruff check .`, `python -m compileall -q .`

## Documentation Rule
If behavior or contracts change, update docs in `/docs` and relevant wiki pages.
