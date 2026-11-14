"""
Screenshot capture utility for Playwright pages.
Saves timestamped PNG files in the screenshots directory.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.sync_api import Page
from config.config import Config
from utils.logger import get_logger

logger = get_logger("screenshot")


def take_screenshot(
    page: Page,
    name: str = "screenshot",
    output_dir: Optional[Path] = None,
) -> Optional[Path]:
    """
    Captures a full-page screenshot and saves it as a timestamped PNG.

    :param page: Active Playwright Page instance
    :param name: Base identifier for the screenshot file
    :param output_dir: Optional directory override; defaults to Config.SCREENSHOTS_DIR
    :return: Path to the saved file or None if capture was not possible
    """
    try:
        if page.is_closed():
            logger.warning("Cannot take screenshot: Page is already closed.")
            return None

        target_dir = output_dir or Config.SCREENSHOTS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)

        safe_name = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = target_dir / f"{safe_name}_{timestamp}.png"

        page.screenshot(path=str(file_path), full_page=True)
        logger.info(f"Screenshot successfully saved: {file_path}")
        return file_path
    except Exception as exc:
        logger.error(f"Failed to capture screenshot '{name}': {exc}")
        return None
