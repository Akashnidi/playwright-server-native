"""
tests/test_cart.py — Test suite for SauceDemo shopping cart operations.
Covers cart item verification, removing products, continuing shopping, and checkout navigation.
"""
import pytest
from playwright.sync_api import Page
from config.config import Config
from pages import LoginPage, ProductsPage, CartPage


@pytest.fixture
def cart_page_with_item(page: Page) -> CartPage:
    """Fixture that logs in, adds an item to the cart, and navigates to the cart page."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login(Config.SAUCEDEMO_USERNAME, Config.SAUCEDEMO_PASSWORD)

    products_page = ProductsPage(page)
    products_page.add_product_to_cart_by_name("Sauce Labs Backpack")
    products_page.navigate_to_cart()
    return CartPage(page)


@pytest.mark.cart
@pytest.mark.regression
def test_added_product_appears_in_cart(cart_page_with_item: CartPage) -> None:
    """Verifies that an added item is present in the cart view."""
    assert "/cart.html" in cart_page_with_item.current_url
    assert cart_page_with_item.get_cart_item_count() == 1
    assert "Sauce Labs Backpack" in cart_page_with_item.get_cart_item_names()


@pytest.mark.cart
@pytest.mark.regression
def test_remove_product_from_cart(cart_page_with_item: CartPage) -> None:
    """Verifies that clicking Remove inside the cart clears the item row."""
    assert cart_page_with_item.get_cart_item_count() == 1
    cart_page_with_item.remove_item_by_name("Sauce Labs Backpack")
    assert cart_page_with_item.get_cart_item_count() == 0
    assert "Sauce Labs Backpack" not in cart_page_with_item.get_cart_item_names()


@pytest.mark.cart
@pytest.mark.regression
def test_continue_shopping_navigation(cart_page_with_item: CartPage, page: Page) -> None:
    """Verifies that the Continue Shopping button navigates back to the products catalog."""
    cart_page_with_item.continue_shopping()
    products_page = ProductsPage(page)
    assert "/inventory.html" in products_page.current_url
    assert products_page.get_title_text() == "Products"


@pytest.mark.cart
@pytest.mark.regression
@pytest.mark.smoke
def test_proceed_to_checkout_navigation(cart_page_with_item: CartPage) -> None:
    """Verifies that clicking Checkout navigates to Step 1 of the checkout flow."""
    cart_page_with_item.proceed_to_checkout()
    assert "/checkout-step-one.html" in cart_page_with_item.current_url
