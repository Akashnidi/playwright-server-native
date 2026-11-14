
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Validate Environment') {
            steps {
                sh '''
                    set -e

                    if [ -z "$PIP_INDEX_URL" ]; then
                        echo "ERROR: PIP_INDEX_URL is not configured. Ask DevOps for the JFrog Artifactory pip index."
                        exit 1
                    fi

                    if [ -z "$SAUCEDEMO_USERNAME" ] || [ -z "$SAUCEDEMO_PASSWORD" ]; then
                        echo "ERROR: SauceDemo credentials are not configured in Jenkins."
                        exit 1
                    fi

                    python3.9 --version
                '''
            }
        }

        stage('Create Environment and Install Dependencies') {
            steps {
                sh '''
                    set -e

                    python3.9 -m venv .venv

                    .venv/bin/python -m pip install --upgrade pip \
                        --index-url "$PIP_INDEX_URL"

                    .venv/bin/python -m pip install \
                        --index-url "$PIP_INDEX_URL" \
                        -r requirements.txt
                '''
            }
        }

        stage('Verify Browser') {
            steps {
                sh '''
                    set -e

                    BROWSER_PATH=$(.venv/bin/python -c \
                        "from playwright.sync_api import sync_playwright; p=sync_playwright().start(); print(p.chromium.executable_path); p.stop()")

                    if [ ! -x "$BROWSER_PATH" ]; then
                        echo "ERROR: Playwright Chromium is not provisioned."
                        echo "Ask DevOps to provide the approved browser binaries."
                        exit 1
                    fi

                    echo "Chromium executable found."
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    .venv/bin/python -m pytest -v
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts(
                artifacts: 'reports/**,logs/**,screenshots/**',
                allowEmptyArchive: true
            )

            deleteDir()
        }
    }
}
