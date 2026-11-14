
pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        SAUCEDEMO_USERNAME = 'standard_user'
        SAUCEDEMO_PASSWORD = 'secret_sauce'
    }

    stages {
        stage('Check Python') {
            steps {
                sh 'python3.9 --version'
            }
        }

        stage('Create Virtual Environment') {
            steps {
                sh '''
                    python3.9 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    .venv/bin/python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Install Playwright Chromium') {
            steps {
                sh '''
                    .venv/bin/python -m playwright install chromium
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
