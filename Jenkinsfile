
pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'SEND_TO_JIRA',
            defaultValue: false,
            description: 'When enabled and tests have failed, send a consolidated failure report to Jira via webhook. Has no effect when all tests pass.'
        )
    }

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {

        stage('Check Python') {
            steps {
                sh '''
                    set -e
                    python3.9 --version
                '''
            }
        }

        stage('Create Virtual Environment') {
            steps {
                sh '''
                    set -e
                    python3.9 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    set -e
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Install Playwright Chromium') {
            steps {
                sh '''
                    set -e
                    .venv/bin/python -m playwright install chromium
                '''
            }
        }

        stage('Run Tests') {
            steps {
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
            }
        }
    }

    post {
        always {
            // ── 1. Archive test artifacts ────────────────────────────────────
            // Must run before deleteDir() so outputs are retained as build
            // artifacts regardless of test outcome.
            // failures.json is under reports/** and is included automatically.
            archiveArtifacts(
                artifacts: 'reports/**,logs/**,screenshots/**',
                allowEmptyArchive: true
            )

            // ── 2. Jira webhook notification (conditional) ───────────────────
            // Runs only when:
            //   a) SEND_TO_JIRA parameter is true, AND
            //   b) reports/failures.json exists (i.e. at least one test failed).
            //
            // Errors inside this block (network timeout, bad URL, etc.) are
            // caught and logged without changing the overall build result.
            // A failing test run stays FAILURE; a passing run stays SUCCESS.
            script {
                if (params.SEND_TO_JIRA && fileExists('reports/failures.json')) {
                    echo "Jira notification: failures detected and SEND_TO_JIRA=true — dispatching webhook."
                    try {
                        withCredentials([
                            string(
                                credentialsId: 'jira-webhook-url',
                                variable: 'JIRA_WEBHOOK_URL'
                            )
                        ]) {
                            sh '''
                                set +x
                                curl -s -f \
                                     -X POST \
                                     -H "Content-Type: application/json" \
                                     -d @reports/failures.json \
                                     --max-time 10 \
                                     "${JIRA_WEBHOOK_URL}"
                            '''
                        }
                        echo "Jira webhook dispatched successfully."
                    } catch (Exception e) {
                        // Log the notification failure but intentionally do not
                        // alter the build result — the Pytest outcome is authoritative.
                        echo "WARNING: Jira webhook dispatch failed — ${e.getMessage()}"
                        echo "Build result is preserved. Jira notification did not succeed."
                    }
                } else if (params.SEND_TO_JIRA && !fileExists('reports/failures.json')) {
                    echo "Jira notification: SEND_TO_JIRA=true but no failures.json found — all tests passed. Nothing sent."
                } else {
                    echo "Jira notification: disabled (SEND_TO_JIRA=false)."
                }
            }

            // ── 3. Workspace cleanup ─────────────────────────────────────────
            // Runs last so artifacts are archived and the webhook is dispatched
            // before the workspace is purged.
            deleteDir()
        }
    }
}
