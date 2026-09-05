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
            page.locator('[data-search]').fill('RTX')
            self.assertEqual(page.locator('[data-search-item]:visible').count(), 1)
            page.locator('[data-search]').fill('no-article-matches-zz123')
            self.assertTrue(page.locator('[data-empty]').is_visible())
            self.assertIn('0', page.locator('[data-search-status]').inner_text())
            page.locator('[data-clear-search]').click()
            self.assertEqual(page.locator('[data-search-item]:visible').count(), 6)
            browser.close()

if __name__ == '__main__':
    unittest.main()
