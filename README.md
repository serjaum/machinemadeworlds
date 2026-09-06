# Machine Made Worlds

Static English-language AI blog at https://machinemadeworlds.com.

See site files and deploy-hostinger.sh.

## Authoring

Journal posts live in `content/posts/<slug>.json` + `<slug>.html`.
Every production change follows this flow:

1. Scaffold a draft with `python3 scripts/new_post.py <slug> --title "..." --topic <key> --date YYYY-MM-DD`,
   complete the metadata and body, then set `draft` to `false`.
2. Ship its build-log entry in the same PR (see `## Build log` below):
   scaffold with `python3 scripts/new_buildlog.py <slug> --title "..." --topic <key> --kind <kind> --date YYYY-MM-DD`,
   fill the provenance metadata, cover Motivation / Changes / Implementation /
   Agent trail / Evidence, and set `draft` to `false`.
3. Publish with `python3 scripts/build.py` and verify with `python -m unittest discover -s tests`.
4. Run the presence gate `python3 scripts/check_buildlog_presence.py`:
   it FAILs any change set that touches production output (`content/posts/`,
   `templates/`, `scripts/build.py`, `assets/`, `content/site.json`) without a
   matching non-draft build-log entry. QA enforces the same check on every PR.

Standing rule (MAC-64): from now on, every production change ships with its
Build Log entry in the same PR — Motivation, Changes, Implementation, Agent
trail, Evidence — enforced by the QA buildlog-presence check (FAIL without it)
and the Director merge-gate (no release approval without it).

## Build log

Short, status-stamped site-change entries live in `content/buildlog/<slug>.json` +
`<slug>.html` and render to `/build-log/` (index) and `/build-log/<slug>/` (detail),
reusing the journal templates. Scaffold a draft with
`python3 scripts/new_buildlog.py <slug> --title "..." --topic <key> --kind <kind> --date YYYY-MM-DD`
where `--kind` is one of `Shipped`, `Fix`, `Experiment`, `Note`. The entry schema,
field limits and `ArticleMarkup` gate are identical to journal posts; `topic` must
exist in `content/site.json` and `draft` must stay a JSON boolean. Before publishing,
fill the provenance metadata (`mac_id` like `MAC-47`, `commit` short SHA or `n/a`,
`agents` array) and the v2 pipeline fields below, then set `draft` to `false`.
End every entry body with the agent-trail block (allowlisted markup only, no secrets,
prompts or credentials):

```html
<div class="trail"><h2>How this entry was built.</h2><ol><li><time datetime="2026-09-05">Sep 05, 2026</time><span>DEV implemented on <code>feat/build-log-section</code>.</span></li></ol></div>
```

### Build log v2 fields (MAC-72)

Published entries carry machine-readable provenance plus an ordered pipeline:

- `pr`: integer PR number, or `null` when there is no PR (then `pr_url`
  and `branch` must also be `null`).
- `pr_url`: full public PR URL, exactly
  `https://github.com/serjaum/machinemadeworlds/pull/<pr>`.
- `branch`: source branch name (e.g. `feat/my-change`), or `null` with no PR.
- `merge_sha`: full 40-char hex merge SHA, or `null` pre-merge. When `null`,
  `merge_note` must explain why (e.g. "Pre-merge: ships in the same PR").
- `stages`: non-empty ordered array of
  `{agent, stage, verdict, sha, rationale, at}`. `agent` is one of
  `Editor/DEV/SEC/QA/SRE/Director`; `verdict` is one of
  `PASS/BLOCK/FAIL/done/skipped`; `sha` is 7-40 hex chars (`null` only for
  `skipped`); `rationale` is a single line, required non-empty for
  `BLOCK`/`FAIL`; `at` is `YYYY-MM-DD`. Every `BLOCK`/`FAIL` must be
  followed by at least two return-loop entries (fix SHA, then re-review).
  Every stage must trace to a real issue comment or PR event — nothing invented.
- `reasoning`: per-agent summaries of 2-4 sentences each, sourced strictly
  from the linked issues. Agents without evidence are marked with
  "Not evidenced ..." (then 1-4 sentences are accepted).

The builder renders the pipeline from `stages` into the entry's trail div:
a top link row (PR, merge commit, branch — the branch links at the PR
commits page, never `/tree/<branch>`, so merged entries cannot 404 after
their head branch is deleted), a vertical `flow` node list with
text-first verdict labels (`◆` prefix plus muted left rule for `BLOCK`/`FAIL`,
accent left rule on the terminal node), linearized `↩ BLOCK → fix → re-review`
loop rows with short SHAs, a verdict-trail table (`Stage | Agent | Verdict |
SHA | Why`), and the per-agent reasoning list. Markup is ArticleMarkup-safe
(`div/span/table/h3`, zero JS, zero external assets) and styles are additive
`flow-*` classes under `.trail` using semantic tokens only (see MAC-78).

Use `h3` instead of `h2` for the trail title when the entry body already contains
`h2` sections. Build-log entries appear in the sitemap but are excluded from
`feed.xml` and `posts.json`, which stay journal-only.

Every production change ships with its build-log entry in the same PR (standing
rule, MAC-64). The automated side of the rule is
`scripts/check_buildlog_presence.py` (unit-covered by
`tests/test_always_log.py`): any PR changing production output —
`content/posts/`, `templates/`, `scripts/build.py`, `assets/`,
`content/site.json` — without a matching non-draft entry covering Motivation /
Changes / Implementation / Agent trail / Evidence is a QA FAIL.
