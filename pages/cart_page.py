"""
pages/cart_page.py — Page Object for SauceDemo shopping cart view.
Encapsulates cart items inspection, removal, continuing shopping, and checkout navigation.
"""
from typing import List
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class CartPage(BasePage):
    """Page object representing the SauceDemo Shopping Cart page."""

    URL_PATH = "/cart.html"

    def __init__(self, page: Page):
        super().__init__(page)
        # Structural locators
        self.title: Locator = page.locator('[data-test="title"]')
        self.cart_items: Locator = page.locator('[data-test="inventory-item"]')
        self.cart_item_names: Locator = page.locator('[data-test="inventory-item-name"]')
        self.cart_item_prices: Locator = page.locator('[data-test="inventory-item-price"]')
        self.continue_shopping_button: Locator = page.locator('[data-test="continue-shopping"]')
        self.checkout_button: Locator = page.locator('[data-test="checkout"]')

    def load(self) -> None:
        """Navigates directly to the cart page."""
        self.navigate_to(self.URL_PATH)

    def get_title_text(self) -> str:
        """Returns the page title text (e.g. 'Your Cart')."""
        return self.title.inner_text().strip()

    def get_cart_item_count(self) -> int:
        """Returns the count of distinct item rows present in the cart."""
        return self.cart_items.count()

    def get_cart_item_names(self) -> List[str]:
        """Returns a list of all product names currently in the cart."""
        return [name.strip() for name in self.cart_item_names.all_text_contents()]

    def remove_item_by_name(self, product_name: str) -> None:
        """Removes an item from the cart by targeting its specific item row."""
        item = self.cart_items.filter(
            has=self.page.locator('[data-test="inventory-item-name"]', has_text=product_name)
        )
        remove_button = item.locator("button")
        remove_button.click()

    def continue_shopping(self) -> None:
        """Clicks the Continue Shopping button to return to the catalog."""
        self.continue_shopping_button.click()

    def proceed_to_checkout(self) -> None:
        """Clicks Checkout to navigate to the information step."""
        self.checkout_button.click()
