# HireSense production deployment

Production uses Caddy for the compiled React application and a single hardened
Gunicorn/Eventlet worker for Flask and Socket.IO. This is deliberate for the
one-vCPU host: Caddy serves static assets without a second Node process, while
the eventlet worker keeps WebSocket connections inside the same process.

The installed deployment command creates immutable releases under
`/opt/hiresense/releases`, atomically switches `/opt/hiresense/current`, checks
database readiness, and rolls back if the new backend does not become ready.
The GitHub workflow deploys only a commit on `main`, and only after backend and
frontend checks pass.

Host state:

- application secrets: `/etc/hiresense/hiresense.env` (`0600`, root:root)
- persistent private uploads: `/var/lib/hiresense/uploads`
- backend service: `hiresense.service`
- static site and reverse proxy: Caddy
- deployment command: `/usr/local/sbin/deploy-hiresense <git-sha>`

Three unprivileged principals keep the deployment boundary narrow:

- `hiresense-deploy` can only trigger the root-owned deployment command over SSH;
  it owns no code, releases, or secrets.
- `hiresense-build` owns only the Git mirror and the release currently being built.
- `hiresense` runs the backend and can write only the persistent upload directory.

Final releases are `root:hiresense`, are not writable by the service or deployment
accounts, and are validated before reuse. Caddy must be a member of the
`hiresense` group so it can read the compiled frontend. The sudoers entry for
`hiresense-deploy` must use `NOPASSWD:NOSETENV` and name only
`/usr/local/sbin/deploy-hiresense`.

This host is shared with deployments that replace `/etc/caddy/Caddyfile`.
Install `Caddyfile.root` as `/etc/caddy/Caddyfile.root`, install
`caddy-hiresense-override.conf` under
`/etc/systemd/system/caddy.service.d/`, and keep the HireSense site at
`/etc/caddy/sites.d/hiresense.caddy`. The override makes Caddy load both the
replaceable primary file and every independently managed site fragment, so one
project cannot remove another project's virtual host during a reload.
`Caddyfile.root` is the sole owner of the `sites.d` import; do not repeat that
import in the replaceable `/etc/caddy/Caddyfile`. Validate
`/etc/caddy/Caddyfile.root` after every primary-file change and before reloading
the service. It is also the sole owner of Caddy's global-options block; the
replaceable primary and site fragments must contain site blocks only.

The stable entrypoint also moves Caddy's admin API from the TCP loopback port to
`/run/caddy/admin.sock`. The service drop-in creates that runtime directory for
the `caddy` user and all reloads target the permissioned socket, preventing
unprivileged application accounts from replacing the proxy configuration.
Require Caddy 2.6.1 or newer.

Before installation, verify that `/etc/caddy`, the primary and root Caddyfiles,
`sites.d`, and every imported fragment are root-owned, non-writable by group or
others, regular paths with no symlinks. Validate the composite root file, install
the drop-in, run `systemctl daemon-reload`, and use a one-time
`systemctl restart caddy` to create the runtime directory and move the admin API
to its socket. Verify that the socket exists, TCP port 2019 is closed, and every
shared site is healthy. Subsequent changes use `systemctl reload caddy`; a direct
reload of the replaceable primary file bypasses this shared-host protection.

Production overrides must include:

```dotenv
APP_ENV=production
DATABASE_URL=postgresql://hiresense_app:URL_ENCODED_PASSWORD@POOLER_HOST:5432/postgres?sslmode=verify-full&sslrootcert=/etc/ssl/certs/supabase-prod-ca-2021.crt
FRONTEND_URL=https://hiresense.tiwaribabu.in
CORS_ORIGINS=https://hiresense.tiwaribabu.in
TRUST_PROXY_HOPS=1
UPLOAD_FOLDER=/var/lib/hiresense/uploads
ALLOW_INSECURE_DEV_SECRET=false
ALLOW_RUNTIME_ENV_MUTATION=false
DB_POOL_MIN=1
DB_POOL_MAX=8
DB_POOL_ACQUIRE_TIMEOUT_SECONDS=5
CODE_RUNNER_ENABLED=false
CODE_RUNNER_URL=
```

The runtime URL must authenticate as `hiresense_app`, not `postgres`, and must
request `sslmode=verify-full`; production startup fails closed for every weaker
mode. Install Supabase's `prod-ca-2021.crt` read-only at the configured
`sslrootcert` path and verify hostname validation on-host before cutover. The runtime
validates the connected PostgreSQL identity and refuses superuser, role-creation,
database-creation, replication, `BYPASSRLS`, inherited-role, and application-table
ownership privileges. The URL should use the IPv4-capable Supabase pooler; the
original direct database hostname is IPv6-only and is unreachable from this host.

Run migrations from an administrator shell with both `DATABASE_ADMIN_URL` and the
runtime `DATABASE_URL` set. In production the migration command requires the
separate administrator URL, creates or rotates the `hiresense_app` login from the
runtime URL password, removes role memberships, installs its RLS policies and
limited table/sequence grants, and verifies the resulting role. URL-encode reserved
characters in both connection strings. Never write either connection string to a
shell history or log.

Database migrations remain an explicit administrator operation. The runtime
service receives only the restricted Supabase application connection; automatic
deployments never receive the administrator database URL. The systemd unit also
removes `DATABASE_ADMIN_URL` even if it is accidentally left in the environment
file. Likewise, pushes to
`main` automatically deploy application releases only. Changes to Caddy,
systemd, the root-owned deployment command, or database migrations require a
separate audited administrator install.

The current ARM host has no safely working Piston runtime, so technical-assessment
scheduling is deliberately disabled while non-technical hiring remains available.
`/api/health/ready` reports `code_runner: disabled` alongside database readiness.
Do not set `CODE_RUNNER_ENABLED=true` until `CODE_RUNNER_URL` points to an isolated,
healthy runner; enabling it also requires removing the systemd safety override.

The single Eventlet worker is intentional on the one-vCPU host and preserves
in-process Socket.IO room state. Public WebRTC currently uses STUN only; a TURN
service is still required for reliable proctor video across restrictive or
symmetric NAT networks.
