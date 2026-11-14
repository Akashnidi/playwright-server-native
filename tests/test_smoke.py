"""
tests/test_smoke.py — Initial smoke test for Phase 2 validation.
Verifies that the Playwright browser foundation can initialize,
navigate to SauceDemo, and gracefully close.
"""
import pytest
from playwright.sync_api import Page
from config.config import Config


@pytest.mark.smoke
def test_saucedemo_title_smoke(page: Page, app_config: Config):
    """
    Smoke test:
    1. Navigate to SauceDemo base URL.
    2. Verify page title is 'Swag Labs'.
    """
    page.goto(app_config.BASE_URL)
    assert page.title() == "Swag Labs"
