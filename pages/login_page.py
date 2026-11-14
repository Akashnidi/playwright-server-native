"""
pages/login_page.py — Page Object for SauceDemo login page.
Encapsulates credentials inputs, login actions, and error banner validation.
"""
from typing import Optional
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class LoginPage(BasePage):
    """Page object representing the SauceDemo Login page."""

    URL_PATH = "/"

    def __init__(self, page: Page):
        super().__init__(page)
        # Locators using data-test attributes and accessible semantics
        self.username_input: Locator = page.locator('[data-test="username"]')
        self.password_input: Locator = page.locator('[data-test="password"]')
        self.login_button: Locator = page.locator('[data-test="login-button"]')
        self.error_message_container: Locator = page.locator('[data-test="error"]')

    def load(self) -> None:
        """Navigates directly to the login page."""
        self.navigate_to(self.URL_PATH)

    def enter_username(self, username: str) -> "LoginPage":
        """Enters the username into the username field."""
        self.username_input.fill(username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        """Enters the password into the password field."""
        self.password_input.fill(password)
        return self

    def click_login(self) -> None:
        """Clicks the login submit button."""
        self.login_button.click()

    def login(self, username: str, password: str) -> None:
        """Convenience method to execute a complete login flow."""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        """Returns the text of the login error message if displayed."""
        return self.error_message_container.inner_text().strip()

    def is_error_displayed(self) -> bool:
        """Checks if the login error banner is currently visible."""
        return self.error_message_container.is_visible()
