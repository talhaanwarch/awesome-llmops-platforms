"""Build README.md from data/projects.toml and live GitHub data.

Reads the curated list, fetches stars, license, archived status and last-push
date for every repo from the GitHub REST API, and renders one table per
category, sorted by stars (highest first).

Usage:
    GITHUB_TOKEN=... python scripts/build_readme.py

Only the standard library is used, so the GitHub Action needs no install step.
The script exits non-zero without writing anything if any repo cannot be
fetched, so a renamed or deleted repo shows up as a failed run, not a
silently shorter list.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import tomllib
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "projects.toml"
TEMPLATE_FILE = ROOT / "scripts" / "README.template.md"
README_FILE = ROOT / "README.md"

# A repo with no push for this many days is shown as inactive.
INACTIVE_AFTER_DAYS = 365


def fetch_repo(full_name: str, token: str | None) -> dict:
    """Return the GitHub API record for one repo. Follows renames."""
    req = urllib.request.Request(f"https://api.github.com/repos/{full_name}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "awesome-llmops-platforms-builder")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def format_stars(n: int) -> str:
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def anchor(title: str) -> str:
    """GitHub's heading anchor: lowercase, drop punctuation, spaces to hyphens."""
    return re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")


def render_row(p: dict, gh: dict, today: dt.date) -> str:
    name = gh["full_name"]
    label = name.split("/")[1]
    pushed = dt.date.fromisoformat(gh["pushed_at"][:10])

    notes = []
    if gh["archived"]:
        notes.append("archived")
    elif (today - pushed).days > INACTIVE_AFTER_DAYS:
        notes.append("inactive")
    note = f" *({', '.join(notes)})*" if notes else ""

    spdx = (gh.get("license") or {}).get("spdx_id")
    license_ = p.get("license") or (spdx if spdx not in (None, "NOASSERTION") else "unknown")
    if p.get("source_available"):
        license_ += " †"

    desc = p["desc"].replace("|", "/")
    homepage = (p.get("homepage") or "").strip()
    site = f" ([site]({homepage}))" if homepage else ""
    return (
        f"| {format_stars(gh['stargazers_count'])} | [{label}](https://github.com/{name}){site}{note} "
        f"| {desc} | {license_} | {pushed.isoformat()} |"
    )


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    data = tomllib.loads(DATA_FILE.read_text())
    categories = data["category"]

    all_repos = [p["repo"] for c in categories for p in c["projects"]]
    dupes = {r for r in all_repos if all_repos.count(r) > 1}
    if dupes:
        print(f"Duplicate repos in {DATA_FILE.name}: {sorted(dupes)}", file=sys.stderr)
        return 1

    def safe_fetch(repo: str):
        try:
            return repo, fetch_repo(repo, token), None
        except urllib.error.HTTPError as e:
            return repo, None, f"HTTP {e.code}"
        except urllib.error.URLError as e:
            return repo, None, str(e.reason)

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(safe_fetch, all_repos))

    failed = [(r, err) for r, gh, err in results if err]
    if failed:
        for repo, err in failed:
            print(f"Could not fetch {repo}: {err}", file=sys.stderr)
        return 1
    github = {r: gh for r, gh, _ in results}

    today = dt.date.today()
    toc, sections = [], []
    for cat in categories:
        rows = sorted(cat["projects"], key=lambda p: -github[p["repo"]]["stargazers_count"])
        title = f"{cat['name']}"
        toc.append(f"- [{title}](#{anchor(title)}) ({len(rows)})")
        sections += [
            f"## {title}",
            "",
            cat["blurb"],
            "",
            "| Stars | Project | Description | License | Last push |",
            "|---:|---|---|---|---|",
            *[render_row(p, github[p["repo"]], today) for p in rows],
            "",
        ]

    readme = (
        TEMPLATE_FILE.read_text()
        .replace("{{COUNT}}", str(len(all_repos)))
        .replace("{{UPDATED}}", today.isoformat())
        .replace("{{TOC}}", "\n".join(toc))
        .replace("{{SECTIONS}}", "\n".join(sections).rstrip() + "\n")
    )
    README_FILE.write_text(readme)
    print(f"Wrote {README_FILE.name}: {len(all_repos)} projects in {len(categories)} categories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
