# Boring Weather

Minnesota forecast. Just the forecast. Live at https://boringweather.com.

A static site built from `posts/YYYY-MM-DD.md` by `build.py` (Python standard library only). Pushing to `main` builds and deploys to GitHub Pages through `.github/workflows/pages.yml`.

## Post format

```
title: Warm through Saturday, cooler Sunday
issued: 5:44 AM CDT
source: https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD
alert: false
alert_url:
---
Paragraphs separated by blank lines.

## Optional heading

More text.
```

When the NWS has any watch, warning, or advisory in effect, set `alert: true` and put the link to the alert in `alert_url`. The post then leads with a banner pointing to the official alert.

## Local build

```
python build.py
```

Output goes to `_site/`.

## One-time setup

In the repo settings under Pages, set the source to GitHub Actions. The custom domain comes from `static/CNAME`.
