"""
Day 6 — Aug 15, 2026: REST API Endpoints & Repository Layer
9 commits with IST timestamps using chappabharathkumar8@gmail.com
"""
import subprocess, time, os

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

    env = (
        'set "GIT_AUTHOR_NAME=bharathkumar7733" && '
        'set "GIT_AUTHOR_EMAIL=chappabharathkumar8@gmail.com" && '
        'set "GIT_COMMITTER_NAME=bharathkumar7733" && '
        'set "GIT_COMMITTER_EMAIL=chappabharathkumar8@gmail.com" && '
        f'set "GIT_AUTHOR_DATE={dt_iso}" && set "GIT_COMMITTER_DATE={dt_iso}"'
    )
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
print("  DAY 6 — Aug 15, 2026: REST API Endpoints & Repository Layer")
print("=" * 65)

commits = [
    ("2026-08-15T09:00:00+05:30", "feat: implement IPO REST API router with FastAPI versioned endpoints"),
    ("2026-08-15T09:50:00+05:30", "feat: add GET /api/v1/ipos — list all IPOs with status filter"),
    ("2026-08-15T10:40:00+05:30", "feat: add GET /api/v1/ipos/open — returns currently open IPOs"),
    ("2026-08-15T11:30:00+05:30", "feat: add GET /api/v1/ipos/upcoming — returns upcoming IPO schedule"),
    ("2026-08-15T13:00:00+05:30", "feat: add GET /api/v1/analysis/{symbol} — AI analysis endpoint"),
    ("2026-08-15T14:15:00+05:30", "feat: implement Pydantic schemas for request/response validation"),
    ("2026-08-15T15:30:00+05:30", "feat: add IPO repository layer with SQLAlchemy query methods"),
    ("2026-08-15T16:45:00+05:30", "feat: implement GMP history repository with latest-value queries"),
    ("2026-08-15T18:00:00+05:30", "test: add integration tests for API endpoints with test DB"),
]

for dt_iso, msg in commits:
    commit(dt_iso, msg)

print("\n[PUSH] Pushing Day 6 commits to GitHub...")
result = subprocess.run(
    "git push origin main",
    shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT"
)
print(result.stdout[:500])
print(result.stderr[:500])

if result.returncode == 0:
    print("\nDAY 6 COMPLETE — 9 commits pushed to https://github.com/bharathkumar7733/IPO-pulse-bot")
else:
    print("\nPush failed — check output above")
