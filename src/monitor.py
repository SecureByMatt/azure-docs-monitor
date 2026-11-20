"""Monitor selected official Microsoft Learn pages for visible documentation changes.

This is a documentation-change monitor, NOT a notification of released Azure features.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources.json"
STATE = ROOT / "state" / "pages.json"
HEADERS = {"User-Agent": "AzureDocsMonitor/1.0 (documentation change detection)"}


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_lines(html: str) -> list[str]:
    """Extract article text while excluding menus, code samples and UI chrome."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.select_one("main#main, main, article, #main")
    if main is None:
        raise ValueError("Microsoft Learn article container not found; page layout may have changed")
    for el in main.select("nav, aside, footer, script, style, button, form, pre, code, .feedback-section, .metadata"):  # type: ignore[union-attr]
        el.decompose()
    lines = []
    for tag in main.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        if tag.name == "li" and tag.find_parent("li") is not None:
            continue
        t = normalize(tag.get_text(" ", strip=True))
        if len(t) >= 12 and (not lines or lines[-1] != t):
            lines.append(t)
    if len(lines) < 5:
        raise ValueError("Too little article content extracted; refusing to replace saved baseline")
    return lines


def digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def get_page(session: requests.Session, url: str) -> list[str]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "learn.microsoft.com":
        raise ValueError(f"Untrusted source URL: {url}")
    for attempt in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
            r.raise_for_status()
            if urlparse(r.url).hostname != "learn.microsoft.com":
                raise ValueError("Source redirected outside Microsoft Learn")
            return extract_lines(r.text)
        except (requests.RequestException, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def additions(old: list[str], new: list[str]) -> tuple[list[str], list[str]]:
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    plus, minus = [], []
    for op, a1, a2, b1, b2 in sm.get_opcodes():
        if op in ("insert", "replace"):
            plus.extend(new[b1:b2])
        if op in ("delete", "replace"):
            minus.extend(old[a1:a2])
    return plus, minus


def preview_text(lines: list[str], max_len: int = 750) -> str:
    if not lines:
        return "No added content detected; wording may have been removed or reordered."
    result = ""
    for line in lines:
        candidate = (result + "\n• " + line).strip()
        if len(candidate) > max_len:
            break
        result = candidate
    return result or ("• " + lines[0][:max_len - 5] + "…")


def embed_for(source: dict, old: list[str], new: list[str]) -> dict:
    plus, minus = additions(old, new)
    return {
        "title": f"{source['category']}: Documentation updated",
        "url": source["url"],
        "description": f"**{source['name']}**\nMicrosoft Learn article text has changed. Review the linked page before applying operational changes.",
        "color": 3447003,
        "fields": [
            {"name": "Added or revised text (excerpt)", "value": preview_text(plus), "inline": False},
            {"name": "Change summary", "value": f"{len(plus)} added/revised paragraphs; {len(minus)} removed/revised paragraphs", "inline": False},
        ],
        "footer": {"text": "Documentation change only — not necessarily a new Azure feature"},
    }


def notify(webhook: str, embeds: list[dict], session: requests.Session) -> None:
    # One batch of at most three embeds, keeping below Discord's total embed text limit.
    for i in range(0, len(embeds), 3):
        payload = {
            "username": "Azure Docs Watch (DEV)",
            "content": "📘 **Microsoft Learn documentation changes detected**",
            "embeds": embeds[i:i + 3],
        }
        for attempt in range(4):
            response = session.post(webhook, json=payload, timeout=20)
            if response.status_code == 429 and attempt < 3:
                wait = min(float(response.headers.get("Retry-After", "2")), 30)
                time.sleep(max(wait, 1))
                continue
            response.raise_for_status()
            break
        if i + 3 < len(embeds):
            time.sleep(1)


def run(preview: bool) -> int:
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    proposed = dict(state)
    changed = []
    session = requests.Session()

    # Fetch every source successfully before saving state or posting notifications.
    for source in sources:
        url = source["url"]
        lines = get_page(session, url)
        key = hashlib.sha256(url.encode()).hexdigest()[:20]
        previous = state.get(key)
        new_hash = digest(lines)
        if previous is None:
            print(f"BASELINE: {source['name']}")
        elif previous["sha256"] != new_hash:
            print(f"CHANGED: {source['name']}")
            changed.append(embed_for(source, previous["lines"], lines))
        else:
            print(f"UNCHANGED: {source['name']}")
        proposed[key] = {"name": source["name"], "url": url, "sha256": new_hash, "lines": lines}

    print(f"Summary: {len(sources)} articles checked, {len(changed)} changes detected.")
    if preview:
        print(json.dumps({"preview": True, "embeds": changed}, indent=2, ensure_ascii=False))
        print("Preview: no webhook posts or state changes.")
        return 0

    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if changed and webhook:
        notify(webhook, changed, session)
    elif changed:
        print("WARNING: changes detected but DISCORD_WEBHOOK_URL is not set. Refusing to advance state.", file=sys.stderr)
        return 2

    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(proposed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview", action="store_true", help="Display results without webhook delivery or state writes")
    args = parser.parse_args()
    try:
        raise SystemExit(run(preview=args.preview))
    except Exception as ex:
        print(f"ERROR: {type(ex).__name__}: {ex}", file=sys.stderr)
        raise SystemExit(1)
