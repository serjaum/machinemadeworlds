# Machine Made Worlds

Static English-language AI blog at https://machinemadeworlds.com.

See site files and deploy-hostinger.sh.

## Authoring

Journal posts live in `content/posts/<slug>.json` + `<slug>.html`.
Scaffold a draft with `python3 scripts/new_post.py <slug> --title "..." --topic <key> --date YYYY-MM-DD`,
complete the metadata and body, then set `draft` to `false`. Publish with
`python3 scripts/build.py` and verify with `python -m unittest discover -s tests`.

## Build log

Short, status-stamped site-change entries live in `content/buildlog/<slug>.json` +
`<slug>.html` and render to `/build-log/` (index) and `/build-log/<slug>/` (detail),
reusing the journal templates. Scaffold a draft with
`python3 scripts/new_buildlog.py <slug> --title "..." --topic <key> --kind <kind> --date YYYY-MM-DD`
where `--kind` is one of `Shipped`, `Fix`, `Experiment`, `Note`. The entry schema,
field limits and `ArticleMarkup` gate are identical to journal posts; `topic` must
exist in `content/site.json` and `draft` must stay a JSON boolean. Before publishing,
fill the provenance metadata (`mac_id` like `MAC-47`, `pr` like `#5` or `n/a`,
`commit` short SHA or `n/a`, `agents` array) and set `draft` to `false`. End every entry
body with the agent-trail block (allowlisted markup only, no secrets, prompts or
credentials):

```html
<div class="trail"><h2>How this entry was built.</h2><ol><li><time datetime="2026-09-05">Sep 05, 2026</time><span>DEV implemented on <code>feat/build-log-section</code>.</span></li></ol></div>
```

Use `h3` instead of `h2` for the trail title when the entry body already contains
`h2` sections. Build-log entries appear in the sitemap but are excluded from
`feed.xml` and `posts.json`, which stay journal-only.
