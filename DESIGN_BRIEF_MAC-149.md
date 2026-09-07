# MAC-149 — DESIGN clearance: /terms/ + /privacy/ page type (lightweight)

**Date:** 2026-09-07 · **Author:** UX & Frontend Designer (Design Agent) · **Status:** PASS — DEV cleared to implement after GitHub preflight
**Refs:** OpenDesign `https://github.com/nexu-io/open-design` (brief → direction → artifact → handoff; brand contract = existing `DESIGN.md` equivalent: `assets/site.css` semantic tokens + `templates/base.html` chrome; prototype-reference contract; semantic tokens only; AA contrast on real pairs; `:focus-visible` everywhere; `prefers-reduced-motion`; native semantics). Prior assessments `DESIGN_BRIEF_MAC-80.md`, `DESIGN_BRIEF_MAC-48.md` (nav rules), `DESIGN_BRIEF_MAC-37.md` (about-template precedent, ArticleMarkup gate).
**Scope:** NEW page type → mandatory re-evaluation applies. Site today has `/`, `/blog/`, `/build-log/`, `/about/`, `/posts/*/`, `/topics/*/` only — no legal pages. Routine-content rule does NOT apply.

## 1) Evaluation: current vs proposed (decision per row)

| # | Current experience | Proposal (MAC-149) | Design verdict |
|---|---|---|---|
| 1 | No `/terms/` or `/privacy/`; footer has no legal links | Two static legal pages reusing the `about.html` body-template pattern (`.container` + `.page-heading` + `.article-body`, one `h1`, `h2` sections, `p/ul/ol` only) | **Approve as-is.** New URLs, zero new components. Same reading measure (`--reading: 65ch`), same serif/sans/mono, same eyebrow/h1/lede idiom as About. |
| 2 | Header `.navigation`: Home · Journal · Build Log · About | No header change — legal pages stay out of header nav | **Approve as-is.** Legal content is low-frequency destination traffic; header stays at 4 links so the 360px wrap rule (`@700px` full-width row) is untouched. |
| 3 | Footer nav: The journal · Build log · About us · RSS; `footer-bottom`: © / tagline / Back to top | Append `Terms` + `Privacy` links to footer nav only (after About, before RSS), no footer CSS change | **Approve as-is.** Footer-only discovery is the correct pattern; verifies at 360px with 6 links wrapping as today. |
| 4 | Both themes via `[data-theme]` semantic vars; no new hex since MAC-80 gate | No new tokens, no new CSS classes expected; body copy binds to existing `--bg/--ink/--muted/--line/--accent` | **Approve as-is.** If DEV needs a legal-specific class, it must be additive + `var(--*)`-only with zero hex/`rgb(`/`@import`/new breakpoint/`!important` (static grep gate). |
| 5 | `scripts/build.py` renders `/about/` verbatim via `template()` + `render()` with `AboutPage` JSON-LD; sitemap lists `/`, `/blog/`, `/build-log/`, `/about/`, topics, posts+entries | Mirror the `/about/` render path: two verbatim templates (or one shared `legal.html` partial with per-page title/body), `WebPage` JSON-LD, canonical + OG + `aria-current` absent (footer-only, no header slot), sitemap += `/terms/` + `/privacy/`, feed/`posts.json` unchanged | **Approve with refinement.** Share one template partial rather than duplicating markup; `og:type=website`, no `aria-current` on footer links, `feed.xml` stays journal-only per MAC-48 precedent. |
| 6 | ArticleMarkup gate validates `content/posts/*` bodies; `templates/about.html` bypasses but stays allowlist-clean | Legal templates stay ArticleMarkup-clean (`h1/h2/p/ul/ol/li/a`, `class/id` attrs only, `/`-relative or `https://` hrefs) even though they bypass the gate like About | **Approve as-is.** No `script/style/form/img` needed; `mailto:` contact link allowed by gate scheme list. |

No redesign of surrounding experience: masthead, theme toggle, home/featured/topics/post, RSS band, print rules, robots shape unchanged.

## 2) Token / class reuse plan

- Permitted vars only: `--bg --surface --raised --ink --muted --line --accent --accent-ink` + `--sans/--serif/--mono` + `--s1--s6` + `--reading`. No new hex, font, breakpoint, or JS.
- Expected CSS delta: zero. If a spacing tweak is unavoidable, one additive `.legal-*` rule max, same static-grep gate as MAC-80 §2.
- Weight budget: two pages × ~About weight (~4–6KB HTML each); no new assets; sitemap +2 URLs.

## 3) Responsive / a11y plan (OpenDesign prototype-reference contract)

- 360/768/1240px: same as About — single column, `.about-layout aside` pattern NOT needed (legal = linear `.article-body` only); masthead wraps as today; footer 6-link wrap verified at 360px.
- Semantics: exactly one `h1` per page (`Terms of use` / `Privacy notice`), `h2` per section, no skipped levels; `<main id="main">` + skip link unchanged; `lang="en"`; last-updated `<time datetime="YYYY-MM-DD">`.
- Contrast: body pairs unchanged (`--ink` on `--bg`, `--muted` on `--bg` — both AA per existing system); `:focus-visible` unchanged; `prefers-reduced-motion`: nothing animates; print: existing rules apply.
- Editorial identity: plain English, no legalese drift; effective-date line; contact `mailto:`; no trackers/cookies claims must match reality (static site, localStorage theme only).

## 4) SEC / QA notes

- SEC: static markup only — no `script`, handlers, `foreignObject`, external hrefs beyond `https://`; flag SEC only if copy introduces data-collection claims needing review. No secrets.
- QA: light+dark at 360/768/1240px; footer links resolve; canonical/OG/JSON-LD per page; sitemap contains both URLs; `feed.xml`/`posts.json` unchanged; `python -m unittest discover -s tests` green.

## 5) Acceptance criteria (DEV handoff)

- [ ] `/terms/` + `/privacy/` render via shared about-pattern template, one `h1` each, `h2` sections, `<time>` effective date.
- [ ] Header nav unchanged (4 links); footer nav appends Terms + Privacy (footer-only discovery).
- [ ] Both themes, 360px mobile + tablet + desktop, no horizontal scroll, no new breakpoint.
- [ ] Canonical + OG (`website`) + `WebPage` JSON-LD per page; sitemap +2; feed/posts.json untouched.
- [ ] CSS delta zero or one additive `var(--*)`-only rule passing the hex/rgb/import/`!important` grep gate.
- [ ] Commit scope suggestion: `feat(mac-149): terms + privacy legal pages (template + footer nav + sitemap)` on a fresh branch after GitHub preflight; no merge/deploy in design issue.

**Clearance:** Design PASS. DEV cleared to implement exactly this after preflight. Any new component, header-nav entry, token, breakpoint, or JS re-opens this review.
