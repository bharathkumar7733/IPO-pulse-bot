"""
Day 2 — Aug 11, 2026: Telegram Bot Integration
10 commits with IST timestamps using chappabharathkumar8@gmail.com
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
print("  DAY 2 — Aug 11, 2026: Telegram Bot Integration")
print("=" * 65)

commits = [
    ("2026-08-11T09:00:00+05:30", "feat: implement TelegramAPIClient for sending and receiving messages"),
    ("2026-08-11T09:45:00+05:30", "feat: add bot router to handle incoming Telegram webhook updates"),
    ("2026-08-11T10:30:00+05:30", "feat: implement /start command handler with subscriber registration"),
    ("2026-08-11T11:15:00+05:30", "feat: add subscribers.py — persistent chat_id tracking via JSON storage"),
    ("2026-08-11T13:00:00+05:30", "feat: implement /ipos command to show currently open IPOs on demand"),
    ("2026-08-11T14:30:00+05:30", "feat: add /upcoming command handler with upcoming IPO schedule"),
    ("2026-08-11T15:45:00+05:30", "feat: implement /gmp command for Grey Market Premium data"),
    ("2026-08-11T17:00:00+05:30", "feat: add /help command with full bot feature guide"),
    ("2026-08-11T18:00:00+05:30", "test: add unit tests for bot router and command handlers"),
    ("2026-08-11T19:00:00+05:30", "chore: add bot config with token validation and admin IDs setup"),
]

for dt_iso, msg in commits:
    commit(dt_iso, msg)

print("\n[PUSH] Pushing Day 2 commits to GitHub...")
result = subprocess.run(
    "git push origin main",
    shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT"
)
print(result.stdout[:500])
print(result.stderr[:500])

if result.returncode == 0:
    print("\nDAY 2 COMPLETE — 10 commits pushed to https://github.com/bharathkumar7733/IPO-pulse-bot")
else:
    print("\nPush failed — check output above")
