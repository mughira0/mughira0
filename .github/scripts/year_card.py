"""Builds assets/year-stats.svg: GitHub stats for the current year only."""
import datetime as dt
import json
import os
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]

now = dt.datetime.now(dt.timezone.utc)
year = now.year
query = """
query($u: String!, $f: DateTime!, $t: DateTime!) {
  user(login: $u) {
    contributionsCollection(from: $f, to: $t) {
      totalCommitContributions
      totalPullRequestContributions
      totalPullRequestReviewContributions
      totalIssueContributions
      restrictedContributionsCount
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""
body = json.dumps({
    "query": query,
    "variables": {"u": USER, "f": f"{year}-01-01T00:00:00Z", "t": now.strftime("%Y-%m-%dT%H:%M:%SZ")},
}).encode()
req = urllib.request.Request(
    "https://api.github.com/graphql", data=body,
    headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
)
c = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]
cal = c["contributionCalendar"]

today = now.date().isoformat()
days = [d for w in cal["weeks"] for d in w["contributionDays"] if d["date"] <= today]
counts = [d["contributionCount"] for d in days]

longest = run = 0
for n in counts:
    run = run + 1 if n else 0
    longest = max(longest, run)

current = 0
i = len(counts) - 1
if i >= 0 and counts[i] == 0:  # today not started yet: don't break the streak
    i -= 1
while i >= 0 and counts[i]:
    current += 1
    i -= 1

active = sum(1 for n in counts if n)
best = max(days, key=lambda d: d["contributionCount"]) if days else None
best_label = (
    f'{best["contributionCount"]} on {dt.date.fromisoformat(best["date"]).strftime("%b %d")}'
    if best and best["contributionCount"] else "n/a"
)

fmt = "{:,}".format
rows = [
    ("Total contributions", fmt(cal["totalContributions"])),
    ("Private contributions", fmt(c["restrictedContributionsCount"])),
    ("Public commits", fmt(c["totalCommitContributions"])),
    ("Pull requests", fmt(c["totalPullRequestContributions"])),
    ("Active days", f"{active} / {len(counts)}"),
    ("Current streak", f"{current} days"),
    ("Longest streak", f"{longest} days"),
    ("Busiest day", best_label),
]

W, H = 495, 210
out = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
    "<style>",
    ".t{font:600 18px 'Segoe UI',Ubuntu,Sans-Serif;fill:#70a5fd}",
    ".l{font:600 13px 'Segoe UI',Ubuntu,Sans-Serif;fill:#38bdae}",
    ".v{font:700 13px 'Segoe UI',Ubuntu,Sans-Serif;fill:#c0caf5}",
    ".s{font:italic 11px 'Segoe UI',Ubuntu,Sans-Serif;fill:#565f89}",
    "</style>",
    f'<rect width="{W}" height="{H}" rx="6" fill="#1a1b27"/>',
    f'<text x="25" y="36" class="t">Mughira\'s {year} Stats ⚡</text>',
]
for idx, (label, value) in enumerate(rows):
    col, r = divmod(idx, 4)
    x = 25 + col * 235
    y = 72 + r * 30
    out.append(f'<text x="{x}" y="{y}" class="l">{label}:</text>')
    out.append(f'<text x="{x + 215}" y="{y}" class="v" text-anchor="end">{value}</text>')
out.append(f'<text x="25" y="{H - 14}" class="s">This year only. We don\'t talk about last year.</text>')
out.append("</svg>")

os.makedirs("assets", exist_ok=True)
with open("assets/year-stats.svg", "w", encoding="utf-8") as f:
    f.write("\n".join(out) + "\n")
print("\n".join(f"{l}: {v}" for l, v in rows))
