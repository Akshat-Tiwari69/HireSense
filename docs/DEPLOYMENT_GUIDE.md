# Deployment Guide

How HireSense is built, deployed, and operated in production. Host-level setup
(users, Caddy, systemd, secrets, the public demo) is covered step by step in
[deploy/README.md](../deploy/README.md); this guide explains the overall shape
and the day-to-day release flow.

---

## Production Topology

```
Browser ──HTTPS──▶ Caddy ──┬── static files: compiled React app (frontend/dist)
                           └── /api, /socket.io ──▶ Gunicorn (1 eventlet worker, 127.0.0.1:5000)
                                                        │
                                                        ├── PostgreSQL (Supabase pooler, TLS verify-full)
                                                        ├── OpenAI (optional, deterministic fallbacks)
                                                        ├── Resend or SMTP (email)
                                                        └── Piston code runner (disabled in production)
```

- **Host:** a single 1-vCPU VPS shared with other sites.
- **Frontend:** built with `npm run build` and served directly by Caddy. There is
  no Node process in production.
- **Backend:** `hiresense.service` runs
  `gunicorn --worker-class eventlet --workers 1 app:app_with_socketio`. One worker
  is deliberate: Socket.IO room state lives in that process.
- **Database:** Supabase PostgreSQL through its IPv4 pooler. The runtime connects
  as the restricted `hiresense_app` role; schema changes use a separate
  administrator URL that the service never receives.
- **Uploads:** resumes and proctoring screenshots are written to the private
  directory `/var/lib/hiresense/uploads` (`UPLOAD_FOLDER`), never a public path.
- **Secrets:** `/etc/hiresense/hiresense.env` (`0600`, root-owned).

The systemd unit, Caddy site, and deployment scripts live in [`deploy/`](../deploy/).

---

## Release Flow

1. A pull request runs the **Quality and deploy** workflow
   (`.github/workflows/quality-and-deploy.yml`):
   - backend: `ruff check backend`, `pytest`, `python database/validate_schema.py`,
     and a syntax check of the deploy scripts (Python 3.12)
   - frontend: `npm ci` and `npm run check` (tests, lint, dead-code check, build) on Node 24
2. Merging to `main` runs the same checks. When both pass, the `deploy` job
   connects over SSH as the restricted `hiresense-deploy` account and runs
   `deploy <commit-sha>`.
3. On the host, `/usr/local/sbin/deploy-hiresense` builds an immutable release
   under `/opt/hiresense/releases`, switches `/opt/hiresense/current` atomically,
   restarts the service, waits for `/api/health/ready`, and rolls back if the new
   release does not become ready.

Automatic deploys ship application code only. Changes to Caddy, systemd units,
the deployment command, or the database schema are separate administrator
installs (see [deploy/README.md](../deploy/README.md)). In particular, the
deploy script does not install `deploy/Caddyfile.hiresense`: after a change to
it (for example the CSP), copy it to `/etc/caddy/sites.d/hiresense.caddy`,
validate, and reload Caddy by hand.

---

## Database Changes

Run migrations by hand from an administrator shell with both
`DATABASE_ADMIN_URL` and the runtime `DATABASE_URL` set:

```bash
# Fresh, empty database
python backend/scripts/run_migration.py --schema

# Existing HireSense database
python backend/scripts/run_migration.py --reconcile
```

In production the runner requires the administrator URL. It also creates or
rotates the `hiresense_app` login, installs RLS policies and the limited grants,
and verifies the role. See [database/README.md](../database/README.md) for the
schema contract and [DATABASE.md](DATABASE.md) for the data model.

### First Staff Accounts

Create the first admin, interviewer, and proctor with the seeder, then manage
everyone else from the Admin Dashboard:

```bash
SEED_ADMIN_PASSWORD=... SEED_INTERVIEWER_PASSWORD=... SEED_PROCTOR_PASSWORD=... \
  python database/seed_users.py --db-url "$DATABASE_ADMIN_URL"
```

Any password variable you leave out is generated and printed once.

---

## Production Environment

The full list of variables is in `backend/.env.example`; [SETUP.md](SETUP.md)
describes them. Production must set at least:

| Variable | Value / purpose |
|----------|-----------------|
| `APP_ENV` | `production` (enables the strict startup checks) |
| `DATABASE_URL` | `hiresense_app` pooler URL with `sslmode=verify-full` and `sslrootcert` |
| `JWT_SECRET_KEY` | Random secret, 32+ characters |
| `FRONTEND_URL` / `CORS_ORIGINS` | The public site origin |
| `TRUST_PROXY_HOPS` | `1` (Caddy) |
| `UPLOAD_FOLDER` | `/var/lib/hiresense/uploads` |
| `ALLOW_INSECURE_DEV_SECRET` / `ALLOW_RUNTIME_ENV_MUTATION` | `false` |
| `DB_POOL_MIN` / `DB_POOL_MAX` | `1` / `8` |
| `CODE_RUNNER_ENABLED` | `false` until an isolated Piston runner is available |

Optional: `OPENAI_API_KEY`, `RESEND_API_KEY` or `SMTP_*`, `REDIS_URL` (shared
rate-limit storage), `DEMO_MODE`.

Generate a JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## Health Checks

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Liveness. Returns `{"status": "ok", "demo_mode": <bool>}` |
| `GET /api/health/ready` | Readiness. Checks PostgreSQL; returns `503` with `"database": "unavailable"` when it is unreachable, and reports `code_runner: enabled/disabled` |

Logs go to the systemd journal: `journalctl -u hiresense.service`.

---

## Known Limitations

- **Code runner:** the ARM host has no safe Piston runtime, so technical
  assessments (with a coding section) cannot be scheduled in production.
- **TURN:** WebRTC uses public STUN servers only. Proctor video can fail across
  restrictive or symmetric NAT networks until a TURN server is added.
- **Single worker:** scaling out needs a shared Socket.IO message queue and
  sticky sessions before adding Gunicorn workers or hosts.

---

## Other Platforms

`backend/Procfile`, `backend/nixpacks.toml`, and `backend/runtime.txt` are left
over from an earlier Railway setup. They are not used or tested by the current
deployment, and `nixpacks.toml` still pins Python 3.11 while `runtime.txt` and
CI use 3.12. If you deploy to a PaaS, run the same Gunicorn command, serve
`frontend/dist` as static files with `/api` and `/socket.io` proxied to the
backend (or set `VITE_API_BASE_URL` at build time), use a persistent private
volume for `UPLOAD_FOLDER`, and apply the same environment rules as above.

---

## Related Documentation

- [deploy/README.md](../deploy/README.md) — host installation and the public demo
- [SETUP.md](SETUP.md) — local development and environment variables
- [ARCHITECTURE.md](ARCHITECTURE.md) — system design
- [database/README.md](../database/README.md) — schema contract and migrations
