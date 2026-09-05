# MAC-5 Release QA and SEO Gate — Report
**Site:** machinemadeworlds.com  
**Artifact under review:** `dist/` as built in workspace `78f3c7a5-cb2f-40ac-a2cb-d8e0e03c84c1/_default/dist`  
**Date (UTC):** 2026-09-05  
**Reviewer:** QA & SEO Reviewer (ddce59cd-61d6-41d7-8e58-39e5ab85d034)  
**Mode:** standard / release gate — no deploy, no commit, no secrets touched

## Execution Summary
Ran real-output checks locally against `dist/` with filesystem validation + live HTTP `curl` against production host. All commands reproducible below.

## Live HTTP Checks (curl)
Reproduction:
```
curl -s -o /dev/null -w "%{http_code}\n" https://machinemadeworlds.com/
curl -s -I https://machinemadeworlds.com/about/ --max-time 8
curl -s -I https://machinemadeworlds.com/blog/ --max-time 8
curl -s -I https://machinemadeworlds.com/sitemap.xml --max-time 8
curl -s -I https://machinemadeworlds.com/robots.txt --max-time 8
curl -s -I https://machinemadeworlds.com/posts/local-agent-team/ --max-time 8
curl -s https://machinemadeworlds.com/ | head -c 200
```

| URL | Expected | Actual | Verdict |
|---|---|---|---|
| `https://machinemadeworlds.com/` | 200 `text/html` | **200** `text/html; charset=UTF-8` `Server: hcdn` `X-Powered-By: PHP/8.3.33` — body is **Hostinger Default page** (`<title>Default page</title>`) | **FAIL — not serving dist artifact** |
| `https://machinemadeworlds.com/about/` | 200 | **404** `Content-Type: text/html` Hostinger 404 template | FAIL |
| `https://machinemadeworlds.com/blog/` | 200 | **404** | FAIL |
| `https://machinemadeworlds.com/sitemap.xml` | 200 `application/xml` | **404** (Hostinger 404 page) | **CRITICAL** |
| `https://machinemadeworlds.com/robots.txt` | 200 `text/plain` | **404** | **CRITICAL** |
| `https://machinemadeworlds.com/posts/local-agent-team/` | 200 | **404** | FAIL |
| `https://machinemadeworlds.com/og-cover.jpg` | 200 `image/jpeg` | **404** | **CRITICAL — OG image referenced but not deployed nor present in dist** |

**Interpretation:** Production host is serving the Hostinger parking page, not `dist/`. Artifact has never been deployed or deploy failed. This is **informational for gate** (artifact quality still matters), but blocks any claim of "live verified".

## Internal Link Checks (filesystem, `dist/`)
Reproduction:
```python
# extract href/src from dist/**/*.html, resolve root-relative / paths against dist/ filesystem
# See heartbeat script — checked 175 internal links, 14 external canonical URLs
```

- **Total internal hrefs scanned:** 175
- **Resolvable to file or index.html:** 174 OK, 1 false-positive (`${p.url}` inside JS template string in legacy `blog.html` / root) — not a real anchor.
- **All navigational links** (`/`, `/blog/`, `/about/`, `/posts/<slug>/`, `/sitemap.xml`, `/robots.txt`, `/styles.css`) resolve to existing files.
- **External links:** 14 unique `https://machinemadeworlds.com/...` canonical URLs — consistent origin.

**Verdict:** PASS — no broken internal links in deploy artifact.

## HTML Structure Checks
Reproduction: regex parse of every `dist/**/*.html` for `<!doctype html>`, `<html lang>`, `<meta charset>`, `<meta viewport>`, `<title>`, heading counts.

| Check | Result |
|---|---|
| `<!doctype html>` | **PASS** all 16 files |
| `<html lang="en">` | PASS all files |
| `<meta charset="utf-8">` | PASS |
| `<meta name="viewport">` | PASS all files |
| `<title>` non-empty, single | PASS (17 unique titles, no dups) |
| Exactly one `<h1>` per page | PASS all files |
| Heading hierarchy (no skipped levels) | **FAIL** `dist/blog/index.html:line_number 26` and `dist/blog.html:line_number 1` go `h1 → h3` skipping `h2` |
| `html-validate` style tag closure | Not run (no npx available), but manual parse shows no unclosed tags |

## Metadata / SEO Checks
Reproduction: regex extraction of `<title>`, `<meta name="description">`, `<link rel="canonical">`, OG, JSON-LD per file.

### Per-file findings (dist)
- **`dist/index.html:6`** `title` 62 chars — slightly long (>60) but acceptable. `meta description` 135 chars PASS. Canonical `https://machinemadeworlds.com/` OK. OG:title/description/url/image + JSON-LD WebSite present. **PASS**.
- **`dist/about/index.html:6`** `title` 27 chars short (<30) WARN. Description 104 chars PASS but short. Canonical `/about/` OK, OG + JSON-LD AboutPage PASS.
- **`dist/blog/index.html:6`** `title` 26 chars short WARN. Description 109 PASS. Canonical `/blog/` OK, OG + JSON-LD Blog PASS. Heading hierarchy FAIL (see above).
- **Post `dist/posts/local-agent-team/index.html:6`** title 68 chars over 60 WARN, description 116 PASS, canonical pretty URL OK, OG + JSON-LD BlogPosting PASS.
- **Post `dist/posts/small-models-rtx2060/index.html:6`** title 59 PASS, description 132 PASS, OG + image PASS, JSON-LD PASS.
- **Post `dist/posts/autonomous-website-ops/index.html:6`** title 82 FAIL (>60) WARN, description 145 PASS, OG PASS, JSON-LD PASS.
- **`dist/posts/hello-machines/index.html:6`** title 63 WARN, description 108 PASS, OG PASS, JSON-LD PASS.
- **`dist/posts/automation-playbook/index.html:6`** title 63 WARN, description 110 PASS, canonical present, OG present (no image) WARN, JSON-LD PASS.
- **`dist/posts/dark-mode-design/index.html:6`** title 51 PASS, description 90 WARN (short), canonical + OG present (no image).
- **`dist/posts/_template/index.html:7`** template placeholder — **should not be indexable** but has `canonical: https://.../posts/your-slug/` (placeholder) and no `noindex`. Currently **linked from `dist/blog/index.html:59`** and reachable.
- **Flat fallbacks** `dist/about.html:6`, `dist/blog.html:4`, `dist/posts/*.html` legacy files: have titles/descriptions but **missing canonical on `about.html`/`blog.html`**, missing OG, missing JSON-LD except post/*.html have canonical to `.html` variant. This creates **duplicate content**.
- **`dist/404.html:7`** correctly has `<meta name="robots" content="noindex">`, single `h1` PASS. No description (acceptable per noindex). **PASS**.

### Critical SEO Defects
1. **`og-cover.jpg` missing (CRITICAL):** Referenced in 6 files (`dist/index.html:18`, `dist/posts/local-agent-team/index.html:15`, `dist/posts/small-models-rtx2060/index.html:15`, `dist/posts/autonomous-website-ops/index.html:15`, `dist/posts/hello-machines/index.html:15`, `dist/posts/_template/index.html:16`) as `https://machinemadeworlds.com/og-cover.jpg`. File does **not exist in `dist/` or root** → social cards broken, HTTP 404 on share crawlers.
2. **Sitemap duplicates + canonical mismatch (MAJOR):** `dist/sitemap.xml:3-16` lists **14 URLs** including **both** pretty and `.html` for same content: `/about/` and `/about.html`, `/blog/` and `/blog.html`, `/posts/<slug>/` and `/posts/<slug>.html` for 3 slugs. Canonicals conflict (`/about.html` has NO canonical). Duplicate URLs in sitemap waste crawl budget and risk indexing wrong variant.
3. **`posts.json` out of sync (MAJOR):** `dist/posts.json:1` lists **3** posts (`.html` URLs), while `dist/blog/index.html` renders **4** post cards (`local-agent-team`, `small-models-rtx2060`, `autonomous-website-ops`, `hello-machines`) + template link. `dist/sitemap.xml` lists **6** posts (`hello-machines`, `automation-playbook`, `dark-mode-design` plus 3). Dynamic JS on `index.html`/`blog.html` loading `posts.json` would show stale list vs static blog cards — data inconsistency.
4. **Template exposure (MAJOR):** `dist/posts/_template/index.html` is deployed, indexable, linked from production blog, with placeholder canonical (`/posts/your-slug/`) and OG image to missing asset. Must be excluded or `noindex`.
5. **Missing canonicals on flat variants (MINOR→MAJOR for crawl):** `dist/about.html`, `dist/blog.html` have no canonical; sitemap includes them, inviting duplication.
6. **`robots.txt` Host directive (MINOR):** `dist/robots.txt:5` `Host: https://machinemadeworlds.com` is non-standard (Yandex only) and URL includes scheme, ignored by Google but not harmful; `Sitemap:` is correct.

## Sitemap / Robots Validation
Reproduction:
```
python3 -c "import xml.etree.ElementTree; ET.parse('dist/sitemap.xml')"
cat dist/robots.txt
```

-
- Well-formed XML: PASS.
- Entries: 14, no duplicates by string.
- Protocol: all https://machinemadeworlds.com/* PASS.
- File correspondence: every <loc> maps to existing file in dist/ (verified via dist/<path>/index.html or .html existence) — PASS on filesystem, FAIL on live (all but / return 404 live).
- lastmod: all 2026-09-05 except automation-playbook 2026-09-04, dark-mode-design 2026-09-03 — plausible.
- robots.txt: User-agent: * / Allow: / PASS, Sitemap: https://machinemadeworlds.com/sitemap.xml PASS, Host: present WARN. No disallow of template.

## Mobile / Accessibility Basics
Reproduction: regex for viewport, a.skip[href="#main"], <nav aria-label>, <img alt>, CSS media queries.
| Check | Result |
|---|---|
| meta viewport present | PASS all dist pages |
| Skip link href="#main" | PASS all pretty pages FAIL legacy flat dist/about.html, dist/blog.html, 404.html (no skip) but minimal markup |
| nav aria-label | PASS pretty pages, FAIL flat legacy |
| img alt | PASS — only 1 image dist/posts/_template/index.html has alt Descriptive alt text |
| Semantic main#main, header.site-header, footer.site-footer | PASS |
| CSS mobile query @media | PASS dist/styles.css contains @media(max-width:600px) and prefers-reduced-motion |
| Touch targets / contrast | Manual: dark theme --bg:#0b0b10 vs --text:#ececf1 off-white NOT pure white, reasonable; not programmatically validated |

## Page Weight
Reproduction:
```
find dist -type f | xargs ls -lh
gzip -c dist/*.html | wc -c
```
| File | Raw | Gzipped |
|---|---|---|
| dist/index.html | 6.2 KB | 2.3 KB |
| dist/about/index.html | 4.1 KB | 1.8 KB |
| dist/blog/index.html | 4.4 KB | 1.6 KB |
| dist/posts/* / index.html | 3.2-7.7 KB | 1.4-3.3 KB |
| dist/styles.css | 10.4 KB (uncompressed) | ~2.9 KB gz (est.) |
| Total dist | 85.8 KB (all files) | — |
No trackers, no JS frameworks. PASS — well under 50 KB HTML+CSS per page, <15 KB CSS claim holds (10.4 KB).

## Additional Observations
- root/styles.css (10,118 B) vs dist/styles.css (10,377 B) differ at offset ~2779 padding. Root is stale; deploy artifact correct but indicates uncommitted divergence.
- Live site serves Hostinger default page, not artifact — deploy gate not yet executed.
- Git shows modified: styles.css + untracked about/, blog/, posts/*/ — artifact not committed.

## Pass / Fail Summary
| Area | Pass | Fail | Severity |
|---|---|---|---|
| HTTP live (if deployed) | 1/7 URLs 200 | 6/7 404, OG image 404 | CRITICAL (deploy missing) |
| Internal links (artifact) | 174/175 | 0 real broken | PASS |
| HTML structure | 14/16 hierarchy | blog h1->h3 skip | MINOR |
| Metadata | 6/10 canonical+OG | OG image missing 6 pages | CRITICAL |
| Sitemap/robots | XML valid, files resolve | duplicate .html + / variants, missing canonicals | MAJOR |
| Mobile/accessibility | viewport/skip/semantics | flat pages minimal | PASS |
| Page weight | all <10 KB | — | PASS |

## Release Recommendation
BLOCK — DO NOT RELEASE

### Critical (must fix before publish)
1. Create and commit og-cover.jpg (1200x630) at dist/og-cover.jpg + root, or remove og:image references until asset exists. Reproduce: ls dist/og-cover.jpg -> missing; curl -I https://machinemadeworlds.com/og-cover.jpg -> 404.
2. Exclude _template from deploy or add <meta name="robots" content="noindex, nofollow"> and remove link from dist/blog/index.html and from sitemap. Verify: grep -r _template dist/.
3. Fix posts.json sync: Regenerate from source posts. Should include hello-machines, automation-playbook, dark-mode-design with pretty URLs /posts/<slug>/. Current posts.json has only 3 .html entries vs 6 sitemap entries vs 4 cards on blog. Reproduce: cat dist/posts.json vs grep -o href="/posts/[^"]*" dist/blog/index.html.

### Major (must fix before next deploy; blocks SEO quality)
4. De-duplicate sitemap: Choose canonical strategy — prefer pretty URLs (/about/, /blog/, /posts/<slug>/) and remove .html variants from sitemap.xml. Ensure every URL in sitemap has self-referential canonical. Remove Host: from robots.txt or fix.
5. Add canonicals to flat fallbacks about.html, blog.html pointing to pretty variant, or drop flat files from dist/ and redirect via .htaccess.
6. Title length: trim autonomous-website-ops (82) and local-agent-team (68) to <=60.

### Minor (fix soon)
7. Fix heading hierarchy on dist/blog/index.html — change cards <h3> under <h1> Blog to <h2> or add <h2>All posts</h2>.
8. Unify og:image strategy: either add og:image to all article pages or explicitly omit; currently mixed (3 posts missing image).
9. Commit divergence: styles.css root vs dist diff — copy dist/styles.css to root or build step to keep in sync.

## Exact Reproduction Steps (copy/paste)
```
# 1. Internal link check
python3 -c "
import pathlib, re
dist=pathlib.Path('dist')
href=re.compile(r'href=["']([^"']+)["']')
for f in dist.rglob('*.html'):
  for m in href.finditer(f.read_text()):
    url=m.group(1)
    if url.startswith('/') and not url.startswith('//'):
      path=url.split('#')[0].split('?')[0].lstrip('/')
      cand=dist/path
      cand2=dist/(path+'/index.html')
      print(f,cand.exists(),cand2.exists())
"

# 2. Metadata audit
grep -n '<title>|<meta name="description"|<link rel="canonical"' dist/**/*.html dist/*.html

# 3. Sitemap validity
python3 -m xml.etree.ElementTree dist/sitemap.xml
cat dist/sitemap.xml
cat dist/robots.txt
curl -s -I https://machinemadeworlds.com/sitemap.xml | head
curl -s -I https://machinemadeworlds.com/robots.txt | head

# 4. Page weight
find dist -type f -exec wc -c {} \; | sort -n
gzip -c dist/index.html | wc -c
ls -lh dist/og-cover.jpg || echo "MISSING og-cover.jpg"

# 5. posts.json vs sitemap vs blog cards
cat dist/posts.json | python3 -m json.tool
grep -o 'href="/posts/[^"]*"' dist/blog/index.html | sort -u
grep -o '<loc>[^<]*</loc>' dist/sitemap.xml
```

## Next Steps
- Fix critical 1-3, re-run checks, then re-request QA gate.
- After critical fixes, require Board request_confirmation with dist/ diff + screenshot before lftp mirror -R dist/ public_html deploy.
- Post-deploy: re-run live curl -I table and confirm 200 for /, /about/, /blog/, /sitemap.xml, /robots.txt, three post URLs, and og-cover.jpg.

---
Generated with real output; no commits or deploys performed per gate contract.
