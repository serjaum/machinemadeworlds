"""Independent browser measurements; Playwright/axe are QA-only dependencies.
MMW_AXE_PATH points to axe-core/axe.min.js. No QA library ships with the site.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'qa'
OUT.mkdir(exist_ok=True)
BASE = os.environ.get('MMW_PREVIEW_URL', 'http://127.0.0.1:8913')
AXE = os.environ['MMW_AXE_PATH']
paths = ['/' + p.relative_to(ROOT / 'dist').as_posix().removesuffix('index.html') for p in (ROOT / 'dist').rglob('*.html')]
report = {'url':BASE,'scope':'Local Chromium browser audit, not production network measurements','pages':[],'errors':[],'mobile':[]}
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce')
    page.on('pageerror', lambda error: report['errors'].append(str(error)))
    for theme in ('light','dark'):
        page.goto(BASE)
        page.evaluate('(theme) => localStorage.setItem("mmw-theme", theme)',theme)
        for path in paths:
            response = page.goto(BASE + path,wait_until='load')
            page.add_script_tag(path=AXE)
            result = page.evaluate('''async () => {
                const a = await axe.run(document, {runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}});
                return {violations:a.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))})),
                overflow:document.documentElement.scrollWidth > innerWidth,
                theme:document.documentElement.dataset.theme};
            }''')
            report['pages'].append({'path':path,'theme':theme,'status':response.status,**result})
    for width in (320,390,768):
        page.set_viewport_size({'width':width,'height':844})
        for path in ['/', '/blog/', '/posts/local-agent-team/', '/about/']:
            page.goto(BASE+path)
            report['mobile'].append({'width':width,'path':path,'overflow':page.evaluate('document.documentElement.scrollWidth > innerWidth')})
    nojs = browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
    static = nojs.new_page()
    static.goto(BASE+'/blog/')
    report['no_js_article_count'] = static.locator('[data-search-item]').count()
    report['no_js_search_hidden'] = not static.locator('[data-search-control]').is_visible()
    # Storage can be unavailable in private/locked-down environments.
    private = browser.new_context()
    private.add_init_script("Object.defineProperty(window, 'localStorage', {get(){throw new Error('Storage unavailable')}})")
    private_page = private.new_page()
    private_page.goto(BASE)
    private_page.locator('[data-theme-toggle]').click()
    report['storage_disabled_toggle'] = private_page.locator('html').get_attribute('data-theme')
    # Synthetic cold mobile load. This measures localhost under throttling, not CDN latency.
    mobile = browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,reduced_motion='reduce')
    measured = mobile.new_page()
    measured.add_init_script("window.metrics={cls:0,lcp:0}; new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)metrics.cls+=e.value})).observe({type:'layout-shift',buffered:true}); new PerformanceObserver(l=>{metrics.lcp=l.getEntries().at(-1).startTime}).observe({type:'largest-contentful-paint',buffered:true})")
    cdp = mobile.new_cdp_session(measured)
    cdp.send('Network.enable')
    cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
    cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':93750})
    cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
    measured.bring_to_front()
    measured.goto(BASE,wait_until='networkidle')
    measured.screenshot(path=str(OUT/'cold-mobile.png'))
    measured.wait_for_timeout(300)
    report['synthetic_mobile'] = measured.evaluate('''() => ({...metrics,
        fcp:performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
        requests:performance.getEntriesByType('resource').filter(r=>r.initiatorType!=='other').map(r=>({url:r.name,bytes:r.transferSize,duration:r.duration})),
        nav:performance.getEntriesByType('navigation')[0].toJSON()})''')
    browser.close()
report['passed'] = not report['errors'] and all(not x['violations'] and not x['overflow'] and x['status']==200 for x in report['pages']) and all(not x['overflow'] for x in report['mobile']) and report['storage_disabled_toggle']=='dark' and report['no_js_article_count']==6
(OUT/'browser-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({**{k:v for k,v in report.items() if k not in ('pages','mobile','synthetic_mobile')},'page_theme_checks':len(report['pages']),'responsive_checks':len(report['mobile']),'violations':[{k:x[k] for k in ('path','theme','violations','overflow')} for x in report['pages'] if x['violations'] or x['overflow']],'mobile_overflows':[x for x in report['mobile'] if x['overflow']],'performance':{k:v for k,v in report['synthetic_mobile'].items() if k!='nav'}},indent=2))
raise SystemExit(0 if report['passed'] else 1)
