#!/usr/bin/env python3
"""Submit changed page URLs to IndexNow after a push to main.

Usage: indexnow.py [--dry-run] <before-sha> <after-sha>

Derives public URLs for changed posts and pages from the git diff. A change
to shared files (layouts, includes, config, CSS) submits every URL from the
live sitemap instead. Only URLs that currently return HTTP 200 are submitted.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

SITE = "https://www.cyberpunk.tools"
HOST = "www.cyberpunk.tools"
SHARED_PREFIXES = ("_layouts/", "_includes/", "_sass/", "assets/css/", "_config.yml")
POST_RE = re.compile(r"^_posts/(\d{4}-\d{1,2}-\d{1,2})-(.*)\.[^.]+$")


def sh(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def find_key():
    for name in os.listdir("."):
        if re.fullmatch(r"[0-9a-f]{32}\.txt", name):
            return name[:-4]
    sys.exit("IndexNow key file (<32 hex chars>.txt) not found at repo root")


def front_matter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    data = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def slugify(s):
    # Jekyll's :title placeholder: slugify in "pretty" mode, case preserved.
    # Runs of characters outside [\w._~!$&'()+,;=@] become "-", ends trimmed.
    s = re.sub(r"[^\w._~!$&'()+,;=@]+", "-", s)
    return s.strip("-")


def post_url(path, text):
    m = POST_RE.match(path)
    if not m:
        return None
    fm = front_matter(text)
    date = fm.get("date", m.group(1))
    d = None
    for parse in (dt.datetime.fromisoformat,
                  lambda v: dt.datetime.strptime(v, "%Y-%m-%d %H:%M:%S %z"),
                  lambda v: dt.datetime.strptime(v, "%Y-%m-%d %H:%M %z")):
        try:
            d = parse(date)
            break
        except ValueError:
            continue
    if d is None:
        d = dt.datetime.strptime(date[:10], "%Y-%m-%d")
    if d.tzinfo:
        d = d.astimezone(dt.timezone.utc)  # GitHub Pages builds in UTC
    cats = fm.get("categories", "").split()
    slug = slugify(fm.get("slug") or m.group(2))
    parts = cats + [f"{d.year:04d}", f"{d.month:02d}", f"{d.day:02d}", f"{slug}.html"]
    return SITE + "/" + "/".join(parts)


def page_url(path, text):
    if path == "index.md":
        return SITE + "/"
    if path.endswith(".md") and "/" not in path:
        fm = front_matter(text)
        permalink = fm.get("permalink") or "/" + path[:-3] + "/"
        return SITE + permalink
    return None


def file_text(sha, path):
    try:
        out = subprocess.run(["git", "show", f"{sha}:{path}"], check=True,
                             capture_output=True).stdout
    except subprocess.CalledProcessError:
        return ""
    return out.decode("utf-8", errors="replace")


def sitemap_urls():
    with urllib.request.urlopen(SITE + "/sitemap.xml", timeout=30) as r:
        root = ET.fromstring(r.read())
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    return [loc.text.strip() for loc in root.findall(".//s:loc", ns)]


def is_live(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status == 200
    except Exception:
        return False


def main():
    args = [a for a in sys.argv[1:] if a != "--dry-run"]
    dry_run = "--dry-run" in sys.argv
    before, after = args[0], args[1]
    if set(before) == {"0"}:
        raw = sh("git", "ls-files", "-z")
    else:
        raw = sh("git", "diff", "--name-only", "-z", before, after)
    changed = [p for p in raw.split("\0") if p]
    print("changed files:", *changed, sep="\n  ")

    if any(p.startswith(SHARED_PREFIXES) for p in changed):
        urls = set(sitemap_urls())
    else:
        urls = set()
        for p in changed:
            if not (POST_RE.match(p) or (p.endswith(".md") and "/" not in p)):
                continue
            text = file_text(after, p) or file_text(before, p)
            u = post_url(p, text) or page_url(p, text)
            if u:
                urls.add(u)
        if any(POST_RE.match(p) for p in changed):
            urls.add(SITE + "/")  # the post list on the home page changed too

    live = sorted(u for u in urls if is_live(u))
    skipped = sorted(urls - set(live))
    if skipped:
        print("not live (skipped):", *skipped, sep="\n  ")
    if not live:
        print("nothing to submit")
        return

    key = find_key()
    body = json.dumps({
        "host": HOST,
        "key": key,
        "keyLocation": f"{SITE}/{key}.txt",
        "urlList": live,
    }).encode()
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"}, method="POST")
    print("submitting:", *live, sep="\n  ")
    if dry_run:
        print("dry run: not sending")
        return
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow response:", r.status)
    except urllib.error.HTTPError as e:
        sys.exit(f"IndexNow rejected the request: {e.code} {e.read().decode(errors='replace')}")


if __name__ == "__main__":
    main()
