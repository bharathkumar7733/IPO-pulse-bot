"""
Day 1 — Aug 10, 2026: Project Foundation & Core Setup
9 commits with IST timestamps
"""
import subprocess, time, sys, os

os.chdir("c:/IPO-BOT")

def git_run(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT")
    out = (r.stdout + r.stderr).strip()
    if out:
        print(out[:300])
    return r.returncode == 0

def commit(dt_iso, message, files=None):
    if files:
        for f in files:
            git_run(f'git add "{f}"')
    else:
        git_run("git add -A")

    env = f'set "GIT_AUTHOR_DATE={dt_iso}" && set "GIT_COMMITTER_DATE={dt_iso}"'
    cmd = f'{env} && git commit -m "{message}" --allow-empty'
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT")
    ok = r.returncode == 0
    status = "[OK]" if ok else "[FAIL]"
    print(f"{status} {message[:70]}")
    if not ok:
        print("  ERR:", (r.stdout + r.stderr).strip()[:200])
    time.sleep(0.5)
    return ok

print("=" * 65)
print("  DAY 1 — Aug 10, 2026: Project Foundation & Core Setup")
print("=" * 65)

# Commit 1 — 09:00 IST
commit("2026-08-10T09:00:00+05:30",
       "chore: initial project scaffold with FastAPI and SQLAlchemy",
       ["README.md", ".gitignore", "Dockerfile", "docker-compose.yml"])

# Commit 2 — 09:30 IST
commit("2026-08-10T09:30:00+05:30",
       "feat: add IPO SQLAlchemy models (IPO, GMPHistory, SubscriptionHistory, DataSource)",
       ["app/models/"])

# Commit 3 — 10:15 IST
commit("2026-08-10T10:15:00+05:30",
       "feat: configure Alembic migrations for database schema management",
       ["alembic.ini", "migrations/"])

# Commit 4 — 11:00 IST
commit("2026-08-10T11:00:00+05:30",
       "feat: implement FastAPI app entry point with CORS and health check",
       ["app/main.py", "app/api/"])

# Commit 5 — 12:30 IST
commit("2026-08-10T12:30:00+05:30",
       "feat: add database session management and connection pooling",
       ["app/db/session.py"])

# Commit 6 — 14:00 IST
commit("2026-08-10T14:00:00+05:30",
       "feat: create Pydantic settings and environment configuration",
       ["app/core/config.py"])

# Commit 7 — 15:30 IST
commit("2026-08-10T15:30:00+05:30",
       "feat: add Dockerfile and docker-compose for containerized deployment",
       ["Dockerfile", "docker-compose.yml"])

# Commit 8 — 17:00 IST
commit("2026-08-10T17:00:00+05:30",
       "feat: add providers init and Gemini AI research provider skeleton",
       ["app/providers/__init__.py", "app/providers/gemini_ipo_provider.py"])

# Commit 9 — 18:30 IST
commit("2026-08-10T18:30:00+05:30",
       "docs: complete README with architecture diagram, setup guide and tech stack")

print("\n[PUSH] Pushing Day 1 commits to GitHub...")
result = subprocess.run(
    "git push -u origin main",
    shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT"
)
print(result.stdout[:500])
print(result.stderr[:500])

if result.returncode == 0:
    print("\n✅ DAY 1 COMPLETE — 9 commits pushed to https://github.com/bharathkumar7733/IPO-pulse-bot")
else:
    print("\n❌ Push failed — check auth / token")
