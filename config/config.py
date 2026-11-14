"""
Central configuration for playwright-server-native.
Provides execution parameters, target URLs, timeouts, project paths,
and centralized credential handling.
All values support overrides via environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load environment variables from .env if present ─────────────
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
env_path: Path = PROJECT_ROOT / ".env"
if env_path.is_file():
    # override=False ensures OS / Jenkins environment variables take precedence
    load_dotenv(dotenv_path=env_path, override=False)


class Config:
    # ── Project Directory Paths ─────────────────────────────────
    PROJECT_ROOT: Path = PROJECT_ROOT
    SCREENSHOTS_DIR: Path = PROJECT_ROOT / "screenshots"
    LOGS_DIR: Path = PROJECT_ROOT / "logs"
    REPORTS_DIR: Path = PROJECT_ROOT / "reports"

    # ── Target Application ─────────────────────────────────────
    BASE_URL: str = os.getenv("BASE_URL", "https://www.saucedemo.com")

    # ── Centralized Credentials ────────────────────────────────
    SAUCEDEMO_USERNAME: str = os.getenv("SAUCEDEMO_USERNAME", "").strip()
    SAUCEDEMO_PASSWORD: str = os.getenv("SAUCEDEMO_PASSWORD", "").strip()

    # ── Browser Execution Settings ─────────────────────────────
    BROWSER: str = os.getenv("BROWSER", "chromium").lower()
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() in ("true", "1", "yes")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))

    # ── Timeouts (milliseconds) ────────────────────────────────
    TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "15000"))
    NAVIGATION_TIMEOUT: int = int(os.getenv("NAVIGATION_TIMEOUT", "30000"))

    # ── Viewport ───────────────────────────────────────────────
    VIEWPORT = {
        "width": int(os.getenv("VIEWPORT_WIDTH", "1280")),
        "height": int(os.getenv("VIEWPORT_HEIGHT", "720")),
    }

    @classmethod
    def validate_credentials(cls) -> None:
        """
        Validates that required credentials are provided.
        Raises ValueError with a clear, safe error message (never exposing secret values).
        """
        missing = []
        if not cls.SAUCEDEMO_USERNAME:
            missing.append("SAUCEDEMO_USERNAME")
        if not cls.SAUCEDEMO_PASSWORD:
            missing.append("SAUCEDEMO_PASSWORD")

        if missing:
            missing_names = ", ".join(missing)
            raise ValueError(
                f"Missing required credential environment variable(s): {missing_names}. "
                "Ensure they are set in the .env file for local runs or as OS/Jenkins environment variables."
            )

    @classmethod
    def reload_credentials(cls) -> None:
        """Reloads credentials from the current environment and .env."""
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path, override=False)
        cls.SAUCEDEMO_USERNAME = os.getenv("SAUCEDEMO_USERNAME", "").strip()
        cls.SAUCEDEMO_PASSWORD = os.getenv("SAUCEDEMO_PASSWORD", "").strip()


# Ensure essential directories exist at runtime
Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
