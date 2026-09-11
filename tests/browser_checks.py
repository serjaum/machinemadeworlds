"""Browser contract; run separately with the QA-only Playwright environment."""
import os
import unittest
from playwright.sync_api import sync_playwright

BASE = os.environ.get('MMW_PREVIEW_URL', 'http://127.0.0.1:8913')

class ThemeTests(unittest.TestCase):
    def test_light_first_and_manual_theme_survives_navigation(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(color_scheme='dark')
            page = context.new_page()
            page.goto(BASE)
            self.assertEqual(page.locator('html').get_attribute('data-theme'), 'light')
            page.locator('[data-theme-toggle]').click()
            self.assertEqual(page.locator('html').get_attribute('data-theme'), 'dark')
            self.assertEqual(page.locator('[data-theme-toggle]').get_attribute('aria-pressed'), 'true')
            page.goto(BASE + '/blog/')
            self.assertEqual(page.locator('html').get_attribute('data-theme'), 'dark')
            page.locator('[data-theme-toggle]').click()
            page.reload()
            self.assertEqual(page.locator('html').get_attribute('data-theme'), 'light')
            browser.close()

class SearchTests(unittest.TestCase):
    def test_search_filters_and_recovers_from_empty_results(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(BASE + '/blog/')
            self.assertTrue(page.locator('[data-search]').is_visible(), 'Search must progressively enhance the archive')
            total = page.locator('[data-search-item]:visible').count()
            self.assertGreater(total, 1)
            page.locator('[data-search]').fill('RTX')
            self.assertEqual(page.locator('[data-search-item]:visible').count(), 1)
            page.locator('[data-search]').fill('no-article-matches-zz123')
            self.assertTrue(page.locator('[data-empty]').is_visible())
            self.assertIn('0', page.locator('[data-search-status]').inner_text())
            page.locator('[data-clear-search]').click()
            self.assertEqual(page.locator('[data-search-item]:visible').count(), total)
            browser.close()

class GlobalSearchTests(unittest.TestCase):
    PAGES = ['/', '/blog/', '/topics/automation/', '/posts/gpt-6-astra-launch/']
    BODY_TERMS = ['osworld', 'compaction', 'idempotent']

    def test_header_search_present_on_every_page(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for path in self.PAGES:
                page.goto(BASE + path)
                box = page.locator('[data-global-search]')
                self.assertTrue(box.is_visible(), f'Header search must show on {path}')
                self.assertEqual(box.get_attribute('maxlength'), '120')
                self.assertEqual(
                    page.locator('form.masthead-search').get_attribute('action'), '/search/')
            browser.close()

    def test_body_only_terms_rank_target_first(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for term in self.BODY_TERMS:
                page.goto(BASE + '/search/?q=' + term)
                page.wait_for_selector('[data-global-results] [data-search-item]', timeout=10000)
                first = page.locator('[data-global-results] [data-search-item] h3 a').first
                self.assertEqual(first.get_attribute('href'), '/posts/gpt-6-astra-launch/',
                                 f'Body-only term {term!r} must rank the Astra article first')
                self.assertIn(term, page.locator('[data-search-status]').inner_text().lower())
            browser.close()

    def test_url_reload_reproduces_results(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(BASE + '/search/')
            page.locator('[data-search-page]').fill('osworld')
            page.wait_for_selector('[data-global-results] [data-search-item]', timeout=10000)
            self.assertIn('q=osworld', page.url)
            count = page.locator('[data-global-results] [data-search-item]').count()
            self.assertGreater(count, 0)
            page.reload()
            page.wait_for_selector('[data-global-results] [data-search-item]', timeout=10000)
            self.assertEqual(
                page.locator('[data-global-results] [data-search-item]').count(), count)
            self.assertEqual(page.locator('[data-search-page]').input_value(), 'osworld')
            browser.close()

    def test_keyboard_and_empty_state(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(BASE + '/search/?q=no-article-matches-zz123')
            page.wait_for_selector('[data-empty]:visible', timeout=10000)
            self.assertIn('No articles found.', page.locator('[data-empty]').inner_text())
            self.assertIn('Try a different word.', page.locator('[data-empty]').inner_text())
            page.keyboard.press('Escape')
            self.assertEqual(page.locator('[data-search-page]').input_value(), '')
            page.evaluate('document.activeElement.blur()')
            page.keyboard.press('/')
            self.assertEqual(page.evaluate('document.activeElement.id'), 'site-search')
            browser.close()

    def test_no_js_hides_progressive_controls(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context(java_script_enabled=False)
            page = context.new_page()
            page.goto(BASE + '/blog/')
            self.assertFalse(page.locator('[data-search]').is_visible(),
                             'Listing filter must stay hidden without JS')
            self.assertTrue(page.locator('form.masthead-search').is_visible(),
                            'Header search must degrade to a plain GET form without JS')
            page.goto(BASE + '/search/?q=osworld')
            self.assertIn('Search needs JavaScript', page.content())
            browser.close()

if __name__ == '__main__':
    unittest.main()
