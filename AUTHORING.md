# Authoring rules for daily posts

These rules govern every post, whether written by the scheduled task or by hand. The generator (`build.py`) enforces the format. The rest is on the writer.

## Job

Turn the National Weather Service Twin Cities forecast discussion into a short post a reader can use in under a minute. Keep the forecasters' reasoning where it changes what someone does with their day. Cut everything else. No filler, no throat clearing, no weather puns, and no agency shorthand (PWAT, advection, KMSP, and so on).

## Sources

1. Area Forecast Discussion, NWS Twin Cities (MPX): https://forecast.weather.gov/product.php?site=MPX&issuedby=MPX&product=AFD&format=txt&version=1&glossary=0
2. For the radar page only: the Weather Prediction Center extended forecast discussion and the Climate Prediction Center hazards outlook (days 3 to 7).

Use only what these say. Never fill a gap from memory or model knowledge. If the discussion gives "mid 70s," write "mid 70s," not 76.

## Format

File: `posts/YYYY-MM-DD.md`, date in America/Chicago. Header lines, a `---` line, then pages. A page starts with `=== Page title`. Inside a page, `Label :: text` makes a yellow label followed by text. A line starting with `|` is a forecast-grid column: `| Thu | Dry | Mid 70s | Mid 50s |` (day, sky, high, low). Source text is sentence case; the stylesheet capitalizes it.

Pages, in order:

1. **Minnesota forecast.** Today first, then the next few days grouped by what changes. At most five entries.
2. **Extended forecast.** One grid column per day, up to five. Fill sky, high, and low only as far as the sources support. If the discussion doesn't say, use a coarse word like "Dry" or "Showers," not a guess.
3. **Alerts and winds.** Active watches, warnings, and advisories (or "None in effect for Minnesota"), notable wind, and when the next update comes.
4. **On the radar** (optional, see below). Insert it after page 2.

Header fields: `title` (a plain headline, no more than 8 words), `issued` (the discussion's issue time, for example `5:44 AM CDT`), `source`, `alert` (`true` or `false`), `alert_url`.

Units: Fahrenheit and miles per hour. The aviation section is in knots, so convert (1 knot is about 1.15 mph) and round.

## Voice

Flat and factual. Numbers first. State the forecasters' confidence when they give it ("models disagree on timing"). No exclamation marks, no adjectives that aren't weather, no advice the source doesn't support. A sentence that doesn't change what someone does with their day gets cut.

## On the radar

Add this page only when the discussion, the WPC discussion, or the CPC hazards outlook names a specific system expected to affect Minnesota within the next 3 to 7 days. On a quiet day the page does not exist. Do not add it to fill space.

Write it the way a weather person would: first person plural ("we're watching"), the expected day in the first line, one short update each day. Every system carries exactly one confidence label, taken from the forecasters' own wording:

- `Watching`: models show something, timing or track unsettled. No snowfall or rainfall amounts.
- `Likely`: the NWS commits to timing and precipitation type. Amounts only if the NWS gives them, in their words.
- `Alert`: an actual watch or warning is in effect. Set `alert: true` and treat it under the alert rule below.

Never name a system the sources don't name. Never give amounts the sources don't give. If a system flagged yesterday faded, weakened, or moved, say so in one line.

## Alerts

If the NWS has any watch, warning, or advisory in effect for the Twin Cities or a substantial part of Minnesota, set `alert: true` and `alert_url` to the official NWS product (or https://www.weather.gov/mpx/ if no direct link is available). The first page leads with the alert in plain terms: what, where, until when. Drop any lighter framing. The site turns the screen red and links to the official alert.

## When not to publish

Do not publish, and do not write from memory, if:

- the discussion can't be fetched,
- the fetched discussion was issued more than 12 hours ago,
- the discussion is clearly a partial or special update that doesn't cover the forecast period.

Stop and report why. A missing day is better than an invented one.

## Review stage

Until the site owner says otherwise, daily posts go to a branch named `draft/YYYY-MM-DD` and never straight to `main`. Merging that branch publishes the post.

## Check before committing

1. `python build.py` runs without errors.
2. Every number in the post appears in the sources, or is a stated conversion of one.
3. Every system on the radar page appears by name in a source.
4. Reading the post aloud, nothing in it sounds like a press release.
