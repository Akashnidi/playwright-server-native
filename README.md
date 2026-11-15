# playwright-server-native

An enterprise-grade Python UI automation framework using **Playwright** and **Pytest** to test the [SauceDemo](https://www.saucedemo.com/) web application.

This repository serves as a **Proof of Concept (POC)** for executing automated browser tests natively on an **AWS EC2 Jenkins agent without Docker**, featuring automated failure reporting and **Jenkins-to-Jira webhook integration for automatic Incident creation**.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [Prerequisites, System Dependencies and Browser Binaries](#3-prerequisites-system-dependencies-and-browser-binaries)
   - [3.1 System Prerequisites](#31-system-prerequisites)
   - [3.2 Python Dependencies](#32-python-dependencies)
   - [3.3 Playwright Browser Binaries](#33-playwright-browser-binaries)
   - [3.4 Linux System Libraries and Browser Prerequisites](#34-linux-system-libraries-and-browser-prerequisites)
   - [3.5 Binary and Dependency Storage Locations](#35-binary-and-dependency-storage-locations)
   - [3.6 Fresh EC2 Setup Checklist](#36-fresh-ec2-setup-checklist)
   - [3.7 Version and Compatibility Notes](#37-version-and-compatibility-notes)
4. [Architecture](#4-architecture)
5. [Project Structure](#5-project-structure)
6. [Test Coverage](#6-test-coverage)
7. [Local Setup Guide](#7-local-setup-guide)
8. [Configuration and Credentials](#8-configuration-and-credentials)
9. [AWS EC2 and Jenkins Setup & Configuration](#9-aws-ec2-and-jenkins-setup--configuration)
   - [9.1 AWS EC2 Infrastructure Setup](#91-aws-ec2-infrastructure-setup)
   - [9.2 Jenkins Installation and Initial Configuration](#92-jenkins-installation-and-initial-configuration)
   - [9.3 Jenkins Pipeline Job Configuration](#93-jenkins-pipeline-job-configuration)
   - [9.4 Jenkins Build Parameter (SEND_TO_JIRA)](#94-jenkins-build-parameter-send_to_jira)
   - [9.5 Jenkins Credentials Configuration](#95-jenkins-credentials-configuration)
   - [9.6 Jenkins Build Execution & Lifecycle](#96-jenkins-build-execution--lifecycle)
   - [9.7 Infrastructure, Networking and Cost Notes](#97-infrastructure-networking-and-cost-notes)
10. [Reporting and Execution Artifacts](#10-reporting-and-execution-artifacts)
11. [Jira Webhook Integration](#11-jira-webhook-integration)
    - [11.1 Integration Components & Flow](#111-integration-components--flow)
    - [11.2 Webhook Payload Specification](#112-webhook-payload-specification)
    - [11.3 Jira Automation Configuration (NOC Space)](#113-jira-automation-configuration-noc-space)
    - [11.4 Screenshot Artifact Links vs Attachments](#114-screenshot-artifact-links-vs-attachments)
12. [POC Validation & Build History](#12-poc-validation--build-history)
    - [12.1 Baseline Pipeline Verification (Build #1)](#121-baseline-pipeline-verification-build-1)
    - [12.2 Jira Integration & Incident Creation Verification (Builds #7, #8, #9)](#122-jira-integration--incident-creation-verification-builds-7-8-9)
13. [Future Enhancements](#13-future-enhancements)
14. [Limitations and Scope](#14-limitations-and-scope)

---

## 1. Project Overview

`playwright-server-native` demonstrates how to run scalable, headless UI test automation directly on server infrastructure (EC2) orchestrated through a CI/CD pipeline (Jenkins), backed by automated issue tracking in Atlassian Jira.

### Key Highlights:
- **Native Server Execution**: Runs directly on the host operating system without container overhead or nested virtualization issues.
- **Page Object Model (POM)**: Complete structural separation of web elements, page interactions, and test assertions.
- **Robust Locators**: Prioritizes standard SauceDemo `data-test` attributes and user-facing accessibility selectors.
- **Automated Failure Reporting**: Generates interactive HTML reports, machine-readable CSV summaries, detailed runtime logs, automated failure screenshots, and structured failure JSON data.
- **Jenkins-to-Jira Webhook Integration**: Consolidates all failure metrics from a test run into a single structured payload and sends it via an authenticated webhook to Atlassian Jira Automation.
- **Automatic Jira Incident Creation**: Automatically creates a dedicated Incident ticket in the Jira NOC space for failed builds when enabled, preventing multiple duplicate tickets per build.
- **Secure Credential Handling**: Strict credential isolation supporting local `.env` development and Jenkins Credentials Manager injection (`saucedemo-credentials`, `jira-webhook-url`) without exposing secrets in code, logs, or reports.

---

## 2. Technology Stack

All dependencies are explicitly pinned and verified for dual compatibility across **Python 3.9** (used on the target EC2 Jenkins runner) and **Python 3.13** (modern local development):

| Component | Technology | Version | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.9 / 3.13 | Core runtime environment |
| **Browser Engine** | Playwright | 1.49.1 | Synchronous browser automation engine |
| **Browser** | Chromium | Bundled with 1.49.1 | Headless browser execution binary |
| **Test Runner** | Pytest | 8.3.4 | Test orchestration and assertions |
| **Pytest Integration** | pytest-playwright | 0.6.2 | Playwright browser lifecycle fixtures for Pytest |
| **HTML Reporting** | pytest-html | 4.1.1 | Self-contained HTML test execution reporting |
| **Report Metadata** | pytest-metadata | 3.1.1 | Environment and package metadata for HTML reports |
| **Config / Secrets** | python-dotenv | 1.0.1 | `.env` variable loading for local development |
| **CI/CD Orchestration** | Jenkins | LTS | Declarative pipeline execution on EC2 |
| **Incident Tracking** | Atlassian Jira | Cloud (NOC Space) | Automated Incident creation via Jira Automation |
| **Version Control** | GitHub | Git 2.x | Source code management |
| **Host Infrastructure** | AWS EC2 | Amazon Linux 2023 | Native bare-metal execution host (No Docker) |

> Verified from [`requirements.txt`](requirements.txt). Python's built-in `csv`, `json`, and `logging` modules power reporting and Jira payload generation without introducing unnecessary third-party dependencies.

---

## 3. Prerequisites, System Dependencies and Browser Binaries

### 3.1 System Prerequisites

The following components represent the system software configurations required to run this framework:

#### AWS EC2 Jenkins Execution Host
| Component | POC Configuration | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Amazon Linux 2023 (x86_64) | Host server operating system |
| **Python** | 3.9.25 | Server-side Python runtime |
| **Java** | Java 21 (Amazon Corretto) | Required runtime for the Jenkins daemon |
| **Git** | 2.x+ | Source repository checkout |
| **Jenkins** | LTS | Pipeline orchestration server |
| **pip** | 23.x+ | Python package installer |
| **Virtual Environment** | `python3.9 -m venv` | Isolated Python test environment |

#### Local Development Host (Windows)
| Component | Minimum Version | Purpose |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 / 11 (or macOS / Linux) | Local developer workstation |
| **Python** | Python 3.9 or Python 3.13 | Local execution runtime |
| **Shell** | Windows PowerShell 5.1+ / PowerShell 7+ | Command-line execution |
| **Git** | Git for Windows 2.x+ | Source code version control |
| **Browser** | Playwright Chromium | Local headed/headless test execution |

---

### 3.2 Python Dependencies

The Python environment is strictly isolated using `venv` and driven by pinned dependencies in [`requirements.txt`](requirements.txt):

```text
pytest==8.3.4
playwright==1.49.1
pytest-playwright==0.6.2
pytest-html==4.1.1
pytest-metadata==3.1.1
python-dotenv==1.0.1
```

- **Isolation**: A dedicated `.venv` is created for every execution to prevent library pollution across builds.
- **Installation Command**:
  ```bash
  .venv/bin/python -m pip install -r requirements.txt
  ```

---

### 3.3 Playwright Browser Binaries

It is critical to distinguish between the Playwright Python library and the browser binaries:

1. **Playwright Python Package (`pip install playwright==1.49.1`)**: Installs the Python language bindings and the `playwright` CLI. It does **not** include the browser executables.
2. **Chromium Browser Binary**: Downloaded via `python -m playwright install chromium`. In Playwright 1.49.1, this provisions **Chromium build `1148` (Chromium 131.0.6778.33)**.
3. **Chromium Headless Shell (`chrome-headless-shell`)**: Playwright packages an optimized headless-only Chromium executable that strips unnecessary desktop GUI subsystems, significantly reducing memory consumption and CPU overhead during CI runs.
4. **FFmpeg Helper Binary**: Downloaded alongside Chromium to capture video recordings of test runs when enabled.

**Browser Binary Installation Command:**
```bash
python -m playwright install chromium
```

> **Jenkins Cache Note**: In the Jenkins pipeline, this command downloads browser binaries into the Jenkins user's home cache directory (`/var/lib/jenkins/.cache/ms-playwright`). Because the cache resides outside the workspace, browser downloads persist across pipeline runs rather than being re-downloaded every build.

---

### 3.4 Linux System Libraries and Browser Prerequisites

Chromium requires several underlying Linux shared libraries (`.so` files) for font configuration, rendering, graphics, NSS, and IPC messaging.

- **Risk**: If essential Linux libraries (e.g., `libnss3.so`, `libatk-1.0.so`, `libcups.so`, `libasound.so`, `libXcomposite.so`) are absent, Playwright will fail with errors such as:
  ```
  error while loading shared libraries: libX11.so.6: cannot open shared object file: No such file or directory
  ```
- **Diagnostic Inspection**: To inspect which shared libraries are missing from the installed Chromium executable on Linux, run:
  ```bash
  ldd /var/lib/jenkins/.cache/ms-playwright/chromium-1148/chrome-linux/chrome | grep "not found"
  ```
- **OS Package Status**: *The exact list of minimal system RPM packages installed on Amazon Linux 2023 for this host is pending full manual package audit.* Ensure standard font and graphic libraries (`libX11`, `nss`, `atk`, `cups-libs`, `alsa-lib`) are available via `dnf`.

---

### 3.5 Binary and Dependency Storage Locations

Observed directory structure on the Amazon Linux 2023 Jenkins server:

| Resource | Path on EC2 Server | Persistence Behavior |
| :--- | :--- | :--- |
| **Jenkins Workspace** | `/var/lib/jenkins/workspace/playwright-server-native` | Purged after build execution via `deleteDir()` |
| **Virtual Environment** | `/var/lib/jenkins/workspace/playwright-server-native/.venv` | Recreated fresh on each build |
| **Playwright Browser Cache** | `/var/lib/jenkins/.cache/ms-playwright` | **Persisted** across builds under the `jenkins` user home |
| **Jenkins Secrets** | `/var/lib/jenkins/secrets/initialAdminPassword` | Secure master initial password store |

---

### 3.6 Fresh EC2 Setup Checklist

Use this checklist when commissioning a new AWS EC2 instance for this framework:

- [ ] **EC2 Provisioning**: Launch an EC2 instance with Amazon Linux 2023 (x86_64, recommended instance type: `t3.medium` or larger).
- [ ] **Security Group Configuration**: Allow inbound SSH (port 22) and Jenkins UI (port 8080) restricted to trusted IP addresses.
- [ ] **Java 21 Installation**: Install Amazon Corretto 21 (`java-21-amazon-corretto`).
- [ ] **Python Installation**: Verify or install Python 3.9 (`python3.9`, `python3.9-pip`).
- [ ] **Git Installation**: Install `git` for repository cloning.
- [ ] **Jenkins Installation**: Install Jenkins via official RedHat/RPM repository, enable and start `jenkins.service`.
- [ ] **Jenkins Initial Setup**: Unlock Jenkins using `/var/lib/jenkins/secrets/initialAdminPassword`, install suggested plugins.
- [ ] **Virtual Environment Support**: Ensure `python3.9 -m venv` is functional.
- [ ] **Outbound Internet Access**: Verify instance can reach GitHub (`github.com`), PyPI (`pypi.org`), Playwright CDN (`playwright.azureedge.net`), and Jira Automation webhooks.
- [ ] **Linux Shared Libraries**: Verify that shared libraries required by Chromium are satisfied.
- [ ] **Playwright Browser Provisioning**: Verify Chromium installs successfully into `/var/lib/jenkins/.cache/ms-playwright`.
- [ ] **Jenkins Credentials**: Store `saucedemo-credentials` and `jira-webhook-url` in Jenkins Credentials Manager.
- [ ] **Pipeline Execution**: Configure and trigger the `playwright-server-native` Pipeline job with `SEND_TO_JIRA`.

---

### 3.7 Version and Compatibility Notes

| Category | Component & Version | Status |
| :--- | :--- | :--- |
| **Verified in POC** | Amazon Linux 2023 (AL2023 x86_64) | Tested & validated |
| **Verified in POC** | Python 3.9.25 | Tested & validated on EC2 |
| **Verified in POC** | Java 21 Amazon Corretto | Tested & validated on EC2 |
| **Verified in POC** | Playwright 1.49.1 / Chromium Build 1148 | Tested & validated |
| **Verified in POC** | Pytest 8.3.4, pytest-playwright 0.6.2, pytest-html 4.1.1 | Tested & validated |
| **Verified in POC** | python-dotenv 1.0.1 | Tested & validated |
| **Verified in POC** | Jira Automation Incoming Webhook / NOC Space | Tested & validated |
| **Recommended** | EC2 Instance Type: `t3.medium` (2 vCPU, 4GB RAM) | Recommended baseline for headless browser runs |
| **Recommended** | AWS Elastic IP (EIP) | Recommended to avoid changing Jenkins URLs |
| **Pending Verification** | Minimal standalone RPM package manifest for AL2023 | Requires further OS package audit |

---

## 4. Architecture

The end-to-end execution lifecycle follows a sequential flow from source control to artifact archiving and automated incident creation:

```
┌──────────┐     ┌─────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  GitHub  │ ──> │ Jenkins │ ──> │ Python Virtual Env  │ ──> │ Install Dependencies │
│ (Source) │     │ (Build) │     │     (.venv)         │     │  (requirements.txt)  │
└──────────┘     └─────────┘     └─────────────────────┘     └──────────────────────┘
                                                                        │
                                                                        ▼
┌──────────────────┐     ┌────────────────┐     ┌────────┐     ┌──────────────────────┐
│ Jenkins Artifacts│ <── │ Output Reports │ <── │ Pytest │ <── │ Playwright Chromium  │
│  (HTML/CSV/Logs) │     │  & Failures    │     │ Suite  │     │   (Native Binary)    │
└──────────────────┘     └────────────────┘     └────────┘     └──────────────────────┘
                                  │
                   [Failures Exist & SEND_TO_JIRA=true]
                                  │
                                  ▼
                     ┌───────────────────────────┐
                     │ Jenkins curl POST Webhook │
                     │  (reports/failures.json)  │
                     └───────────────────────────┘
                                  │
                                  ▼
                     ┌───────────────────────────┐
                     │ Jira Automation (Webhook) │
                     └───────────────────────────┘
                                  │
                                  ▼
                     ┌───────────────────────────┐
                     │ Create Incident in NOC    │
                     │       (e.g. NOC-12)       │
                     └───────────────────────────┘
```

### Execution Flow:
1. **GitHub Checkout**: Jenkins checks out the repository (`main` branch) containing the application code and declarative `Jenkinsfile`.
2. **Environment Isolation**: Jenkins provisions an isolated Python virtual environment (`.venv`) using the host's native `python3.9`.
3. **Dependency & Browser Installation**: `pip` installs pinned wheels from `requirements.txt` and Playwright provisions the native Chromium headless binary into `/var/lib/jenkins/.cache/ms-playwright`.
4. **Credential Injection**: Jenkins retrieves `saucedemo-credentials` and injects them securely as environment variables (`SAUCEDEMO_USERNAME`, `SAUCEDEMO_PASSWORD`).
5. **Pytest Execution**: Headless Chromium executes the 24 Page Object Model test scenarios.
6. **Failure Capture & Screenshots**: If any test fails, Pytest hooks automatically capture full-page failure screenshots (`screenshots/FAIL_*.png`), exception types, and full tracebacks.
7. **Report Generation**: Pytest produces `reports/report.html`, `reports/report.csv`, and runtime logs in `logs/`.
8. **Consolidated Failure Payload**: If one or more tests fail, `conftest.py` calls `utils/jira_notifier.py` to write a consolidated `reports/failures.json` containing complete build, test, and screenshot metadata.
9. **Artifact Archiving**: In the `post { always }` block, Jenkins archives all reports, logs, failure JSON, and screenshots as build artifacts before workspace cleanup.
10. **Jira Webhook Dispatch & Incident Creation**: If `SEND_TO_JIRA=true` and `reports/failures.json` exists, Jenkins securely reads `jira-webhook-url` and dispatches one consolidated HTTP POST request via `curl`. Jira Automation processes the event and automatically creates a single Incident ticket in the **NOC** space.

---

## 5. Project Structure

```
playwright-server-native/
├── config/
│   ├── __init__.py
│   └── config.py          # Centralized configuration, timeouts, URLs, and credential validator
├── logs/
│   ├── .gitkeep           # Preserves logs folder structure in Git
│   ├── framework.log      # Application runtime and lifecycle log file (git-ignored)
│   └── pytest.log         # Pytest runner log file (git-ignored)
├── pages/
│   ├── __init__.py        # Exposes POM classes
│   ├── base_page.py       # Reusable base wrapper around Playwright Page methods
│   ├── login_page.py      # Login page locators and authentication workflows
│   ├── products_page.py   # Inventory catalog, item counts, price parsing, and sorting
│   ├── cart_page.py       # Cart view, item verification, and removal workflows
│   └── checkout_page.py   # 3-step checkout flow (Customer Info, Overview, Confirmation)
├── reports/
│   ├── .gitkeep           # Preserves reports folder structure in Git
│   ├── report.html        # Standalone, interactive HTML report with failure screenshots (git-ignored)
│   ├── report.csv         # Structured execution summary with status, timing, and errors (git-ignored)
│   └── failures.json      # Dynamic failure payload generated when tests fail (git-ignored runtime artifact)
├── screenshots/
│   ├── .gitkeep           # Preserves screenshots folder structure in Git
│   └── FAIL_*.png         # Automated full-page screenshots captured on test failure (git-ignored)
├── tests/
│   ├── __init__.py
│   ├── test_smoke.py      # Baseline connectivity and title validation (1 test)
│   ├── test_login.py      # Authentication scenarios including valid, invalid, locked (5 tests)
│   ├── test_products.py   # Catalog items, counts, prices, cart adding, and sorting (9 tests)
│   ├── test_cart.py       # Cart contents, item removal, and navigation (4 tests)
│   └── test_checkout.py   # Information validations, end-to-end checkout, and order confirm (5 tests)
├── utils/
│   ├── __init__.py
│   ├── jira_notifier.py   # Builds consolidated failure JSON payload for Jira webhook
│   ├── logger.py          # Dual console/file logger configuration
│   └── screenshot.py      # Robust full-page screenshot capture utility
├── .env.example           # Version-controlled credential template
├── .gitignore             # Strict ignore rules for .env, virtualenvs, reports, logs, and screenshots
├── conftest.py            # Global Pytest fixtures, browser context setup, and reporting/Jira hooks
├── Jenkinsfile            # Declarative pipeline script for native EC2 server execution & Jira webhook
├── pytest.ini             # Pytest discovery paths, CLI arguments, markers, and logging config
├── requirements.txt       # Pinned production dependencies
└── README.md              # Project documentation
```

> **Note on `reports/failures.json`**: This file is generated dynamically at runtime inside the test session only when test failures occur. It is not a permanent source file and is ignored by Git, but is captured by Jenkins `archiveArtifacts`.

---

## 6. Test Coverage

The test suite contains **24 automated test cases** across 5 distinct test modules, exercising core functional journeys of the SauceDemo platform:

| Test Module | Test Cases | Scope & Scenarios Covered |
| :--- | :---: | :--- |
| **`tests/test_smoke.py`** | 1 | Basic sanity check verifying SauceDemo connectivity, title validation (`Swag Labs`), and browser fixture lifecycle. |
| **`tests/test_login.py`** | 5 | • Successful login with `standard_user`<br>• Error validation with invalid password<br>• Missing username validation (`Epic sadface: Username is required`)<br>• Missing password validation (`Epic sadface: Password is required`)<br>• Locked-out user rejection (`Epic sadface: Sorry, this user has been locked out.`) |
| **`tests/test_products.py`** | 9 | • Verify inventory page displays after login<br>• Catalog item count verification (exactly 6 items)<br>• Product title and price retrieval<br>• Add product to cart (badge counter increments to 1)<br>• Remove product from catalog page (badge counter cleared)<br>• Sort by Name: A to Z<br>• Sort by Name: Z to A<br>• Sort by Price: Low to High<br>• Sort by Price: High to Low |
| **`tests/test_cart.py`** | 4 | • Added products accurately appear in shopping cart list<br>• Remove product from cart view<br>• Continue shopping button navigates back to inventory<br>• Proceed to checkout button transitions to checkout step one |
| **`tests/test_checkout.py`** | 5 | • Form validation when First Name is missing<br>• Form validation when Last Name is missing<br>• Form validation when Postal Code is missing<br>• Complete end-to-end checkout flow (Info → Overview → Finish)<br>• Order dispatch confirmation header (`Thank you for your order!`) and back-home navigation |
| **Total** | **24** | **100% passing across all functional areas** |

---

## 7. Local Setup Guide

### Prerequisites
- Python 3.9 or Python 3.13 installed locally.
- Git.
- Windows PowerShell (or terminal equivalent on Linux / macOS).

### Setup Instructions (Windows PowerShell)

1. **Clone the repository:**
   ```powershell
   git clone https://github.com/Akashnidi/playwright-server-native.git
   cd playwright-server-native
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   *(If using Python 3.9 locally, replace `py -3.13` with `py -3.9` or `python -m venv .venv`)*

3. **Install pinned dependencies:**
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **Install Playwright Chromium browser binaries:**
   ```powershell
   python -m playwright install chromium
   ```

5. **Set up local credentials:**
   Copy the example environment file and set your credentials:
   ```powershell
   Copy-Item .env.example .env
   ```
   Edit `.env` with your editor:
   ```env
   SAUCEDEMO_USERNAME=your_username
   SAUCEDEMO_PASSWORD=your_password
   ```

6. **Execute tests:**
   ```powershell
   # Run all 24 tests headlessly
   python -m pytest -v

   # Run tests in headed mode (for local visual inspection)
   python -m pytest tests/test_login.py --headed

   # Run a specific test module
   python -m pytest tests/test_checkout.py -v
   ```

---

## 8. Configuration and Credentials

### Central Configuration (`config/config.py`)
All execution configurations, timeout settings, and credentials are managed in `config/config.py`. Key properties include:
- `BASE_URL`: Default `https://www.saucedemo.com` (overridable via `BASE_URL` env variable).
- `BROWSER`: Default `chromium`.
- `HEADLESS`: Boolean flag controlling browser visibility (default `True`).
- `TIMEOUT` / `NAVIGATION_TIMEOUT`: Standard action and navigation limits in milliseconds.
- `VIEWPORT`: Default dimensions `{width: 1280, height: 720}`.
- `JIRA_FAILURES_JSON`: Path pointing to `reports/failures.json`.

### Environment Variable Precedence
`config.py` loads variables using `python-dotenv`:
```python
load_dotenv(dotenv_path=env_path, override=False)
```
Setting `override=False` ensures that **system and Jenkins environment variables always take precedence** over local `.env` files.

### Credential Handling:
- **Local Development**: Stored in a local `.env` file at the project root.
- **Git Security**: `.env` is explicitly listed in `.gitignore` and **must never be committed to Git**. A sanitized `.env.example` file is tracked as a template.
- **Jenkins CI Execution**: Credentials are stored securely inside the **Jenkins Credentials Manager**.
- **Safe Validation**: `Config.validate_credentials()` verifies that both username and password exist before tests start. If credentials are missing, it raises an informative exception without printing secret values.

---

## 9. AWS EC2 and Jenkins Setup & Configuration

This section documents the actual server infrastructure and Jenkins setup used to execute this POC natively without containers.

### 9.1 AWS EC2 Infrastructure Setup

- **Host Environment**: Amazon Web Services (AWS) EC2 Virtual Machine.
- **Operating System**: **Amazon Linux 2023 (AL2023) x86_64**.
- **Execution Architecture**: Jenkins is installed directly on the EC2 host. Tests execute in native user space using Python `venv` and Chromium binaries.
- **Installed Host Tooling**:
  - Java 21 Amazon Corretto (`java-21-amazon-corretto`)
  - Python 3.9.25 (`python3.9`, `python3.9-pip`)
  - Git 2.x
- **Network & Ports**:
  - **Port 8080**: Inbound HTTP access to the Jenkins Web UI.
  - **Port 22**: Inbound SSH access for server administration.
  - **Security Best Practice**: The EC2 Security Group inbound rules for ports 22 and 8080 **must be restricted to your trusted IP address** (`<your-ip>/32`) rather than open to the entire internet (`0.0.0.0/0`).

---

### 9.2 Jenkins Installation and Initial Configuration

The following verified Linux commands setup Java 21, the Jenkins service, and host dependencies on Amazon Linux 2023:

#### Step 1: Install Java 21 (Amazon Corretto) & Git
```bash
sudo dnf update -y
sudo dnf install java-21-amazon-corretto -y
sudo dnf install git -y

# Verify installations
java -version
git --version
```

#### Step 2: Install Python 3.9
```bash
sudo dnf install python3.9 python3.9-pip -y

# Verify Python version
python3.9 --version
```

#### Step 3: Configure the Jenkins Repository and Install Jenkins
```bash
sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io-2023.key
sudo dnf upgrade -y
sudo dnf install jenkins -y
```

#### Step 4: Start and Enable the Jenkins Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable jenkins
sudo systemctl start jenkins

# Verify running state
sudo systemctl status jenkins
```

#### Step 5: Complete Initial Jenkins Wizard
1. **Retrieve Initial Admin Password**:
   ```bash
   sudo cat /var/lib/jenkins/secrets/initialAdminPassword
   ```
2. **Access Web Interface**: Open `http://<EC2-PUBLIC-IP>:8080` in your web browser.
3. **Unlock Jenkins**: Paste the administrator password retrieved above.
4. **Install Plugins**: Choose **Install suggested plugins** (automatically installs Git, Pipeline, Credentials, Workspace Cleanup).
5. **Create Admin User**: Create your Jenkins administrator account and confirm the Jenkins Root URL.

---

### 9.3 Jenkins Pipeline Job Configuration

Create a Pipeline project to execute the tests from source control:

1. Click **New Item** on the Jenkins dashboard.
2. Enter the project name: `playwright-server-native` and select **Pipeline**. Click **OK**.
3. In the job configuration screen, configure the following settings:

| Setting | Value | Description |
| :--- | :--- | :--- |
| **Job Name** | `playwright-server-native` | Unique pipeline identifier |
| **Job Type** | `Pipeline` | Declarative pipeline project |
| **Definition** | `Pipeline script from SCM` | Reads pipeline definition directly from Git |
| **SCM** | `Git` | Source control system |
| **Repository URL** | `https://github.com/Akashnidi/playwright-server-native.git` | Public repository clone URL |
| **Branch Specifier** | `*/main` | Target repository branch |
| **Script Path** | `Jenkinsfile` | Location of declarative pipeline script |
| **Lightweight checkout**| `Enabled` | Fetches only the Jenkinsfile before executing |
| **Build Trigger** | `Manual` | Triggered on-demand via "Build Now" / "Build with Parameters" |

4. Click **Save**.

---

### 9.4 Jenkins Build Parameter (SEND_TO_JIRA)

The pipeline defines a Boolean parameter in `Jenkinsfile`:

- **Parameter Name**: `SEND_TO_JIRA`
- **Type**: `booleanParam`
- **Default Value**: `false`
- **Description**: Controls whether a consolidated failure report is transmitted to Jira via webhook.

#### Parameter Behaviour Matrix:

| `SEND_TO_JIRA` | Test Execution Result | Jira Action Taken |
| :---: | :---: | :--- |
| `false` | All Passed | No Incident created |
| `false` | Failures Present | No Incident created (Notification disabled) |
| `true` | All Passed | No Incident created (Nothing to report) |
| `true` | Failures Present | **Creates exactly ONE Incident ticket in Jira NOC space** |

#### Operational Guarantees:
- **No Retries**: The webhook call executes with a strict `--max-time 10` timeout without retries, preventing build hangs.
- **Status Isolation**: Any webhook dispatch error is caught inside a Groovy `try/catch` block. A notification failure logs a warning and **never alters the original Pytest test outcome**.
- **Pytest Exit Integrity**: If any test fails, the Jenkins build result remains **`FAILURE`**.
- **Isolated Logging**: Jira webhook status is logged clearly in the console output independently of test logs.
- **Safe Archiving**: Artifacts are archived before `deleteDir()` cleans the workspace.

---

### 9.5 Jenkins Credentials Configuration

The framework retrieves SauceDemo test credentials and the Jira webhook URL dynamically at runtime without committing secrets to source control.

| Credential ID | Credential Type | Purpose | Injected Variable |
| :--- | :--- | :--- | :--- |
| `saucedemo-credentials` | `Username with password` | SauceDemo application login | `SAUCEDEMO_USERNAME`, `SAUCEDEMO_PASSWORD` |
| `jira-webhook-url` | `Secret text` | Jira Automation incoming webhook endpoint | `JIRA_WEBHOOK_URL` |

#### Security Protocols:
- **Never Hardcoded**: Neither GitHub nor `Jenkinsfile` contains plaintext passwords or webhook URLs.
- **Console Suppression**: Shell steps execute with `set +x` and `curl -s`, ensuring URLs and secrets are never printed in the Jenkins console output.
- **No Python Exposure**: The Jira webhook URL is handled exclusively in Groovy/cURL within Jenkins; the Python runtime never touches or logs the webhook URL.

---

### 9.6 Jenkins Build Execution & Lifecycle

1. **Triggering a Build**: Navigate to the `playwright-server-native` job and click **Build with Parameters**. Select `SEND_TO_JIRA` if desired and click **Build**.
2. **Monitoring Console Output**: Observe stage-by-stage execution (`Check Python`, `Create Virtual Environment`, `Install Dependencies`, `Install Playwright Chromium`, `Run Tests`).
3. **Publishing Artifacts**: The `post { always { ... } }` block executes sequentially:
   ```groovy
   archiveArtifacts(
       artifacts: 'reports/**,logs/**,screenshots/**',
       allowEmptyArchive: true
   )
   ```
4. **Jira Dispatch**: If enabled and failures exist, the webhook dispatches the payload to Jira Automation.
5. **Workspace Cleanup**: `deleteDir()` purges temporary workspace files after archival and notification complete.

---

### 9.7 Infrastructure, Networking and Cost Notes

- **Security Groups**: Restrict SSH (port 22) and Jenkins (port 8080) to your client IP (`<your-ip>/32`).
- **Dynamic Public IPv4 Addresses**: If your EC2 instance restarts, update the **Jenkins URL** setting under **Manage Jenkins** → **System** or allocate an **AWS Elastic IP (EIP)**.
- **AWS Cost Considerations**: Charges apply for EC2 running hours, attached EBS storage, and public IPv4 allocation. Stop instances when not in use.

---

## 10. Reporting and Execution Artifacts

Every test execution automatically generates comprehensive artifacts:

| Artifact | Location | Generated By | Description |
| :--- | :--- | :--- | :--- |
| **Interactive HTML Report** | `reports/report.html` | `pytest-html` | Standalone, self-contained HTML document showing execution metrics, pass/fail status per test, durations, environment metadata, and embedded failure screenshots. |
| **Structured CSV Report** | `reports/report.csv` | `conftest.py` hook (`pytest_sessionfinish`) | Tabular summary containing columns: `Test Name`, `Test File`, `Execution Status`, `Execution Duration (s)`, `Failure Message`. |
| **Consolidated Failure JSON** | `reports/failures.json` | `utils/jira_notifier.py` | Complete structured JSON payload generated when tests fail, containing build metadata, test summaries, exception types, full tracebacks, and screenshot URLs. |
| **Framework Log** | `logs/framework.log` | `utils/logger.py` | Granular internal execution logs (DEBUG level) detailing page creation, lifecycle hooks, locator queries, and teardown steps. |
| **Pytest Log** | `logs/pytest.log` | `pytest.ini` (`log_file`) | Standard Pytest runner session log capturing test discovery, CLI logging, and stdout output. |
| **Failure Screenshots** | `screenshots/FAIL_<test_name>_<timestamp>.png` | `utils/screenshot.py` | Full-page browser screenshot snapped automatically when a test fails. Archived as Jenkins build artifacts and referenced in reports. |

---

## 11. Jira Webhook Integration

The framework features an automated incident management pipeline integrating Jenkins test execution with **Atlassian Jira Automation**.

### 11.1 Integration Components & Flow

```
Pytest Failures Detected
       │
       ▼
conftest.py collects records (exception type, error message, full traceback, screenshot paths)
       │
       ▼
utils/jira_notifier.py builds consolidated JSON payload → reports/failures.json
       │
       ▼
Jenkins post { always } archives artifacts (reports, logs, screenshots)
       │
       ▼
[If SEND_TO_JIRA=true & failures.json exists]
Jenkins dispatches authenticated curl POST using secret 'jira-webhook-url'
       │
       ▼
Jira Automation Incoming Webhook Trigger
       │
       ▼
Jira Automation Action: Create work item (Incident) in NOC Space
```

- **Consolidation**: All test failures from a single build are consolidated into **one Jira Incident**, preventing alert fatigue and ticket spam.

---

### 11.2 Webhook Payload Specification

When failures occur, `reports/failures.json` is generated matching this schema:

```json
{
  "event": "PLAYWRIGHT_TEST_FAILURE",
  "ticket_title": "[QA Automation Failure] playwright-server-native | Build #9 | 8 Tests Failed",
  "project_name": "playwright-server-native",
  "environment": "AWS_EC2_JENKINS",
  "build": {
    "job_name": "playwright-server-native",
    "build_number": "9",
    "build_url": "http://ec2-xx.compute-1.amazonaws.com:8080/job/playwright-server-native/9/",
    "git_branch": "origin/main",
    "git_commit": "711cf568b2e3a19b8893120cfde5a0c0f9947812",
    "timestamp": "2026-11-15T07:10:20Z"
  },
  "summary": {
    "total_tests": 24,
    "passed": 16,
    "failed": 8,
    "skipped": 0
  },
  "failures": [
    {
      "test_name": "test_complete_checkout_successfully[chromium]",
      "test_file": "tests/test_checkout.py",
      "error_type": "AssertionError",
      "error_message": "AssertionError: Expected 'Thank you for your order!'",
      "full_traceback": "page = <Page url='https://www.saucedemo.com/checkout-complete.html'>\n...",
      "duration_seconds": 4.5678,
      "screenshot_artifact": "screenshots/FAIL_test_complete_checkout.png",
      "jenkins_screenshot_url": "http://ec2-xx.compute-1.amazonaws.com:8080/job/playwright-server-native/9/artifact/screenshots/FAIL_test_complete_checkout.png"
    }
  ]
}
```

---

### 11.3 Jira Automation Configuration (NOC Space)

The receiving Jira Automation rule is configured in Atlassian Jira Cloud as follows:

1. **Trigger**: **Incoming webhook**
   - Provides a unique webhook URL stored in Jenkins Credentials Manager (`jira-webhook-url`).
   - Webhook data is stored in the `webhookData` context object.
2. **Audit & Log Action**:
   - `Log action` outputting `{{webhookData}}` for real-time validation in the Jira Audit Log.
3. **Action**: **Create work item**
   - **Project / Space**: `NOC`
   - **Issue Type**: `Incident`
   - **Summary**: `{{webhookData.ticket_title}}`
   - **Description**: Formatted with Jira smart values displaying build metadata, test summary, and detailed failure blocks:
     ```text
     *Project:* {{webhookData.project_name}}
     *Environment:* {{webhookData.environment}}
     *Build URL:* {{webhookData.build.build_url}}
     *Git Commit:* {{webhookData.build.git_commit}}

     *Summary:* {{webhookData.summary.total_tests}} Total | {{webhookData.summary.passed}} Passed | {{webhookData.summary.failed}} Failed

     *Failed Tests:*
     {{#webhookData.failures}}
     *Test:* {{test_name}}
     *Error:* {{error_type}} - {{error_message}}
     *Screenshot:* [View Artifact|{{jenkins_screenshot_url}}]
     ----
     {{/}}
     ```

---

### 11.4 Screenshot Artifact Links vs Attachments

- **Artifact Hosting**: Failure screenshots are permanently archived as Jenkins build artifacts under `screenshots/`.
- **URL Resolution**: The payload constructs direct artifact URLs pointing to the Jenkins server (`jenkins_screenshot_url`).
- **Incident Links**: The Jira Incident description embeds these direct artifact links for one-click access.
- **Current Scope**: Raw binary image files (`.png`) are **not directly attached** to Jira tickets via multipart upload in this version. (See [Future Enhancements](#13-future-enhancements)).

---

## 12. POC Validation & Build History

### 12.1 Baseline Pipeline Verification (Build #1)
- **Host Environment**: AWS EC2 instance running **Amazon Linux 2023 (AL2023)**
- **Python Runtime**: Python 3.9.25 (Native host installation)
- **Browser**: Chromium 1.49.1 (Headless mode)
- **Total Tests Executed**: 24
- **Passed**: 24 | **Failed**: 0
- **Execution Time**: **9.34 seconds**

---

### 12.2 Jira Integration & Incident Creation Verification (Builds #7, #8, #9)

The end-to-end Jira integration has been verified through targeted execution builds on the AWS EC2 Jenkins server:

#### Build #7 — Failure Payload Generation & Status Isolation
- **Test Results**: 24 tests collected (16 passed, 8 intentionally failed to test failure handling).
- **Failure Artifact**: `reports/failures.json` was successfully generated with complete exception types and tracebacks.
- **Parameter Check**: Executed with `SEND_TO_JIRA=false`. The webhook was safely bypassed.
- **Build Outcome**: Jenkins correctly finished with status **`FAILURE`**, verifying that failure detection works without unwanted webhook triggers.

#### Build #8 — Webhook Connectivity & Schema Validation
- **Trigger**: Executed with `SEND_TO_JIRA=true`.
- **Webhook Dispatch**: Jenkins successfully dispatched the JSON payload to the Jira incoming webhook URL.
- **Audit Verification**: Jira Automation Audit Log showed **`Success`**. The full payload was validated in the Jira Log action.

#### Build #9 — End-to-End Automated Jira Incident Creation
- **Incident Created**: **`NOC-12`**
- **Ticket Summary**: `[QA Automation Failure] playwright-server-native | Build #9 | 8 Tests Failed`
- **Execution Metrics**: 24 total tests | 16 passed | 8 failed | 0 skipped.
- **Incident Content**: Build number, commit hash, duration, error classification, full tracebacks, and screenshot links were rendered into the Incident description.
- **Validation Result**: **SUCCESSFUL** — Confirmed end-to-end automated Incident generation in the NOC space.

---

## 13. Future Enhancements

The following extensions are planned for subsequent development phases:

1. **Direct Jira Screenshot Attachments**: Upload binary `.png` failure screenshots directly to the Jira Incident using the Jira REST API multipart endpoint.
2. **Dynamic Severity & Priority Mapping**: Map test failure categories (e.g. smoke vs regression) to Jira incident priorities (P1/Critical vs P3/Minor).
3. **Automated Component & Assignee Tagging**: Automatically tag relevant squads and assign triage leads based on test directory paths (`tests/checkout` → Checkout Team).
4. **Token-Authenticated Jenkins Artifact Proxy**: Provide secure pre-signed or proxied URLs for Jenkins artifact screenshots when the server resides in a private VPC.
5. **Deduplication & Flaky Test Management**: Check for open incidents for the same failing scenario before creating a new ticket, appending build comments instead.

---

## 14. Limitations and Scope

This framework is built as a production-grade proof of concept for server-native execution:

- **Host Environment**: Designed specifically for native execution on AWS EC2 without Docker containers.
- **Browser Scope**: Currently configured and verified for **Chromium**. Firefox and WebKit are not installed on the server agent.
- **Test Application**: Scenarios are scoped specifically to the SauceDemo benchmark web application.
- **Screenshot Delivery**: Jira currently receives direct Jenkins artifact links, not binary image attachments.
- **Network Access**: Accessing screenshot URLs from Jira requires network reachability to the Jenkins EC2 instance.
- **Webhook Delivery**: Webhook dispatch is executed in a single shot without retries to ensure pipeline predictability.
- **No Docker**: Containerization technologies (Docker, Podman) are intentionally excluded from this project.
