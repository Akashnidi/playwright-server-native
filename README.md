# playwright-server-native

A Python Playwright UI automation framework targeting [Sauce Demo](https://www.saucedemo.com/).

This project is a **proof-of-concept** for running Playwright tests directly on an AWS EC2 Jenkins server — without Docker.

---

## Table of Contents

1. [Requirements](#requirements)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Running Tests](#running-tests)
5. [Reports](#reports)
6. [Logging](#logging)
7. [Compatibility Notes](#compatibility-notes)

---

## Requirements

| Tool | Minimum version |
|------|----------------|
| Python | 3.9 or 3.13 |
| pip | 23+ |
| Git | 2.x |

> **EC2 / Jenkins note**: The pipeline expects Python to be installed natively on the EC2 instance (`python3.9` or `python3.13`). No Docker is involved.

---

## Project Structure

```
playwright-server-native/
├── tests/          # Test modules (test_*.py)
├── pages/          # Page Object Model classes
├── utils/          # Shared helpers (logging, CSV writer, etc.)
├── config/         # Environment config and constants
├── reports/        # Generated HTML and CSV reports (git-ignored)
├── logs/           # pytest log files (git-ignored)
├── screenshots/    # Failure screenshots (git-ignored)
├── conftest.py     # pytest fixtures and hooks
├── pytest.ini      # pytest configuration
├── requirements.txt
├── README.md
└── .gitignore
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/playwright-server-native.git
cd playwright-server-native
```

### 2. Create and activate a virtual environment

**Python 3.9**
```bash
python3.9 -m venv .venv
source .venv/bin/activate        # Linux / macOS / EC2
# .venv\Scripts\activate.bat     # Windows
```

**Python 3.13**
```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install Playwright browsers

```bash
playwright install chromium
# To install all browsers:
# playwright install
```

> On a headless EC2 instance install system dependencies first:
> ```bash
> playwright install-deps chromium
> ```

---

## Running Tests

### Smoke suite (headless, default)

```bash
pytest -m smoke
```

### Full regression suite with HTML + CSV reports

```bash
pytest -m regression \
    --html=reports/report.html \
    --self-contained-html
```

> CSV reporting will be wired in a later phase via a custom pytest plugin in `utils/`.

### Run all tests verbosely

```bash
pytest -v
```

### Run against a specific browser

```bash
pytest --browser chromium
pytest --browser firefox
pytest --browser webkit
```

### Headed mode (useful for local debugging)

```bash
pytest --headed
```

---

## Reports

| File | Description |
|------|-------------|
| `reports/report.html` | pytest-html interactive report |
| `reports/results.csv` | CSV summary (Phase 2+) |

Reports are **not committed** to Git (see `.gitignore`). They are published as Jenkins build artifacts.

---

## Logging

pytest captures logs automatically according to `pytest.ini`:

| Output | Level | Location |
|--------|-------|----------|
| Console | INFO | terminal |
| File | DEBUG | `logs/pytest.log` |

Log files are **not committed** to Git.

---

## Compatibility Notes

| Package | Version | Why |
|---------|---------|-----|
| `pytest` | 8.3.4 | Stable on 3.9–3.13 |
| `playwright` | 1.49.1 | Last 1.4x series; supports 3.9–3.13 |
| `pytest-playwright` | 0.6.2 | Aligned with playwright 1.49.x |
| `pytest-html` | 4.1.1 | 4.x API; supports 3.9–3.13 |
| `pytest-metadata` | 3.1.1 | Required by pytest-html 4.x |

Python's built-in `csv` and `logging` modules are used for CSV and log output — no extra packages needed.

---

## Development Phases

| Phase | Scope |
|-------|-------|
| **1 — Foundation** ✅ | Folder structure, dependencies, config |
| 2 — Browser fixtures | conftest.py fixtures, screenshots on failure |
| 3 — Page Objects | POM classes for Sauce Demo |
| 4 — Test cases | Login, inventory, cart, checkout suites |
| 5 — Reporting | CSV writer, enhanced HTML report |
| 6 — Jenkins pipeline | Jenkinsfile, artifact publishing, cleanup |
