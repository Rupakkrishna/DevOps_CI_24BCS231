pipeline {
    agent any

    environment {
        FLASK_ENV = 'testing'
        USE_SQLITE_TEST = 'true'
        SECRET_KEY = 'jenkins-ci-secret-key-test'
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out source code from Git repository...'
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo 'Setting up Python environment and installing dependencies...'
                // Install backend and test requirements
                sh '''
                    python3 -m venv venv || python -m venv venv
                    . venv/bin/activate || venv/Scripts/activate
                    pip install --upgrade pip
                    pip install -r backend/requirements.txt
                '''
            }
        }

        stage('Test') {
            steps {
                echo 'Executing pytest automated test suite...'
                sh '''
                    . venv/bin/activate || venv/Scripts/activate
                    python -m pytest tests/ -v --junitxml=junit.xml
                '''
            }
        }

        stage('Result') {
            steps {
                echo 'Reporting build and test results...'
                junit allowEmptyResults: true, testResults: 'junit.xml'
            }
        }
    }

    post {
        always {
            echo 'PBRMS Pipeline execution completed.'
            cleanWs deleteDirs: true, notFailBuild: true, patterns: [[pattern: 'venv/**', type: 'EXCLUDE']]
        }
        success {
            echo 'SUCCESS: All PBRMS automated tests passed cleanly!'
        }
        failure {
            echo 'FAILURE: One or more stages or tests failed. Check console output.'
        }
    }
}

