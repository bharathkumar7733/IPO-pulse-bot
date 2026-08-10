import httpx, json, sys

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html, */*",
}

urls_to_try = [
    ("NSE IPO allotment", "https://www.nseindia.com/api/ipo-current-allotment"),
    ("IPO Notify v2 open", "https://iponotify.me/api/v2/ipo/open"),
    ("IPO Notify ipos", "https://iponotify.me/api/ipos"),
    ("IPO Notify status open", "https://iponotify.me/api/ipos?status=open"),
    ("StockAnalysis IPO", "https://stockanalysis.com/api/ipo/upcoming/"),
]

with httpx.Client(follow_redirects=True, timeout=15) as c:
    for name, url in urls_to_try:
        try:
            r = c.get(url, headers=headers)
            ct = r.headers.get("content-type", "")
            print(f"{name}: Status {r.status_code}, CT: {ct[:60]}")
            if r.status_code == 200 and "json" in ct:
                print("  Preview:", str(r.json())[:300])
        except Exception as e:
            print(f"{name}: ERROR {e}")
