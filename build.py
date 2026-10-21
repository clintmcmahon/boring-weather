#!/usr/bin/env python3
"""Builds the Boring Weather static site from posts/*.md into _site/.

Usage: python build.py [--posts DIR]

Post file: posts/YYYY-MM-DD.md. See AUTHORING.md for the format and rules.

    title: Warm through Saturday, cooler Sunday
    issued: 5:44 AM CDT
    source: https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD
    alert: false
    alert_url:
    ---
    === Minnesota forecast
    Today :: Sunny and warmer than Tuesday.

    === Extended forecast
    | Thu | Dry | Mid 70s | Mid 50s |

Standard library only.
"""
import datetime
import email.utils
import html
import pathlib
import os
import shutil
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent
STATIC = ROOT / "static"
OUT = ROOT / "_site"
# Public address of the site. Set SITE_URL when building (the workflow does this).
# A project site lives under a path, for example https://user.github.io/repo, and
# every internal link needs that path as a prefix.
BASE = os.environ.get("SITE_URL", "https://boringweather.com").rstrip("/")
PREFIX = urllib.parse.urlparse(BASE).path.rstrip("/")
NAME = "Boring Weather"
TAGLINE = "Minnesota forecast. Just the forecast."
DEFAULT_SOURCE = "https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD"
MAX_PAGES = 5

CSS = """
@font-face { font-family:"VT323"; src:url(__PREFIX__/vt323.woff2) format("woff2"); font-display:swap; }
:root { --bg:#fff; --fg:#1a1a1a; --muted:#666; --rule:#e2e2e2; --alert:#b3261e; --link:#0b57d0; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#111; --fg:#e8e8e8; --muted:#9a9a9a; --rule:#2c2c2c; --alert:#f2b8b5; --link:#8ab4f8; }
}
* { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body { margin:0; background:var(--bg); color:var(--fg);
  font:18px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main, header, footer { max-width:42rem; margin:0 auto; padding:0 16px; }
header { padding-top:24px; padding-bottom:12px; }
header a { color:var(--fg); text-decoration:none; }
.name { font-size:1.1rem; font-weight:700; }
.tag { color:var(--muted); font-size:.9rem; margin:2px 0 0; }
main { padding-top:8px; padding-bottom:24px; }
a { color:var(--link); }
h1.post-title { font-size:1.2rem; margin:0 0 12px; }
.alert-note { border-left:4px solid var(--alert); padding:8px 12px; margin:0 0 16px; }
.alert-note strong { color:var(--alert); }
.scr { background:#1f2f9e; color:#fff; font-family:"VT323", ui-monospace, Menlo, Consolas, monospace;
  font-size:26px; line-height:1.25; text-transform:uppercase; text-shadow:2px 2px 0 #000;
  border:4px solid #0d1860; border-radius:4px; }
.scr.alert { background:#8a1c1c; border-color:#4d0d0d; }
.scr .hd, .scr .ft { background:#0d1860; display:flex; justify-content:space-between; gap:12px; padding:6px 16px; }
.scr.alert .hd, .scr.alert .ft { background:#4d0d0d; }
.scr .ft { font-size:20px; flex-wrap:wrap; }
.scr .ttl { color:#ffe500; padding:12px 16px 0; font-size:32px; }
.scr .bd { padding:6px 16px 16px; min-height:290px; }
.scr .bd p { margin:0 0 12px; }
.scr .y { color:#ffe500; }
.scr .g { display:grid; gap:6px; text-align:center; margin-top:8px; }
.scr .g div div { margin-bottom:6px; }
@media (max-width: 480px) {
  .scr { font-size:20px; }
  .scr .ttl { font-size:26px; }
  .scr .hd, .scr .bd, .scr .ttl { padding-left:10px; padding-right:10px; }
  .scr .ft { font-size:16px; }
}
.nav { display:flex; align-items:center; justify-content:center; gap:16px; margin:12px 0 0; }
.nav button { font:inherit; font-size:16px; padding:6px 14px; border:1px solid var(--rule); border-radius:6px;
  background:transparent; color:var(--fg); cursor:pointer; }
.nav button:hover { border-color:var(--muted); }
.nav span { font-size:14px; color:var(--muted); }
.meta { color:var(--muted); font-size:.85rem; margin:12px 0 0; }
.src { color:var(--muted); font-size:.9rem; margin:4px 0 0; }
.archive-wrap { margin-top:2.2em; }
.archive-wrap h2 { font-size:1.1rem; margin:0 0 .5em; }
ul.archive { list-style:none; padding:0; margin:0; }
ul.archive li { padding:6px 0; border-bottom:1px solid var(--rule); }
ul.archive time { color:var(--muted); font-size:.85rem; display:inline-block; min-width:7.5em; }
footer { padding-top:16px; padding-bottom:40px; border-top:1px solid var(--rule); color:var(--muted); font-size:.85rem; }
"""

# Collapses pages to one at a time. Without JavaScript every page stays visible.
PAGER_JS = """
(function () {
  var pg = document.querySelectorAll('.scr .pg'), n = pg.length, i = 0;
  if (n < 2) return;
  var count = document.getElementById('pn'), label = document.getElementById('pl');
  function show(k) {
    i = (k + n) % n;
    pg.forEach(function (p, j) { p.style.display = j === i ? 'block' : 'none'; });
    count.textContent = (i + 1) + '/' + n;
    label.textContent = 'Page ' + (i + 1) + ' of ' + n;
  }
  document.getElementById('pv').onclick = function () { show(i - 1); };
  document.getElementById('nx').onclick = function () { show(i + 1); };
  document.querySelector('.nav').hidden = false;
  show(0);
})();
"""


def esc(s):
    return html.escape(s, quote=True)


def parse_pages(path, body):
    pages, cur = [], None
    for raw in body.splitlines():
        s = raw.strip()
        if s.startswith("=== "):
            cur = {"title": s[4:].strip(), "items": [], "grid": []}
            pages.append(cur)
            continue
        if not s:
            continue
        if cur is None:
            raise ValueError(f"{path.name}: body must start with '=== Page title'")
        if s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) != 4:
                raise ValueError(f"{path.name}: grid rows need 4 cells (day, sky, high, low): {s}")
            cur["grid"].append(cells)
        elif " :: " in s:
            label, _, text = s.partition(" :: ")
            cur["items"].append((label.strip(), text.strip()))
        else:
            cur["items"].append(("", s))
    if not pages:
        raise ValueError(f"{path.name}: no pages found")
    if len(pages) > MAX_PAGES:
        raise ValueError(f"{path.name}: {len(pages)} pages, maximum is {MAX_PAGES}")
    for pg in pages:
        if not pg["items"] and not pg["grid"]:
            raise ValueError(f"{path.name}: page '{pg['title']}' is empty")
    return pages


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
    if not meta.get("title"):
        raise ValueError(f"{path.name}: missing title")
    alert = meta.get("alert", "").lower() in ("true", "yes", "1")
    if alert and not meta.get("alert_url"):
        raise ValueError(f"{path.name}: alert posts need alert_url")
    return {
        "date": datetime.date.fromisoformat(path.stem),
        "title": meta["title"],
        "issued": meta.get("issued", ""),
        "source": meta.get("source") or DEFAULT_SOURCE,
        "alert": alert,
        "alert_url": meta.get("alert_url", ""),
        "pages": parse_pages(path, body),
    }


def long_date(d):
    return f"{d.strftime('%A, %B')} {d.day}, {d.year}"


def short_date(d):
    return f"{d.strftime('%a %b')} {d.day}"


def path_for(d):
    return f"/{d.year:04d}/{d.month:02d}/{d.day:02d}/"


def url_for(d):
    return PREFIX + path_for(d)


def render_page(pg):
    out = ['<section class="pg">', f'<div class="ttl">{esc(pg["title"])}</div>', '<div class="bd">']
    for label, text in pg["items"]:
        lead = f'<span class="y">{esc(label)}</span> ' if label else ""
        out.append(f"<p>{lead}{esc(text)}</p>")
    if pg["grid"]:
        cols = []
        for day, sky, hi, lo in pg["grid"]:
            cols.append(
                f'<div><div class="y">{esc(day)}</div><div>{esc(sky)}</div>'
                f'<div class="y">Hi</div><div>{esc(hi)}</div>'
                f'<div class="y">Lo</div><div>{esc(lo)}</div></div>'
            )
        out.append(f'<div class="g" style="grid-template-columns:repeat({len(cols)},minmax(0,1fr))">{"".join(cols)}</div>')
    out.append("</div></section>")
    return "\n".join(out)


def render_screen(p):
    parts = []
    if p["alert"]:
        parts.append(
            '<div class="alert-note" role="alert"><strong>Active alert.</strong> '
            "The National Weather Service has a watch, warning, or advisory in effect. "
            f'<a href="{esc(p["alert_url"])}">Read the official alert.</a></div>'
        )
    cls = "scr alert" if p["alert"] else "scr"
    issued = f"Issued {esc(p['issued'])}" if p["issued"] else ""
    parts.append(f'<h1 class="post-title">{esc(p["title"])}</h1>')
    parts.append(f'<article class="{cls}" aria-label="Forecast for {long_date(p["date"])}">')
    parts.append(f'<div class="hd"><span>{NAME}</span><span>{short_date(p["date"])}</span></div>')
    parts.extend(render_page(pg) for pg in p["pages"])
    parts.append(f'<div class="ft"><span>Source: NWS Twin Cities</span><span>{issued}</span><span id="pn">1/{len(p["pages"])}</span></div>')
    parts.append("</article>")
    parts.append(
        '<div class="nav" hidden><button id="pv" type="button">Previous page</button>'
        f'<span id="pl">Page 1 of {len(p["pages"])}</span>'
        '<button id="nx" type="button">Next page</button></div>'
    )
    parts.append(
        f'<p class="src">Written by an AI from the <a href="{esc(p["source"])}">NWS Twin Cities forecast discussion</a>. '
        f'<time datetime="{p["date"].isoformat()}">{long_date(p["date"])}</time>.</p>'
    )
    return "\n".join(parts)


def page(title, body_html, canonical, description, pager=False):
    script = f"<script>{PAGER_JS}</script>" if pager else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{BASE}{canonical}">
<link rel="alternate" type="application/rss+xml" title="{NAME}" href="{PREFIX}/feed.xml">
<link rel="preload" href="{PREFIX}/vt323.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{PREFIX}/style.css">
</head>
<body>
<header>
<div class="name"><a href="{PREFIX}/">{NAME}</a></div>
<p class="tag">{TAGLINE}</p>
</header>
<main>
{body_html}
</main>
<footer>
<p>{NAME} summarizes the National Weather Service Twin Cities forecast discussion. Posts are written by an AI from that text, and the source is linked on every post. For warnings and emergencies, use <a href="https://www.weather.gov/mpx/">weather.gov/mpx</a> or NOAA Weather Radio.</p>
<p><a href="{PREFIX}/feed.xml">RSS</a></p>
</footer>
{script}
</body>
</html>
"""


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def feed_html(p):
    out = []
    for pg in p["pages"]:
        out.append(f"<h2>{esc(pg['title'])}</h2>")
        for label, text in pg["items"]:
            lead = f"<strong>{esc(label)}</strong> " if label else ""
            out.append(f"<p>{lead}{esc(text)}</p>")
        for day, sky, hi, lo in pg["grid"]:
            out.append(f"<p><strong>{esc(day)}</strong> {esc(sky)}. High {esc(hi)}, low {esc(lo)}.</p>")
    return "\n".join(out)


def feed(posts):
    now = email.utils.format_datetime(datetime.datetime.now(datetime.timezone.utc))
    items = []
    for p in posts[:20]:
        dt = datetime.datetime.combine(p["date"], datetime.time(12, 0), datetime.timezone.utc)
        link = BASE + path_for(p["date"])
        items.append(
            "<item>"
            f"<title>{esc(p['title'])}</title><link>{link}</link>"
            f'<guid isPermaLink="true">{link}</guid>'
            f"<pubDate>{email.utils.format_datetime(dt)}</pubDate>"
            f"<description>{esc(feed_html(p))}</description></item>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>'
        f"<title>{NAME}</title><link>{BASE}/</link><description>{esc(TAGLINE)}</description>"
        f"<language>en-us</language><lastBuildDate>{now}</lastBuildDate>"
        + "".join(items)
        + "</channel></rss>\n"
    )


def main():
    posts_dir = ROOT / "posts"
    if "--posts" in sys.argv:
        posts_dir = pathlib.Path(sys.argv[sys.argv.index("--posts") + 1]).resolve()
    posts = []
    if posts_dir.exists():
        for path in sorted(posts_dir.glob("*.md")):
            posts.append(parse(path))
    posts.sort(key=lambda p: p["date"], reverse=True)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    write(OUT / "style.css", CSS.replace("__PREFIX__", PREFIX).strip() + "\n")
    if STATIC.exists():
        for f in STATIC.iterdir():
            if f.is_file():
                shutil.copy(f, OUT / f.name)

    for p in posts:
        title = f"Minnesota forecast for {long_date(p['date'])} | {NAME}"
        write(
            OUT / path_for(p["date"]).strip("/") / "index.html",
            page(title, render_screen(p), path_for(p["date"]), p["title"], pager=True),
        )

    if posts:
        latest = posts[0]
        main_html = render_screen(latest)
        if len(posts) > 1:
            rows = "\n".join(
                f'<li><time datetime="{p["date"].isoformat()}">{p["date"].strftime("%b")} {p["date"].day}, {p["date"].year}</time>'
                f'<a href="{url_for(p["date"])}">{esc(p["title"])}</a></li>'
                for p in posts[1:]
            )
            main_html += f'\n<section class="archive-wrap"><h2>Earlier forecasts</h2><ul class="archive">\n{rows}\n</ul></section>'
        desc = latest["title"]
        has_pager = True
    else:
        main_html = "<p>The first forecast is coming soon.</p>"
        desc = TAGLINE
        has_pager = False
    write(
        OUT / "index.html",
        page(f"{NAME}: Minnesota weather forecast, just the forecast", main_html, "/", desc, pager=has_pager),
    )
    write(OUT / "feed.xml", feed(posts))
    write(
        OUT / "404.html",
        page(f"Not found | {NAME}", f'<h1 class="post-title">Not found</h1><p><a href="{PREFIX}/">Go to today\'s forecast.</a></p>', "/404.html", "Page not found"),
    )
    print(f"Built {len(posts)} post(s) into {OUT}")


if __name__ == "__main__":
    main()
