#!/usr/bin/env python3
"""Builds the Boring Weather static site from posts/*.md into _site/.

Post file: posts/YYYY-MM-DD.md

    title: Warm through Saturday, cooler Sunday
    issued: 5:44 AM CDT
    source: https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD
    alert: false
    alert_url:
    ---
    First paragraph.

    ## Optional heading

    Another paragraph.

Set `alert: true` and `alert_url` when any watch or warning is in effect.
Standard library only.
"""
import datetime
import email.utils
import html
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parent
POSTS = ROOT / "posts"
STATIC = ROOT / "static"
OUT = ROOT / "_site"
BASE = "https://boringweather.com"
NAME = "Boring Weather"
TAGLINE = "Minnesota forecast. Just the forecast."
DEFAULT_SOURCE = "https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD"

CSS = """
:root { --bg:#fff; --fg:#1a1a1a; --muted:#666; --rule:#e2e2e2; --alert:#b3261e; --link:#0b57d0; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#111; --fg:#e8e8e8; --muted:#9a9a9a; --rule:#2c2c2c; --alert:#f2b8b5; --link:#8ab4f8; }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin:0; background:var(--bg); color:var(--fg);
  font:18px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main, header, footer { max-width:38rem; margin:0 auto; padding:0 16px; }
header { padding-top:32px; padding-bottom:16px; border-bottom:1px solid var(--rule); }
header a { color:var(--fg); text-decoration:none; }
.name { font-size:1.1rem; font-weight:700; letter-spacing:.01em; }
.tag { color:var(--muted); font-size:.9rem; margin:2px 0 0; }
main { padding-top:24px; padding-bottom:24px; }
h1 { font-size:1.5rem; line-height:1.25; margin:.2em 0 .3em; }
h2 { font-size:1.1rem; margin:1.6em 0 .2em; }
.meta { color:var(--muted); font-size:.85rem; margin:0 0 1.2em; }
p { margin:0 0 1em; }
a { color:var(--link); }
.alert { border-left:4px solid var(--alert); padding:8px 12px; margin:0 0 1.4em; }
.alert strong { color:var(--alert); }
.source { color:var(--muted); font-size:.9rem; }
ul.archive { list-style:none; padding:0; margin:0; }
ul.archive li { padding:6px 0; border-bottom:1px solid var(--rule); }
ul.archive time { color:var(--muted); font-size:.85rem; display:inline-block; min-width:7.5em; }
section.archive-wrap { margin-top:2.2em; }
footer { padding-top:16px; padding-bottom:40px; border-top:1px solid var(--rule);
  color:var(--muted); font-size:.85rem; }
"""


def esc(s):
    return html.escape(s, quote=True)


def parse(path):
    text = path.read_text(encoding="utf-8")
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise ValueError(f"{path.name}: missing '---' line between header and body")
    meta = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    date = datetime.date.fromisoformat(path.stem)
    if not meta.get("title"):
        raise ValueError(f"{path.name}: missing title")
    return {
        "date": date,
        "title": meta["title"],
        "issued": meta.get("issued", ""),
        "source": meta.get("source") or DEFAULT_SOURCE,
        "alert": meta.get("alert", "").lower() in ("true", "yes", "1"),
        "alert_url": meta.get("alert_url", ""),
        "body": body.strip(),
    }


def long_date(d):
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def url_for(d):
    return f"/{d.year:04d}/{d.month:02d}/{d.day:02d}/"


def render_body(body):
    out = []
    for block in body.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            out.append(f"<h2>{esc(block[3:].strip())}</h2>")
        else:
            out.append(f"<p>{esc(' '.join(block.split()))}</p>")
    return "\n".join(out)


def render_post(p, heading_tag="h1", link=False):
    parts = []
    if p["alert"]:
        link_html = ""
        if p["alert_url"]:
            link_html = f' <a href="{esc(p["alert_url"])}">Read the National Weather Service alert.</a>'
        parts.append(
            '<div class="alert" role="alert"><strong>Active alert.</strong> '
            f"The National Weather Service has a watch, warning, or advisory in effect.{link_html}</div>"
        )
    title = esc(p["title"])
    if link:
        title = f'<a href="{url_for(p["date"])}">{title}</a>'
    parts.append(f"<{heading_tag}>{title}</{heading_tag}>")
    issued = f" &middot; NWS discussion issued {esc(p['issued'])}" if p["issued"] else ""
    parts.append(f'<p class="meta"><time datetime="{p["date"].isoformat()}">{long_date(p["date"])}</time>{issued}</p>')
    parts.append(render_body(p["body"]))
    parts.append(
        f'<p class="source">Source: <a href="{esc(p["source"])}">NWS Twin Cities forecast discussion</a>.</p>'
    )
    return "\n".join(parts)


def page(title, body_html, canonical, description):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE}{canonical}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="/feed.xml">
<link rel="stylesheet" href="/style.css">
</head>
<body>
<header>
<div class="name"><a href="/">{NAME}</a></div>
<p class="tag">{TAGLINE}</p>
</header>
<main>
{body_html}
</main>
<footer>
<p>{NAME} summarizes the National Weather Service Twin Cities forecast discussion. Posts are written by an AI from that text, and the source is linked on every post. For warnings and emergencies, use <a href="https://www.weather.gov/mpx/">weather.gov/mpx</a> or NOAA Weather Radio.</p>
<p><a href="/feed.xml">RSS</a></p>
</footer>
</body>
</html>
"""


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def feed(posts):
    now = email.utils.format_datetime(
        datetime.datetime.now(datetime.timezone.utc)
    )
    items = []
    for p in posts[:20]:
        dt = datetime.datetime.combine(p["date"], datetime.time(12, 0), datetime.timezone.utc)
        link = BASE + url_for(p["date"])
        items.append(
            "<item>"
            f"<title>{esc(p['title'])}</title>"
            f"<link>{link}</link>"
            f'<guid isPermaLink="true">{link}</guid>'
            f"<pubDate>{email.utils.format_datetime(dt)}</pubDate>"
            f"<description>{esc(render_body(p['body']))}</description>"
            "</item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0"><channel>'
        f"<title>{NAME}</title><link>{BASE}/</link>"
        f"<description>{esc(TAGLINE)}</description>"
        "<language>en-us</language>"
        f"<lastBuildDate>{now}</lastBuildDate>"
        + "".join(items)
        + "</channel></rss>\n"
    )


def main():
    posts = []
    if POSTS.exists():
        for path in sorted(POSTS.glob("*.md")):
            posts.append(parse(path))
    posts.sort(key=lambda p: p["date"], reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    write(OUT / "style.css", CSS.strip() + "\n")
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy(f, OUT / f.name)

    for p in posts:
        title = f"{p['title']} | {NAME}: Minnesota forecast for {long_date(p['date'])}"
        write(
            OUT / url_for(p["date"]).strip("/") / "index.html",
            page(title, render_post(p), url_for(p["date"]), p["title"]),
        )

    if posts:
        latest = posts[0]
        main_html = render_post(latest)
        if len(posts) > 1:
            rows = "\n".join(
                f'<li><time datetime="{p["date"].isoformat()}">{p["date"].strftime("%b")} {p["date"].day}, {p["date"].year}</time>'
                f'<a href="{url_for(p["date"])}">{esc(p["title"])}</a></li>'
                for p in posts[1:]
            )
            main_html += f'\n<section class="archive-wrap"><h2>Earlier forecasts</h2><ul class="archive">\n{rows}\n</ul></section>'
        desc = latest["title"]
    else:
        main_html = "<p>The first forecast is coming soon.</p>"
        desc = TAGLINE
    write(
        OUT / "index.html",
        page(f"{NAME}: Minnesota weather forecast, just the forecast", main_html, "/", desc),
    )
    write(OUT / "feed.xml", feed(posts))
    write(OUT / "404.html", page(f"Not found | {NAME}", "<h1>Not found</h1><p><a href=\"/\">Go to today's forecast.</a></p>", "/404.html", "Page not found"))
    print(f"Built {len(posts)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
