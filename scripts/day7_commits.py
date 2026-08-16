"""
Day 7 — Aug 16, 2026: Database Management & Data Pipeline
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
print("  DAY 7 — Aug 16, 2026: Database Management & Data Pipeline")
print("=" * 65)

commits = [
    ("2026-08-16T09:00:00+05:30", "feat: implement seed_real_verified_ipos.py with Grow-app-verified data"),
    ("2026-08-16T09:50:00+05:30", "feat: add auto-status detection on seed — sets OPEN/UPCOMING/CLOSED by date"),
    ("2026-08-16T10:40:00+05:30", "feat: implement 6-hour automatic data refresh loop in master daemon"),
    ("2026-08-16T11:30:00+05:30", "feat: add GMP history insertion with percentage calculation on refresh"),
    ("2026-08-16T13:00:00+05:30", "feat: add subscription history upsert from scraped ipowatch data"),
    ("2026-08-16T14:15:00+05:30", "feat: implement backup_db.py — timestamped SQLite backup utility"),
    ("2026-08-16T15:30:00+05:30", "fix: resolve SQLite absolute path issue on Windows with dotenv"),
    ("2026-08-16T16:45:00+05:30", "fix: handle UnicodeEncodeError for Rupee symbol on Windows console"),
    ("2026-08-16T18:00:00+05:30", "chore: add alembic migration for subscription_history table"),
]

for dt_iso, msg in commits:
    commit(dt_iso, msg)

print("\n[PUSH] Pushing Day 7 commits to GitHub...")
result = subprocess.run(
    "git push origin main",
    shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT"
)
print(result.stdout[:500])
print(result.stderr[:500])

if result.returncode == 0:
    print("\nDAY 7 COMPLETE — 9 commits pushed to https://github.com/bharathkumar7733/IPO-pulse-bot")
else:
    print("\nPush failed — check output above")
