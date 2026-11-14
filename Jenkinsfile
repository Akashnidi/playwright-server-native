
pipeline {
    agent any

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
            archiveArtifacts(
                artifacts: 'reports/**,logs/**,screenshots/**',
                allowEmptyArchive: true
            )

            deleteDir()
        }
    }
}
