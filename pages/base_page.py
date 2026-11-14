"""
pages/base_page.py — Base class for all Page Object Model classes.
Provides shared navigation, locator helpers, and common page interactions
without excessive abstraction. Compatible with Python 3.9 and 3.13.
"""
from typing import Optional, Union
from playwright.sync_api import Page, Locator, Response
from config.config import Config
from utils.logger import get_logger

logger = get_logger("base_page")


class BasePage:
    """Base class encapsulating common interactions across all pages."""

    def __init__(self, page: Page):
        self.page: Page = page

    def navigate_to(self, url_or_path: str = "") -> Optional[Response]:
        """
        Navigates to the specified URL or relative path.
        If a relative path is provided, it resolves against Config.BASE_URL.
        """
        target_url = (
            url_or_path
            if url_or_path.startswith("http")
            else f"{Config.BASE_URL}{url_or_path}"
        )
        logger.info(f"Navigating to {target_url}")
        return self.page.goto(target_url)

    @property
    def current_url(self) -> str:
        """Returns the current page URL."""
        return self.page.url

    @property
    def page_title(self) -> str:
        """Returns the document title."""
        return self.page.title()

    def to_locator(self, selector_or_locator: Union[str, Locator]) -> Locator:
        """Ensures a Locator object is returned, whether given a string selector or a Locator."""
        if isinstance(selector_or_locator, str):
            return self.page.locator(selector_or_locator)
        return selector_or_locator

    def get_element_text(self, selector_or_locator: Union[str, Locator]) -> str:
        """Returns the trimmed inner text of an element."""
        locator = self.to_locator(selector_or_locator)
        return locator.inner_text().strip()

    def fill_field(self, selector_or_locator: Union[str, Locator], value: str) -> None:
        """Fills an input field with the specified value."""
        locator = self.to_locator(selector_or_locator)
        locator.fill(value)

    def click_element(self, selector_or_locator: Union[str, Locator]) -> None:
        """Clicks an element."""
        locator = self.to_locator(selector_or_locator)
        locator.click()

    def is_element_visible(
        self, selector_or_locator: Union[str, Locator], timeout: Optional[int] = None
    ) -> bool:
        """Checks if an element is visible on the page."""
        locator = self.to_locator(selector_or_locator)
        return locator.is_visible(timeout=timeout)
