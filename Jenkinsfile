pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build') {
            steps {
                bat '"C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m compileall backend'
            }
        }

        stage('Test') {
            steps {
                bat '"C:\\Users\\USER\\AppData\\Local\\Programs\\Python\\Python313\\python.exe" -m pytest tests -v'
            }
        }

        stage('Result') {
            steps {
                echo 'Build and Test completed successfully.'
            }
        }
    }
}