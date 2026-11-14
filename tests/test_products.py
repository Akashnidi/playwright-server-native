"""
tests/test_products.py — Test suite for SauceDemo catalog, item details, and sorting.
"""
import pytest
from playwright.sync_api import Page
from config.config import Config
from pages import LoginPage, ProductsPage


@pytest.fixture
def products_page(page: Page) -> ProductsPage:
    """Fixture that logs in using centralized credentials and returns an active ProductsPage."""
    login_page = LoginPage(page)
    login_page.load()
    login_page.login(Config.SAUCEDEMO_USERNAME, Config.SAUCEDEMO_PASSWORD)
    return ProductsPage(page)


@pytest.mark.inventory
@pytest.mark.smoke
def test_products_page_displays_after_login(products_page: ProductsPage) -> None:
    """Verifies that the products page loads properly after successful login."""
    assert "/inventory.html" in products_page.current_url
    assert products_page.get_title_text() == "Products"
    assert products_page.get_product_count() > 0


@pytest.mark.inventory
@pytest.mark.regression
def test_product_count(products_page: ProductsPage) -> None:
    """Verifies the catalog contains exactly 6 products."""
    assert products_page.get_product_count() == 6


@pytest.mark.inventory
@pytest.mark.regression
def test_product_names_and_prices_retrieved(products_page: ProductsPage) -> None:
    """Verifies product names and numeric prices are populated correctly."""
    names = products_page.get_all_product_names()
    prices = products_page.get_all_product_prices()

    assert len(names) == 6
    assert "Sauce Labs Backpack" in names
    assert "Sauce Labs Bike Light" in names
    assert len(prices) == 6
    assert all(isinstance(price, float) and price > 0.0 for price in prices)


@pytest.mark.inventory
@pytest.mark.regression
def test_add_product_to_cart(products_page: ProductsPage) -> None:
    """Verifies adding a product updates the cart badge count to 1."""
    assert products_page.get_cart_badge_count() == 0
    products_page.add_product_to_cart_by_name("Sauce Labs Backpack")
    assert products_page.get_cart_badge_count() == 1


@pytest.mark.inventory
@pytest.mark.regression
def test_remove_product_from_cart(products_page: ProductsPage) -> None:
    """Verifies removing an added product from the catalog page resets the cart badge."""
    products_page.add_product_to_cart_by_name("Sauce Labs Backpack")
    assert products_page.get_cart_badge_count() == 1

    products_page.remove_product_by_name("Sauce Labs Backpack")
    assert products_page.get_cart_badge_count() == 0


@pytest.mark.inventory
@pytest.mark.regression
@pytest.mark.parametrize(
    "sort_option,sort_type,is_reversed",
    [
        ("az", "name", False),
        ("za", "name", True),
        ("lohi", "price", False),
        ("hilo", "price", True),
    ],
    ids=["name_a_to_z", "name_z_to_a", "price_low_to_high", "price_high_to_low"],
)
def test_product_sorting(
    products_page: ProductsPage, sort_option: str, sort_type: str, is_reversed: bool
) -> None:
    """Verifies that catalog items sort properly by name and price in ascending and descending orders."""
    products_page.select_sort_option(sort_option)

    if sort_type == "name":
        names = products_page.get_all_product_names()
        assert names == sorted(names, reverse=is_reversed)
    elif sort_type == "price":
        prices = products_page.get_all_product_prices()
        assert prices == sorted(prices, reverse=is_reversed)
