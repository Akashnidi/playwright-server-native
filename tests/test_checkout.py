"""
tests/test_checkout.py — Test suite for SauceDemo checkout flow.
Covers customer information validation, overview verification, and order completion.
"""
import pytest
from playwright.sync_api import Page
from config.config import Config
from pages import LoginPage, ProductsPage, CartPage, CheckoutPage


@pytest.fixture
def checkout_step_one(page: Page) -> CheckoutPage:
    """Fixture that logs in, adds an item, and navigates to Checkout Step 1."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login(Config.SAUCEDEMO_USERNAME, Config.SAUCEDEMO_PASSWORD)

    products_page = ProductsPage(page)
    products_page.add_product_to_cart_by_name("Sauce Labs Backpack")
    products_page.navigate_to_cart()

    cart_page = CartPage(page)
    cart_page.proceed_to_checkout()
    return CheckoutPage(page)


@pytest.mark.checkout
@pytest.mark.regression
@pytest.mark.parametrize(
    "first_name,last_name,postal_code,expected_error",
    [
        ("", "Doe", "12345", "Error: First Name is required"),
        ("John", "", "12345", "Error: Last Name is required"),
        ("John", "Doe", "", "Error: Postal Code is required"),
    ],
    ids=["missing_first_name", "missing_last_name", "missing_postal_code"],
)
def test_checkout_information_validation(
    checkout_step_one: CheckoutPage,
    first_name: str,
    last_name: str,
    postal_code: str,
    expected_error: str,
) -> None:
    """Verifies that mandatory customer fields display corresponding error banners."""
    checkout_step_one.fill_customer_information(first_name, last_name, postal_code)
    checkout_step_one.continue_checkout()

    assert checkout_step_one.get_error_message() == expected_error


@pytest.mark.checkout
@pytest.mark.smoke
@pytest.mark.regression
def test_complete_checkout_successfully(checkout_step_one: CheckoutPage) -> None:
    """Verifies complete end-to-end checkout flow from information to order confirmation."""
    # Step 1: Submit valid customer details
    checkout_step_one.fill_customer_information("Jane", "Doe", "94043")
    checkout_step_one.continue_checkout()

    # Step 2: Overview validation
    assert "/checkout-step-two.html" in checkout_step_one.current_url
    assert checkout_step_one.get_overview_item_count() == 1
    assert "Item total: $29.99" in checkout_step_one.get_item_total_text()
    assert "Tax: $" in checkout_step_one.get_tax_text()
    assert "Total: $" in checkout_step_one.get_total_text()

    # Step 3: Finish and verify confirmation
    checkout_step_one.finish_checkout()
    assert "/checkout-complete.html" in checkout_step_one.current_url
    assert checkout_step_one.is_order_complete()
    assert checkout_step_one.get_confirmation_header() == "Thank you for your order!"


@pytest.mark.checkout
@pytest.mark.regression
def test_order_confirmation_content(checkout_step_one: CheckoutPage) -> None:
    """Verifies order confirmation message body and back home navigation element."""
    checkout_step_one.fill_customer_information("Jane", "Doe", "94043")
    checkout_step_one.continue_checkout()
    checkout_step_one.finish_checkout()

    assert checkout_step_one.is_order_complete()
    assert (
        "Your order has been dispatched"
        in checkout_step_one.get_confirmation_message()
    )
    assert checkout_step_one.back_home_button.is_visible()
