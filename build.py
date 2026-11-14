#!/usr/bin/env python3
"""Builds blog.jtmaui.com from Markdown.

posts/YYYY-MM-DD-slug.md  -> site/posts/slug/index.html
pages/about.md            -> site/about/index.html
static/*                  -> site/
Each .md starts with a header block:
---
title: My title
date: 2026-12-12
summary: One line for the home page
---
Raw HTML (e.g. a SmugMug embed) can go straight into the Markdown.
"""
import html, re, shutil, datetime
from pathlib import Path
import markdown

ROOT = Path(__file__).parent
OUT = ROOT / "site"
SITE_TITLE = "Jeff's Journal"
SITE_URL = "https://blog.jtmaui.com"
TAGLINE = "Travel notes and photos"

def parse(path):
    text = path.read_text(encoding="utf-8")
    meta, body = {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        body = m.group(2)
    meta["html"] = markdown.markdown(body, extensions=["extra", "sane_lists"])
    return meta

def page(title, content, depth):
    up = "../" * depth
    t = html.escape(title)
    full = t if title == SITE_TITLE else f"{t} · {SITE_TITLE}"
    year = datetime.date.today().year
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{full}</title>
<link rel="stylesheet" href="{up}style.css">
<link rel="alternate" type="application/rss+xml" title="{SITE_TITLE}" href="{up}feed.xml">
</head>
<body>
<header class="site">
  <a class="brand" href="{up}">{SITE_TITLE}</a>
  <nav><a href="{up}">Posts</a><a href="https://photos.jtmaui.com">Photos</a><a href="{up}about/">About</a></nav>
</header>
<main>
{content}
</main>
<footer class="site">© {year} Jeff · <a href="{up}feed.xml">RSS</a></footer>
</body>
</html>
"""

def fmt_date(d):
    try:
        return datetime.date.fromisoformat(d).strftime("%B %-d, %Y")
    except Exception:
        return d

def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for f in (ROOT / "static").iterdir():
        if f.is_file():
            shutil.copy(f, OUT / f.name)
        else:
            shutil.copytree(f, OUT / f.name)

    posts = []
    for f in sorted((ROOT / "posts").glob("*.md")):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", f.name)
        if not m:
            continue
        meta = parse(f)
        if meta.get("draft", "").lower() in ("true", "yes"):
            continue
        meta.setdefault("date", m.group(1))
        meta["slug"] = m.group(2)
        meta.setdefault("title", meta["slug"].replace("-", " ").title())
        posts.append(meta)
    posts.sort(key=lambda p: p["date"], reverse=True)

    for p in posts:
        d = OUT / "posts" / p["slug"]
        d.mkdir(parents=True)
        body = (f'<article class="post">\n<p class="date">{fmt_date(p["date"])}</p>\n'
                f'<h1>{html.escape(p["title"])}</h1>\n{p["html"]}\n</article>\n'
                f'<p class="back"><a href="../../">← All posts</a></p>')
        (d / "index.html").write_text(page(p["title"], body, 2), encoding="utf-8")

    items = "\n".join(
        f'<li><a href="posts/{p["slug"]}/"><span class="date">{fmt_date(p["date"])}</span>'
        f'<span class="title">{html.escape(p["title"])}</span>'
        + (f'<span class="summary">{html.escape(p["summary"])}</span>' if p.get("summary") else "")
        + "</a></li>" for p in posts) or "<li>No posts yet.</li>"
    home = (f'<section class="intro"><h1>{SITE_TITLE}</h1><p>{TAGLINE}</p></section>\n'
            f'<ul class="posts">\n{items}\n</ul>')
    (OUT / "index.html").write_text(page(SITE_TITLE, home, 0), encoding="utf-8")

    for f in (ROOT / "pages").glob("*.md"):
        meta = parse(f)
        d = OUT / f.stem
        d.mkdir()
        body = f'<article class="post"><h1>{html.escape(meta.get("title", f.stem.title()))}</h1>\n{meta["html"]}</article>'
        (d / "index.html").write_text(page(meta.get("title", f.stem.title()), body, 1), encoding="utf-8")

    rss = "\n".join(
        f"<item><title>{html.escape(p['title'])}</title><link>{SITE_URL}/posts/{p['slug']}/</link>"
        f"<guid>{SITE_URL}/posts/{p['slug']}/</guid><pubDate>{datetime.date.fromisoformat(p['date']).strftime('%a, %d %b %Y 00:00:00 GMT')}</pubDate>"
        f"<description>{html.escape(p.get('summary', ''))}</description></item>" for p in posts[:20])
    (OUT / "feed.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{SITE_TITLE}</title>'
        f"<link>{SITE_URL}</link><description>{TAGLINE}</description>\n{rss}\n</channel></rss>\n", encoding="utf-8")
    print(f"Built {len(posts)} post(s) into {OUT}")

if __name__ == "__main__":
    main()
