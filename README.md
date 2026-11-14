# playwright-server-native

An enterprise-grade Python UI automation framework using **Playwright** and **Pytest** to test the [SauceDemo](https://www.saucedemo.com/) web application.

This repository serves as a **Proof of Concept (POC)** for executing automated browser tests natively on an **AWS EC2 Jenkins agent without Docker**.

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
   - [9.4 Jenkins Credentials Configuration](#94-jenkins-credentials-configuration)
   - [9.5 Jenkins Build Execution & Lifecycle](#95-jenkins-build-execution--lifecycle)
   - [9.6 Infrastructure, Networking and Cost Notes](#96-infrastructure-networking-and-cost-notes)
10. [Reporting and Execution Artifacts](#10-reporting-and-execution-artifacts)
11. [Latest POC Validation](#11-latest-poc-validation)
12. [Future Enhancement — Jira Webhook Integration](#12-future-enhancement--jira-webhook-integration)
13. [Limitations and Scope](#13-limitations-and-scope)

---

## 1. Project Overview

`playwright-server-native` demonstrates how to run scalable, headless UI test automation directly on server infrastructure (EC2) orchestrated through a CI/CD pipeline (Jenkins).

### Key Highlights:
- **Native Server Execution**: Runs directly on the host operating system without container overhead or nested virtualization issues.
- **Page Object Model (POM)**: Complete structural separation of web elements, page interactions, and test assertions.
- **Robust Locators**: Prioritizes standard SauceDemo `data-test` attributes and user-facing accessibility selectors.
- **Multi-Format Reporting**: Automatically generates interactive HTML reports, machine-readable CSV summaries, detailed runtime logs, and automated failure screenshots.
- **Secure Credential Handling**: Strict credential isolation supporting local `.env` development and Jenkins Credentials Manager injection without exposing secrets in code, logs, or reports.

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
| **Version Control** | GitHub | Git 2.x | Source code management |
| **Host Infrastructure** | AWS EC2 | Amazon Linux 2023 | Native bare-metal execution host (No Docker) |

> Verified from [`requirements.txt`](requirements.txt). Python's built-in `csv` and `logging` modules power CSV generation and framework logging without introducing unnecessary third-party dependencies.

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
2. **Chromium Browser Binary**: Downloaded via `python -m playwright install chromium`. Playwright downloads a specialized, tested build of Chromium. In Playwright 1.49.1, this provisions **Chromium build `1148` (Chromium 131.0.6778.33)**.
3. **Chromium Headless Shell (`chrome-headless-shell`)**: Playwright packages an optimized headless-only Chromium executable that strips unnecessary desktop GUI subsystems, significantly reducing memory consumption and CPU overhead during CI runs.
4. **FFmpeg Helper Binary**: Downloaded alongside Chromium to capture video recordings of test runs when enabled.

**Browser Binary Installation Command:**
```bash
python -m playwright install chromium
```

> **Jenkins Cache Note**: In the Jenkins pipeline, this command downloads the browser binaries into the Jenkins user's home cache directory (`/var/lib/jenkins/.cache/ms-playwright`). Because the cache resides outside the workspace, browser downloads persist across pipeline runs rather than being re-downloaded every build.

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
  Or for the headless shell:
  ```bash
  ldd /var/lib/jenkins/.cache/ms-playwright/chromium-1148/chrome-headless-shell-linux/chrome-headless-shell | grep "not found"
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
- [ ] **Outbound Internet Access**: Verify instance can reach GitHub (`github.com`), PyPI (`pypi.org`), and Playwright CDN (`playwright.azureedge.net`).
- [ ] **Linux Shared Libraries**: Verify that shared libraries required by Chromium are satisfied.
- [ ] **Playwright Browser Provisioning**: Verify Chromium installs successfully into `/var/lib/jenkins/.cache/ms-playwright`.
- [ ] **Jenkins Credentials**: Store `saucedemo-credentials` in Jenkins Credentials Manager.
- [ ] **Pipeline Execution**: Configure and trigger the `playwright-server-native` Pipeline job.

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
| **Recommended** | EC2 Instance Type: `t3.medium` (2 vCPU, 4GB RAM) | Recommended baseline for headless browser runs |
| **Recommended** | AWS Elastic IP (EIP) | Recommended to avoid changing Jenkins URLs |
| **Pending Verification** | Minimal standalone RPM package manifest for AL2023 | Requires further OS package audit |

---

## 4. Architecture

The end-to-end execution lifecycle follows a sequential flow from source control to artifact archiving:

```
┌──────────┐     ┌─────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│  GitHub  │ ──> │ Jenkins │ ──> │ Python Virtual Env  │ ──> │ Install Dependencies │
│ (Source) │     │ (Build) │     │     (.venv)         │     │  (requirements.txt)  │
└──────────┘     └─────────┘     └─────────────────────┘     └──────────────────────┘
                                                                        │
                                                                        ▼
┌──────────────────┐     ┌────────────────┐     ┌────────┐     ┌──────────────────────┐
│ Jenkins Artifacts│ <── │ Output Reports │ <── │ Pytest │ <── │ Playwright Chromium  │
│  (Archived Post) │     │ (HTML/CSV/Logs)│     │ Suite  │     │   (Native Binary)    │
└──────────────────┘     └────────────────┘     └────────┘     └──────────────────────┘
```

### Execution Flow:
1. **GitHub Trigger**: Jenkins checks out the repository (`main` branch) containing application code and the declarative `Jenkinsfile`.
2. **Environment Isolation**: Jenkins provisions an isolated Python virtual environment (`.venv`) using the host's native `python3.9`.
3. **Dependency Installation**: `pip` installs the pinned wheels from `requirements.txt`.
4. **Browser Provisioning**: Playwright installs the native Chromium headless binary into the agent cache.
5. **Credential Injection**: Jenkins retrieves credentials from its Credentials Manager (`saucedemo-credentials`) and securely injects them as OS environment variables (`SAUCEDEMO_USERNAME`, `SAUCEDEMO_PASSWORD`).
6. **Pytest Execution**: Headless Chromium executes the 24 Page Object Model test scenarios.
7. **Report & Log Capture**: Test lifecycle hooks record test outcomes to `reports/report.html`, generate `reports/report.csv`, capture debug logs in `logs/`, and snap full-page screenshots to `screenshots/` upon any failure.
8. **Artifact Archiving**: Jenkins post-build stage archives all test outputs as persistent build artifacts and cleanly purges the temporary workspace directory.

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
│   └── report.csv         # Structured execution summary with status, timing, and errors (git-ignored)
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
│   ├── logger.py          # Dual console/file logger configuration
│   └── screenshot.py      # Robust full-page screenshot capture utility
├── .env.example           # Version-controlled credential template
├── .gitignore             # Strict ignore rules for .env, virtualenvs, reports, logs, and screenshots
├── conftest.py            # Global Pytest fixtures, browser context setup, and reporting hooks
├── Jenkinsfile            # Declarative pipeline script for native EC2 server execution
├── pytest.ini             # Pytest discovery paths, CLI arguments, markers, and logging config
├── requirements.txt       # Pinned production dependencies
└── README.md              # Project documentation
```

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

### Environment Variable Precedence
`config.py` loads variables using `python-dotenv`:
```python
load_dotenv(dotenv_path=env_path, override=False)
```
Setting `override=False` ensures that **system and Jenkins environment variables always take precedence** over local `.env` files.

### Credential Handling:
- **Local Development**: Stored in a local `.env` file at the project root.
- **Git Security**: `.env` is explicitly listed in `.gitignore` and **must never be committed to Git**. A sanitized `.env.example` file is tracked as a template.
- **Jenkins CI Execution**: Credentials are stored securely inside the **Jenkins Credentials Manager** as a `Username with password` credential with the ID:
  ```
  saucedemo-credentials
  ```
  During pipeline execution, Jenkins injects these credentials as masked environment variables (`SAUCEDEMO_USERNAME`, `SAUCEDEMO_PASSWORD`) inside a secure `withCredentials` block.
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
| **Build Trigger** | `Manual` | Triggered on-demand via "Build Now" |

4. Click **Save**.

---

### 9.4 Jenkins Credentials Configuration

The framework retrieves SauceDemo login credentials dynamically at runtime without committing secrets to source control.

#### Configuring Credentials in Jenkins:
1. Navigate to **Manage Jenkins** → **Credentials** → **System** → **Global credentials (unrestricted)**.
2. Click **Add Credentials**.
3. Fill in the credential details:
   - **Kind**: `Username with password`
   - **Scope**: `Global (Jenkins, nodes, items, all child items)`
   - **Username**: Enter your SauceDemo username (e.g. `standard_user`)
   - **Password**: Enter your SauceDemo password
   - **ID**: `saucedemo-credentials` *(Must match the ID in Jenkinsfile exactly)*
   - **Description**: `SauceDemo automation test credentials`
4. Click **Create**.

#### How the Pipeline Injects Credentials:
In [`Jenkinsfile`](Jenkinsfile), the `withCredentials` step binds these values securely into runtime environment variables:

```groovy
withCredentials([
    usernamePassword(
        credentialsId: 'saucedemo-credentials',
        usernameVariable: 'SAUCEDEMO_USERNAME',
        passwordVariable: 'SAUCEDEMO_PASSWORD'
    )
]) {
    sh '''
        set +x
        .venv/bin/python -m pytest -v
    '''
}
```

- `set +x` explicitly disables shell command echoing, ensuring passwords never leak into Jenkins console output.
- `config/config.py` automatically reads `os.environ["SAUCEDEMO_USERNAME"]` and `os.environ["SAUCEDEMO_PASSWORD"]`.
- Neither GitHub nor the `Jenkinsfile` contains any hardcoded secrets.

---

### 9.5 Jenkins Build Execution & Lifecycle

1. **Triggering a Build**: Navigate to the `playwright-server-native` job and click **Build Now**.
2. **Build History**: The left pane shows the execution queue and build numbers (`#1`, `#2`, etc.).
3. **Monitoring Console Output**: Click on the active build number → **Console Output** to observe stage-by-stage execution:
   - `python3.9 --version` validation.
   - `.venv` creation and `pip install -r requirements.txt`.
   - Native Playwright Chromium binary verification.
   - Pytest execution of the 24 test scenarios.
4. **Publishing Artifacts**: In the pipeline `post { always { ... } }` block:
   ```groovy
   archiveArtifacts(
       artifacts: 'reports/**,logs/**,screenshots/**',
       allowEmptyArchive: true
   )
   deleteDir()
   ```
   Jenkins archives the HTML report, CSV report, runtime logs, and failure screenshots before `deleteDir()` cleans the workspace.
5. **Accessing Artifacts**: On the build summary page, view and download the archived files under **Build Artifacts**.

---

### 9.6 Infrastructure, Networking and Cost Notes

- **Security Groups**:
  - Restrict SSH (port 22) and Jenkins (port 8080) to your client IP (`<your-ip>/32`).
  - Do not expose port 8080 to `0.0.0.0/0` unless an authentication proxy or SSL reverse proxy is configured.
- **Dynamic Public IPv4 Addresses**:
  - Standard EC2 instances receive a dynamic public IP that **changes whenever the instance is stopped and started**.
  - If your EC2 instance restarts, update your browser URL (`http://<new-ip>:8080`) and update the **Jenkins URL** setting under **Manage Jenkins** → **System**.
  - To prevent IP changes, allocate and associate an **AWS Elastic IP (EIP)** to the instance.
- **AWS Cost Considerations**:
  - **EC2 Compute**: Charges apply per hour while the instance is running. Stop the instance when not in use.
  - **EBS Storage**: Attached EBS root volumes (e.g., gp3 30GB) incur standard monthly gigabyte storage fees.
  - **Public IPv4 Charges**: AWS charges a nominal hourly fee for in-use and idle public IPv4 addresses.

---

## 10. Reporting and Execution Artifacts

Every test execution automatically generates comprehensive artifacts:

| Artifact | Location | Generated By | Description |
| :--- | :--- | :--- | :--- |
| **Interactive HTML Report** | `reports/report.html` | `pytest-html` | Standalone, self-contained HTML document showing execution metrics, pass/fail status per test, durations, environment metadata, and embedded failure screenshots. |
| **Structured CSV Report** | `reports/report.csv` | `conftest.py` hook (`pytest_sessionfinish`) | Tabular summary containing columns:<br>• `Test Name`<br>• `Test File`<br>• `Execution Status` (PASSED / FAILED / SKIPPED)<br>• `Execution Duration (s)`<br>• `Failure Message` |
| **Framework Log** | `logs/framework.log` | `utils/logger.py` | Granular internal execution logs (DEBUG level) detailing page creation, lifecycle hooks, locator queries, and teardown steps. |
| **Pytest Log** | `logs/pytest.log` | `pytest.ini` (`log_file`) | Standard Pytest runner session log capturing test discovery, CLI logging, and stdout output. |
| **Failure Screenshots** | `screenshots/FAIL_<test_name>_<timestamp>.png` | `utils/screenshot.py` | Full-page browser screenshot snapped automatically when a test fails. Also embedded directly into `reports/report.html`. |

---

## 11. Latest POC Validation

The native EC2 server execution has been verified via the Jenkins pipeline.

### Recorded Build Metrics:
- **Host Environment**: AWS EC2 instance running **Amazon Linux 2023 (AL2023)**
- **Python Runtime**: Python 3.9.25 (Native host installation)
- **Browser**: Chromium 1.49.1 (Headless mode)
- **Total Tests Executed**: 24
- **Passed**: 24
- **Failed**: 0
- **Execution Time**: **9.34 seconds**

> *Note: These figures reflect the recorded results from the baseline verification run on the EC2 Jenkins agent. Performance and exact execution times may vary depending on instance sizing and network latency.*

---

## 12. Future Enhancement — Jira Webhook Integration

> **Status: PLANNED (Not Yet Implemented)**

As a planned post-POC extension, the framework architecture can be integrated directly with Atlassian Jira for automated defect tracking:

### Planned Design:
1. **Failure Hook Interception**: A custom Pytest hook catches failed test results at session completion.
2. **Payload Construction**: The framework constructs a structured JSON payload containing:
   - Failing test name and file location.
   - Error classification and condensed failure message / traceback.
   - Build environment metadata (Git commit hash, Jenkins build URL, execution timestamp).
   - Screenshot attachment reference.
3. **Webhook Dispatch**: Sends an authenticated HTTP POST request to a configured Jira Automation incoming webhook endpoint.
4. **Jira Automation Rule**: Ingests the webhook event to automatically create a linked Bug issue or comment on an existing defect ticket.

---

## 13. Limitations and Scope

This framework is built strictly as a proof-of-concept for native server execution:

- **Host Environment**: Designed specifically for native execution on AWS EC2 without Docker containers.
- **Browser Support**: Currently configured and verified exclusively for **Chromium**. Firefox and WebKit are not installed on the server agent.
- **Test Application**: Scenarios are scoped specifically to the SauceDemo benchmark web application.
- **No Docker**: Containerization technologies (Docker, Podman) are intentionally excluded from this project.
- **No Active Jira Integration**: The Jira webhook mechanism is currently a planned design specification and is not yet implemented in the codebase.
