"""
conftest.py — Pytest fixtures and hooks for playwright-server-native.

Provides:
- Centralized configuration fixture (app_config)
- Browser launch configuration with headless/headed support
- Browser context configuration with base URL, viewport, and timeouts
- Graceful page lifecycle management and shutdown
- Automated failure screenshot capture hook with HTML report embedding
- Automated CSV report generation across all test executions
"""
import csv
from typing import Generator
import pytest
from playwright.sync_api import BrowserContext, Page
from config.config import Config
from utils.logger import get_logger
from utils.screenshot import take_screenshot

logger = get_logger("conftest")


# ── Configuration Fixture ──────────────────────────────────────────
@pytest.fixture(scope="session")
def app_config():
    """Provides access to central application configuration."""
    return Config


# ── Playwright Launch and Context Fixtures ─────────────────────────
@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args, pytestconfig):
    """
    Overrides pytest-playwright browser launch arguments.
    Respects CLI --headed flag; otherwise falls back to Config.HEADLESS.
    """
    launch_args = dict(browser_type_launch_args)
    is_headed = pytestconfig.getoption("--headed", default=False)
    launch_args["headless"] = False if is_headed else Config.HEADLESS

    if Config.SLOW_MO > 0:
        launch_args["slow_mo"] = Config.SLOW_MO

    logger.info(
        f"Browser launch parameters: browser={Config.BROWSER}, "
        f"headless={launch_args['headless']}, slow_mo={launch_args.get('slow_mo', 0)}"
    )
    return launch_args


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """
    Overrides pytest-playwright browser context arguments.
    Injects central base URL, default viewport, and SSL bypass.
    """
    context_args = dict(browser_context_args)
    context_args["base_url"] = Config.BASE_URL
    context_args["viewport"] = Config.VIEWPORT
    context_args["ignore_https_errors"] = True
    logger.info(
        f"Browser context parameters: base_url={Config.BASE_URL}, "
        f"viewport={Config.VIEWPORT}"
    )
    return context_args


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """
    Function-scoped Page fixture.
    Configures timeouts, logs lifecycle, and ensures graceful teardown.
    """
    logger.info("Initializing Playwright page...")
    new_page = context.new_page()
    new_page.set_default_timeout(Config.TIMEOUT)
    new_page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)

    try:
        yield new_page
    finally:
        if not new_page.is_closed():
            logger.info("Gracefully closing Playwright page...")
            new_page.close()


# ── Session Lifecycle Hooks (CSV & Artifact Collection) ─────────────
def pytest_sessionstart(session):
    """Initializes result collection dictionary for CSV reporting."""
    session.test_records = {}
    Config.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    Config.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    Config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    Config.validate_credentials()


# ── Failure Detection, Screenshot Hook & Result Record ──────────────
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Captures test results for CSV generation and triggers failure screenshots.
    Integrates failure screenshot embedding into pytest-html reports.
    """
    outcome = yield
    report = outcome.get_result()

    records = getattr(item.session, "test_records", None)
    if records is None:
        item.session.test_records = {}
        records = item.session.test_records

    nodeid = item.nodeid
    test_name = item.name

    try:
        test_file = str(item.path.relative_to(Config.PROJECT_ROOT))
    except Exception:
        test_file = str(item.location[0])

    # Record setup failures or skips
    if report.when == "setup":
        if report.skipped:
            records[nodeid] = {
                "Test Name": test_name,
                "Test File": test_file,
                "Execution Status": "SKIPPED",
                "Execution Duration (s)": round(report.duration, 4),
                "Failure Message": report.longreprtext if report.longreprtext else "",
            }
        elif report.failed:
            records[nodeid] = {
                "Test Name": test_name,
                "Test File": test_file,
                "Execution Status": "FAILED",
                "Execution Duration (s)": round(report.duration, 4),
                "Failure Message": (
                    report.longreprtext.splitlines()[-1]
                    if report.longreprtext
                    else "Setup failure"
                ),
            }

    # Record test call execution
    elif report.when == "call":
        status = "FAILED" if report.failed else "PASSED"
        error_msg = ""

        if report.failed:
            logger.error(f"Test failed: {item.nodeid}")

            # Extract concise failure reason
            if report.longreprtext:
                err_lines = [
                    line.strip()[2:].strip()
                    if line.strip().startswith("E ")
                    else line.strip()
                    for line in report.longreprtext.splitlines()
                    if line.strip().startswith("E ")
                    and ("assert" in line.lower() or "error" in line.lower())
                ]
                if not err_lines:
                    err_lines = [
                        line.strip()[2:].strip()
                        if line.strip().startswith("E ")
                        else line.strip()
                        for line in report.longreprtext.splitlines()
                        if line.strip().startswith("E ")
                    ]
                error_msg = (
                    err_lines[0]
                    if err_lines
                    else report.longreprtext.splitlines()[-1]
                )
            else:
                error_msg = "Test failed"

            # Capture failure screenshot
            page_instance = item.funcargs.get("page")
            if page_instance:
                screenshot_path = take_screenshot(
                    page=page_instance,
                    name=f"FAIL_{item.name}",
                )
                if screenshot_path and screenshot_path.exists():
                    logger.info(f"Captured failure screenshot: {screenshot_path}")

                    # Attach to pytest-html if present
                    try:
                        import pytest_html

                        extra = getattr(report, "extra", [])
                        extra.append(pytest_html.extras.image(str(screenshot_path)))
                        report.extra = extra
                    except Exception:
                        pass
            else:
                logger.warning(
                    f"No active 'page' fixture available for {item.name}; screenshot skipped."
                )

        records[nodeid] = {
            "Test Name": test_name,
            "Test File": test_file,
            "Execution Status": status,
            "Execution Duration (s)": round(report.duration, 4),
            "Failure Message": error_msg,
        }

    # Record teardown failures
    elif report.when == "teardown":
        if report.failed and nodeid in records:
            records[nodeid]["Execution Status"] = "FAILED"
            if not records[nodeid]["Failure Message"]:
                records[nodeid]["Failure Message"] = "Teardown failure"


# ── Session Finish Hook (Generate CSV Report) ──────────────────────
def pytest_sessionfinish(session, exitstatus):
    """
    Writes collected test execution results to reports/report.csv.
    Guaranteed to execute even if tests fail.
    """
    if getattr(session, "_csv_written", False):
        return
    session._csv_written = True

    records = getattr(session, "test_records", {})
    if not records:
        return

    csv_path = Config.REPORTS_DIR / "report.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "Test Name",
        "Test File",
        "Execution Status",
        "Execution Duration (s)",
        "Failure Message",
    ]

    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in records.values():
                writer.writerow(record)
        logger.info(
            f"Generated CSV report: {csv_path} ({len(records)} test records)"
        )
    except Exception as exc:
        logger.error(f"Failed to generate CSV report: {exc}")
