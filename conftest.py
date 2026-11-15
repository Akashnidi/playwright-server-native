"""
conftest.py — Pytest fixtures and hooks for playwright-server-native.

Provides:
- Centralized configuration fixture (app_config)
- Browser launch configuration with headless/headed support
- Browser context configuration with base URL, viewport, and timeouts
- Graceful page lifecycle management and shutdown
- Automated failure screenshot capture hook with HTML report embedding
- Automated CSV report generation across all test executions
- Automated Jira failure payload generation (reports/failures.json)
"""
import csv
from typing import Generator
import pytest
from playwright.sync_api import BrowserContext, Page
from config.config import Config
from utils.logger import get_logger
from utils.screenshot import take_screenshot
from utils.jira_notifier import write_failures_json

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
                "Error Type": "",
                "Full Traceback": "",
                "Screenshot": "",
            }
        elif report.failed:
            setup_error_type = ""
            if call.excinfo:
                setup_error_type = getattr(call.excinfo, "typename", "") or call.excinfo.type.__name__
            if not setup_error_type and report.longreprtext:
                for line in reversed(report.longreprtext.splitlines()):
                    if ":" in line and ("Error" in line.split(":")[0] or "Exception" in line.split(":")[0]):
                        setup_error_type = line.split(":")[0].strip().replace("E ", "")
                        break
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
                "Error Type": setup_error_type or "SetupFailure",
                "Full Traceback": report.longreprtext if report.longreprtext else "",
                "Screenshot": "",
            }

    # Record test call execution
    elif report.when == "call":
        status = "FAILED" if report.failed else "PASSED"
        error_msg = ""
        error_type = ""
        full_tb = ""
        screenshot_name = ""  # Relative filename stored for Jira payload reference

        if report.failed:
            logger.error(f"Test failed: {item.nodeid}")
            full_tb = report.longreprtext if report.longreprtext else ""

            # Extract exception type (e.g. AssertionError, TimeoutError)
            if call.excinfo:
                error_type = getattr(call.excinfo, "typename", "") or call.excinfo.type.__name__
            if not error_type and full_tb:
                for line in reversed(full_tb.splitlines()):
                    if ":" in line and ("Error" in line.split(":")[0] or "Exception" in line.split(":")[0]):
                        error_type = line.split(":")[0].strip().replace("E ", "")
                        break
            if not error_type:
                error_type = "AssertionError" if "assert" in full_tb.lower() else "TestFailure"

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

            # Capture failure screenshot and retain the relative path for
            # the Jira failure payload (screenshots/<filename>).
            page_instance = item.funcargs.get("page")
            if page_instance:
                screenshot_path = take_screenshot(
                    page=page_instance,
                    name=f"FAIL_{item.name}",
                )
                if screenshot_path and screenshot_path.exists():
                    logger.info(f"Captured failure screenshot: {screenshot_path}")
                    # Store relative path so the Jira payload references a
                    # portable Jenkins artifact path, not an absolute server path.
                    try:
                        screenshot_name = str(
                            screenshot_path.relative_to(Config.PROJECT_ROOT)
                        )
                    except ValueError:
                        screenshot_name = screenshot_path.name

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
            "Error Type": error_type,
            "Full Traceback": full_tb,
            "Screenshot": screenshot_name,  # Empty string when test passes
        }

    # Record teardown failures
    elif report.when == "teardown":
        if report.failed and nodeid in records:
            records[nodeid]["Execution Status"] = "FAILED"
            if not records[nodeid].get("Failure Message"):
                records[nodeid]["Failure Message"] = "Teardown failure"
            if not records[nodeid].get("Error Type"):
                teardown_err = ""
                if call.excinfo:
                    teardown_err = getattr(call.excinfo, "typename", "") or call.excinfo.type.__name__
                records[nodeid]["Error Type"] = teardown_err or "TeardownFailure"
            if not records[nodeid].get("Full Traceback") and report.longreprtext:
                records[nodeid]["Full Traceback"] = report.longreprtext


# ── Session Finish Hook (Generate CSV Report + Jira Failure Payload) ──
def pytest_sessionfinish(session, exitstatus):
    """
    Writes collected test execution results to reports/report.csv.
    When one or more tests have failed, also writes reports/failures.json
    so the Jenkins pipeline can optionally dispatch a Jira webhook.
    Guaranteed to execute even if tests fail.
    """
    if getattr(session, "_csv_written", False):
        return
    session._csv_written = True

    records = getattr(session, "test_records", {})
    if not records:
        return

    # ── CSV Report ────────────────────────────────────────────────
    csv_path = Config.REPORTS_DIR / "report.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    # CSV columns exclude the Screenshot key (HTML report already embeds it).
    csv_fieldnames = [
        "Test Name",
        "Test File",
        "Execution Status",
        "Execution Duration (s)",
        "Failure Message",
    ]

    try:
        with open(csv_path, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames, extrasaction="ignore")
            writer.writeheader()
            for record in records.values():
                writer.writerow(record)
        logger.info(
            f"Generated CSV report: {csv_path} ({len(records)} test records)"
        )
    except Exception as exc:
        logger.error(f"Failed to generate CSV report: {exc}")

    # ── Jira Failure Payload ──────────────────────────────────────
    # Collect session-level counts for the payload summary section.
    all_records = list(records.values())
    total_tests = len(all_records)
    passed_count  = sum(1 for r in all_records if r["Execution Status"] == "PASSED")
    failed_count  = sum(1 for r in all_records if r["Execution Status"] == "FAILED")
    skipped_count = sum(1 for r in all_records if r["Execution Status"] == "SKIPPED")
    failed_records = [r for r in all_records if r["Execution Status"] == "FAILED"]

    if failed_records:
        write_failures_json(
            failed_records=failed_records,
            total_tests=total_tests,
            passed=passed_count,
            failed=failed_count,
            skipped=skipped_count,
        )
    else:
        logger.info(
            "All tests passed — Jira failure payload not generated (nothing to report)."
        )
