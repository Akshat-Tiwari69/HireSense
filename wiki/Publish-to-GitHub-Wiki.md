# Publish to GitHub Wiki

This repository now includes a complete wiki source set in `/wiki`.

## Pages Included
- Home.md
- Getting-Started.md
- System-Architecture.md
- API-Reference.md
- Database-Schema.md
- Roles-and-Permissions.md
- Assessment-and-Proctoring.md
- Deployment-Guide.md
- Security-and-Operations.md
- Troubleshooting.md
- Contributing-and-Branching.md

## How to Publish to GitHub Wiki
Because the GitHub Wiki is a separate repository, publish by syncing these files into your wiki repository.

### Option A: Manual (Web UI)
1. Open the repository wiki in GitHub.
2. Create each page using the same filename/page title.
3. Paste content from matching files in `/wiki`.
4. Set `Home.md` content as the wiki home page.

### Option B: Git-based sync (local machine)
1. Clone wiki repo: `https://github.com/Akshat-Tiwari69/HireSense.wiki.git`
2. Copy all files from `/wiki` into the wiki repo root.
3. Commit and push.

## Maintenance
Treat `/wiki` as canonical source in the main repository so wiki updates can be reviewed in PRs.
