"""
pages/products_page.py — Page Object for SauceDemo inventory/products catalog page.
Encapsulates product listings, item retrieval, sorting, add-to-cart, and cart badge.
"""
from typing import List
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class ProductsPage(BasePage):
    """Page object representing the SauceDemo Products page."""

    URL_PATH = "/inventory.html"

    def __init__(self, page: Page):
        super().__init__(page)
        # Structural locators
        self.title: Locator = page.locator('[data-test="title"]')
        self.inventory_container: Locator = page.locator('[data-test="inventory-container"]')
        self.inventory_items: Locator = page.locator('[data-test="inventory-item"]')
        self.item_names: Locator = page.locator('[data-test="inventory-item-name"]')
        self.item_prices: Locator = page.locator('[data-test="inventory-item-price"]')
        self.sort_select: Locator = page.locator('[data-test="product-sort-container"]')
        self.cart_link: Locator = page.locator('[data-test="shopping-cart-link"]')
        self.cart_badge: Locator = page.locator('[data-test="shopping-cart-badge"]')

    def load(self) -> None:
        """Navigates directly to the inventory page."""
        self.navigate_to(self.URL_PATH)

    def get_title_text(self) -> str:
        """Returns the page title text (e.g. 'Products')."""
        return self.title.inner_text().strip()

    def get_product_count(self) -> int:
        """Returns the total number of inventory items displayed."""
        return self.inventory_items.count()

    def get_all_product_names(self) -> List[str]:
        """Returns a list of all product titles currently visible."""
        return [name.strip() for name in self.item_names.all_text_contents()]

    def get_all_product_prices(self) -> List[float]:
        """Returns a list of all product prices parsed as numeric floats."""
        raw_prices = self.item_prices.all_text_contents()
        return [float(p.replace("$", "").strip()) for p in raw_prices]

    def add_product_to_cart_by_name(self, product_name: str) -> None:
        """
        Adds a product to the cart by targeting its specific item container.
        """
        item = self.inventory_items.filter(
            has=self.page.locator('[data-test="inventory-item-name"]', has_text=product_name)
        )
        add_button = item.locator("button")
        add_button.click()

    def remove_product_by_name(self, product_name: str) -> None:
        """
        Removes a product from the inventory view if it was previously added.
        """
        item = self.inventory_items.filter(
            has=self.page.locator('[data-test="inventory-item-name"]', has_text=product_name)
        )
        remove_button = item.locator("button")
        remove_button.click()

    def select_sort_option(self, option_value: str) -> None:
        """
        Sorts the products list by dropdown value:
        - 'az'   : Name (A to Z)
        - 'za'   : Name (Z to A)
        - 'lohi' : Price (low to high)
        - 'hilo' : Price (high to low)
        """
        self.sort_select.select_option(value=option_value)

    def get_cart_badge_count(self) -> int:
        """Returns the count displayed on the cart badge, or 0 if badge is not present."""
        if self.cart_badge.is_visible():
            badge_text = self.cart_badge.inner_text().strip()
            return int(badge_text) if badge_text.isdigit() else 0
        return 0

    def navigate_to_cart(self) -> None:
        """Navigates to the shopping cart page via the cart icon."""
        self.cart_link.click()
