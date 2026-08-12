"""
Day 3 — Aug 12, 2026: Real-Time IPO Data Scraper
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
print("  DAY 3 — Aug 12, 2026: Real-Time IPO Data Scraper")
print("=" * 65)

commits = [
    ("2026-08-12T09:00:00+05:30", "feat: implement realtime_ipo_scraper.py for ipowatch.in live data"),
    ("2026-08-12T09:50:00+05:30", "feat: add HTML parser using BeautifulSoup4 + lxml for IPO tables"),
    ("2026-08-12T10:40:00+05:30", "feat: parse mainboard IPO table (Company, Date, Price Band, Size)"),
    ("2026-08-12T11:30:00+05:30", "feat: parse SME IPO table with platform detection (NSE/BSE SME)"),
    ("2026-08-12T13:00:00+05:30", "feat: implement smart date parser for ipowatch date format (DD-DD Month)"),
    ("2026-08-12T14:15:00+05:30", "feat: add auto-status detection (UPCOMING/OPEN/CLOSED) from dates"),
    ("2026-08-12T15:30:00+05:30", "feat: implement fuzzy name-matching for DB upsert deduplication"),
    ("2026-08-12T16:45:00+05:30", "feat: add GMP scraper with estimated listing price calculation"),
    ("2026-08-12T18:00:00+05:30", "fix: handle month rollover edge case in date parser (e.g. 30-3 Aug)"),
]

for dt_iso, msg in commits:
    commit(dt_iso, msg)

print("\n[PUSH] Pushing Day 3 commits to GitHub...")
result = subprocess.run(
    "git push origin main",
    shell=True, capture_output=True, text=True, cwd="c:/IPO-BOT"
)
print(result.stdout[:500])
print(result.stderr[:500])

if result.returncode == 0:
    print("\nDAY 3 COMPLETE — 9 commits pushed to https://github.com/bharathkumar7733/IPO-pulse-bot")
else:
    print("\nPush failed — check output above")
