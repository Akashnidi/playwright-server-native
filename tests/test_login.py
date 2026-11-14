"""
tests/test_login.py — Test suite for SauceDemo authentication flows.
Covers valid login, invalid credentials, empty fields, and locked-out users.
"""
import pytest
from playwright.sync_api import Page
from config.config import Config
from pages import LoginPage, ProductsPage


@pytest.mark.login
@pytest.mark.smoke
def test_successful_login(page: Page) -> None:
    """Verifies that a user with valid credentials can log in successfully."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login(Config.SAUCEDEMO_USERNAME, Config.SAUCEDEMO_PASSWORD)

    products_page = ProductsPage(page)
    assert "/inventory.html" in products_page.current_url
    assert products_page.get_title_text() == "Products"


@pytest.mark.login
@pytest.mark.regression
def test_login_invalid_credentials(page: Page) -> None:
    """Verifies that appropriate error is shown when invalid credentials are provided."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login("invalid_user", "invalid_password")

    assert login_page.is_error_displayed()
    assert (
        "Username and password do not match any user in this service"
        in login_page.get_error_message()
    )


@pytest.mark.login
@pytest.mark.regression
@pytest.mark.parametrize(
    "provide_username,password,expected_error",
    [
        (False, "", "Epic sadface: Username is required"),
        (True, "", "Epic sadface: Password is required"),
    ],
    ids=["empty_credentials", "empty_password"],
)
def test_login_empty_credentials(
    page: Page, provide_username: bool, password: str, expected_error: str
) -> None:
    """Verifies validation error messages when username or password are empty."""
    username = Config.SAUCEDEMO_USERNAME if provide_username else ""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login(username, password)

    assert login_page.is_error_displayed()
    assert expected_error in login_page.get_error_message()


@pytest.mark.login
@pytest.mark.regression
def test_login_locked_out_user(page: Page) -> None:
    """Verifies that a locked-out user cannot log in and sees the locked-out message."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login("locked_out_user", Config.SAUCEDEMO_PASSWORD)

    assert login_page.is_error_displayed()
    assert "Sorry, this user has been locked out" in login_page.get_error_message()
