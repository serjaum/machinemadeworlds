# QA release checklist (MAC-64 standing rule)

Run on every PR before release approval. Any FAIL blocks the release.

## 1. Buildlog presence (FAIL without it)

Any PR changing production output — `content/posts/`, `templates/`,
`scripts/build.py`, `assets/`, `content/site.json` — must ship a matching
non-draft `content/buildlog/<slug>` entry in the same PR covering all five
sections: Motivation, Changes (What changed), Implementation (How it was
done), Agent trail (`div.trail` with dated `time` steps), Evidence
(Verification evidence).

Automated side: `python3 scripts/check_buildlog_presence.py` must print
`PASS`. QA FAILs the PR when it prints `FAIL`.

## 2. Build and tests

`python3 scripts/build.py` exits 0, full suite
`python -m unittest discover -s tests` is green, and a second consecutive
build is byte-identical (deterministic rebuild).

## 3. Entry rendering

`/build-log/` index lists the new entry; each new detail page renders with a
single `h1`, the trail block, and a sitemap entry; `feed.xml` and
`posts.json` stay journal-only.
