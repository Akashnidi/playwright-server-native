"""
pages/checkout_page.py — Page Object for SauceDemo checkout workflow.
Encapsulates Step 1 (information), Step 2 (overview/finish), and Order Complete.
"""
from playwright.sync_api import Page, Locator
from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """Page object managing SauceDemo multi-step checkout workflow."""

    STEP_ONE_PATH = "/checkout-step-one.html"
    STEP_TWO_PATH = "/checkout-step-two.html"
    COMPLETE_PATH = "/checkout-complete.html"

    def __init__(self, page: Page):
        super().__init__(page)

        # ── Step 1: Customer Information ─────────────────────────
        self.first_name_input: Locator = page.locator('[data-test="firstName"]')
        self.last_name_input: Locator = page.locator('[data-test="lastName"]')
        self.postal_code_input: Locator = page.locator('[data-test="postalCode"]')
        self.continue_button: Locator = page.locator('[data-test="continue"]')
        self.cancel_button: Locator = page.locator('[data-test="cancel"]')
        self.error_message_container: Locator = page.locator('[data-test="error"]')

        # ── Step 2: Overview & Summary ───────────────────────────
        self.overview_items: Locator = page.locator('[data-test="inventory-item"]')
        self.item_total_label: Locator = page.locator('[data-test="subtotal-label"]')
        self.tax_label: Locator = page.locator('[data-test="tax-label"]')
        self.total_label: Locator = page.locator('[data-test="total-label"]')
        self.finish_button: Locator = page.locator('[data-test="finish"]')

        # ── Step 3: Complete & Confirmation ──────────────────────
        self.complete_header: Locator = page.locator('[data-test="complete-header"]')
        self.complete_text: Locator = page.locator('[data-test="complete-text"]')
        self.back_home_button: Locator = page.locator('[data-test="back-to-products"]')

    # ── Step 1 Actions ───────────────────────────────────────────
    def fill_customer_information(
        self, first_name: str, last_name: str, postal_code: str
    ) -> None:
        """Fills all fields on checkout step 1."""
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)

    def continue_checkout(self) -> None:
        """Clicks Continue to advance to Step 2."""
        self.continue_button.click()

    def get_error_message(self) -> str:
        """Returns error text if step 1 validation fails."""
        return self.error_message_container.inner_text().strip()

    # ── Step 2 Actions ───────────────────────────────────────────
    def get_overview_item_count(self) -> int:
        """Returns the number of line items listed on step 2 overview."""
        return self.overview_items.count()

    def get_item_total_text(self) -> str:
        """Returns the item total string (e.g. 'Item total: $29.99')."""
        return self.item_total_label.inner_text().strip()

    def get_tax_text(self) -> str:
        """Returns the tax total string (e.g. 'Tax: $2.40')."""
        return self.tax_label.inner_text().strip()

    def get_total_text(self) -> str:
        """Returns the grand total string (e.g. 'Total: $32.39')."""
        return self.total_label.inner_text().strip()

    def finish_checkout(self) -> None:
        """Clicks Finish on Step 2 to submit the order."""
        self.finish_button.click()

    # ── Confirmation Actions ─────────────────────────────────────
    def get_confirmation_header(self) -> str:
        """Returns the order confirmation header text."""
        return self.complete_header.inner_text().strip()

    def get_confirmation_message(self) -> str:
        """Returns the order confirmation detailed body text."""
        return self.complete_text.inner_text().strip()

    def is_order_complete(self) -> bool:
        """Verifies if the confirmation header is visible."""
        return self.complete_header.is_visible()
