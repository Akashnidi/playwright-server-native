"""
utils/jira_notifier.py — Jira webhook payload builder.

Builds a consolidated, structured JSON payload from failed Pytest test records
and Jenkins build context environment variables for Jira Automation incoming webhooks.

Design constraints:
- Contains NO HTTP logic. Network delivery is handled exclusively by
  the Jenkins pipeline (curl) so that the webhook URL never enters the
  Python process environment.
- Never logs credential values.
- Safe to call locally (all Jenkins env-vars default gracefully).
"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.config import Config
from utils.logger import get_logger

logger = get_logger("jira-notifier")


def build_failure_payload(
    failed_records: List[Dict[str, Any]],
    total_tests: int,
    passed: int,
    failed: int,
    skipped: int,
) -> Dict[str, Any]:
    """
    Returns a JSON-serialisable dict representing a consolidated failure
    report suitable for dispatch to a Jira Automation incoming webhook.

    Jenkins build context is read from OS environment variables that the
    Jenkins pipeline injects before invoking pytest. When called locally
    (no Jenkins) all build fields default gracefully.

    :param failed_records: List of test record dicts whose status is FAILED.
    :param total_tests:    Total test count for the executed session.
    :param passed:         Number of tests that passed.
    :param failed:         Number of tests that failed.
    :param skipped:        Number of tests that were skipped.
    :return: Payload dict (caller writes it to disk; this function never
             performs I/O or network operations).
    """
    project_name: str = os.getenv("PROJECT_NAME", "playwright-server-native").strip()
    environment: str = os.getenv("EXECUTION_ENV", "AWS_EC2_JENKINS").strip()

    job_name: str = os.getenv("JOB_NAME", "playwright-server-native").strip()
    build_number: str = os.getenv("BUILD_NUMBER", "unknown").strip()
    build_url: str = os.getenv("BUILD_URL", "").strip()
    git_branch: str = os.getenv("GIT_BRANCH", "unknown").strip()
    git_commit: str = os.getenv("GIT_COMMIT", "unknown").strip()
    timestamp: str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    ticket_title: str = (
        f"[QA Automation Failure] {project_name} | Build #{build_number} | {failed} Tests Failed"
    )

    build_section: Dict[str, str] = {
        "job_name":     job_name,
        "build_number": build_number,
        "build_url":    build_url,
        "git_branch":   git_branch,
        "git_commit":   git_commit,
        "timestamp":    timestamp,
    }

    summary_section: Dict[str, int] = {
        "total_tests": total_tests,
        "passed":      passed,
        "failed":      failed,
        "skipped":     skipped,
    }

    failures_section: List[Dict[str, Any]] = []
    for record in failed_records:
        screenshot_artifact: str = record.get("Screenshot", "")
        jenkins_screenshot_url: str = ""

        # Construct full Jenkins artifact URL with clean slash handling
        if build_url and screenshot_artifact:
            jenkins_screenshot_url = (
                f"{build_url.rstrip('/')}/artifact/{screenshot_artifact.lstrip('/')}"
            )

        failures_section.append(
            {
                "test_name":              record.get("Test Name", ""),
                "test_file":              record.get("Test File", ""),
                "error_type":             record.get("Error Type", "TestFailure"),
                "error_message":          record.get("Failure Message", ""),
                "full_traceback":         record.get("Full Traceback", ""),
                "duration_seconds":       record.get("Execution Duration (s)", 0.0),
                "screenshot_artifact":    screenshot_artifact,
                "jenkins_screenshot_url": jenkins_screenshot_url,
            }
        )

    return {
        "event":        "PLAYWRIGHT_TEST_FAILURE",
        "ticket_title": ticket_title,
        "project_name": project_name,
        "environment":  environment,
        "build":        build_section,
        "summary":      summary_section,
        "failures":     failures_section,
    }


def write_failures_json(
    failed_records: List[Dict[str, Any]],
    total_tests: int,
    passed: int,
    failed: int,
    skipped: int,
) -> Optional[Path]:
    """
    Builds the failure payload and writes it to ``Config.JIRA_FAILURES_JSON``.

    This is the only function in this module that performs file I/O.
    It is called once per Pytest session, inside ``pytest_sessionfinish``,
    only when at least one test has failed.

    :return: Absolute path of the written JSON file, or ``None`` if the
             write operation failed (error is logged; exception is not
             re-raised to avoid masking the real test failures).
    """
    try:
        payload = build_failure_payload(
            failed_records=failed_records,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=skipped,
        )

        output_path: Path = Config.JIRA_FAILURES_JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, mode="w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

        logger.info(
            f"Jira failure payload written: {output_path} "
            f"({failed} failure(s) recorded)"
        )
        return output_path

    except Exception as exc:
        logger.error(f"Failed to write Jira failure payload: {exc}")
        return None
