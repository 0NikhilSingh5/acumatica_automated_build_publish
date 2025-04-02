// Jenkins Pipeline for automated package deployment to various instances
pipeline {
    agent any
    // Define parameters for user input during pipeline execution
    parameters {
        choice(
            name: 'INSTANCE_ALIAS',
            choices: '''Instance-A
Instance-B
Instance-C
Instance-D
Instance-E
Instance-F
Instance-G
Instance-H
Instance-I
Instance-J''',
            description: 'Select the Acumatica instance'
        )
        string(
            name: 'PACKAGE_DATE',
            defaultValue: "${new Date().format('dd-MM-yyyy')}-0",
            description: 'Enter the package date in DD-MM-YY-n format, where n is iteration number'
        )
        choice(
            name: 'NOTIFY_USER',
            choices: '''Do not notify
Nikhil S
Arpitha K''',
            description: 'Select user to send mail to'
        )
    }
    // Environment variables for instance URLs
    // In a production environment, consider storing these in Jenkins credentials or configuration files
    environment {
        INSTANCE_A_URL = 'https://instanceA.example.com'
        INSTANCE_B_URL = 'https://instanceB.example.com'
        INSTANCE_C_URL = 'https://instanceC.example.com'
        INSTANCE_D_URL = 'https://instanceD.example.com'
        INSTANCE_E_URL = 'https://instanceE.example.com'
        INSTANCE_F_URL = 'https://instanceF.example.com'
        INSTANCE_G_URL = 'https://instanceG.example.com'
        INSTANCE_H_URL = 'https://instanceH.example.com'
        INSTANCE_I_URL = 'https://instanceI.example.com'
        INSTANCE_J_URL = 'https://instanceJ.example.com'
    }

    stages {
        // Map the selected instance alias to the corresponding URL
        stage('Set URL') {
            steps {
                script {
                    def instanceUrlMap = [
                        'Instance-A': env.INSTANCE_A_URL,
                        'Instance-B': env.INSTANCE_B_URL,
                        'Instance-C': env.INSTANCE_C_URL,
                        'Instance-D': env.INSTANCE_D_URL,
                        'Instance-E': env.INSTANCE_E_URL,
                        'Instance-F': env.INSTANCE_F_URL,
                        'Instance-G': env.INSTANCE_G_URL,
                        'Instance-H': env.INSTANCE_H_URL,
                        'Instance-I': env.INSTANCE_I_URL,
                        'Instance-J': env.INSTANCE_J_URL
                    ]
                    // Set the selected URL based on the chosen instance alias
                    env.SELECTED_URL = instanceUrlMap[env.INSTANCE_ALIAS]
                    if (env.SELECTED_URL == null) {
                        error('Invalid Instance Selection!')
                    }
                    
                    echo "Selected URL: ${env.SELECTED_URL}"

                    // Define package directory path based on the package date parameter
                    def packagePath = "C:\\Backups\\pkg-backups\\${params.PACKAGE_DATE}"
                    echo "Package Directory: ${packagePath}"
                    
                    //List files in the package directory for verification, one can skip this part as this was added to have logs of file which are present.
                    def dirListing = bat(script: """@echo off
setlocal enabledelayedexpansion
set count=1
for /f "tokens=1,2,3,4,*" %%a in ('dir "${packagePath}\\*.*" ^| findstr /R "^[0-9]" ^| findstr /V "<DIR>"') do (echo [!count!] %%a %%b %%c %%e
set /a count=!count!+1)""", returnStdout: true).trim()
                    echo "Directory listing:\n${dirListing}"
                }
            }
        }
        
        // Configure email notification settings based on user selection
        stage('Set Email') {
            steps {
                script {
                    // Map notification user selection to email addresses
                    def emailMap = [
                        'Do not notify': '',
                        'User1': 'user1@example.com',
                        'User2': 'user2@example.com'
                    ]
                    env.NOTIFICATION_EMAIL = emailMap[params.NOTIFY_USER]
                    env.SHOULD_NOTIFY = (params.NOTIFY_USER != 'Do not notify') ? 'true' : 'false'
                }
            }
        }

        stage('Publish Start Notification') {
            when {
                expression { env.SHOULD_NOTIFY == 'true' }
            }
            steps {
                emailext(
                    subject: 'Package Upload Starting',
                    mimeType: 'text/html',
                    to: env.NOTIFICATION_EMAIL,
                    body: """
                    <p>Customisation publish started in <b>${params.INSTANCE_ALIAS}</b>.</p>
                    <p>Please logout from <b>${params.INSTANCE_ALIAS}</b>, resume only after package is finished</p>
                    """)
            }
        }
        
        // Deploy customizatino packages to the selected instance:
        stage('Deploy Packages') {
            steps {
                // Use Jenkins credentials to securely access deployment credentials
                withCredentials([usernamePassword(credentialsId: 'deployment-credentials', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                    // Execute deployment script with required parameters
                    bat '@echo off && cd "C:/Deployment-Scripts" && "C:\\Program Files\\Python311\\python.exe" deployPackage.py --instance-url "' + env.SELECTED_URL + '" --username "%USERNAME%" --password "%PASSWORD%" --package-date "' + params.PACKAGE_DATE.trim() + '"'
                }
            }
        }
        // Send notification email when deployment completes
        stage('Publish Finish Notification') {
            when {
                expression { env.SHOULD_NOTIFY == 'true' }
            }
            steps {
                emailext(
                    subject: 'Package Upload Starting',
                    mimeType: 'text/html',
                    to: env.NOTIFICATION_EMAIL,
                    body: """
                    <p>Customisation publish finished in <b>${params.INSTANCE_ALIAS}</b>.</p>
                    <p>you can resume your work</p>
                    """
                    )
            }
        }
    }
    // Post-deployment actions
    post {
        // Always clean the workspace after the pipeline completes
        always {
            cleanWs()
        }
        // Actions to take on successful deployment
        success {
            echo 'Customization publish completed successfully!'
            emailext(
                attachLog: true,
                subject: '$PROJECT_NAME: $BUILD_STATUS !!',
                mimeType: 'text/html',
                to: 'awsadmin@readywire.com',
                body: """
                <p>Hi Team,</p>
                <p>Automated Customization project publish completed in ${params.INSTANCE_ALIAS} with the status: <b>${currentBuild.result}</b>.</p>
                <p>You can login and resume your work in said instance</p>

                <p>Regards,<br/>SaaS team</p>
                """
            )
        }
        // Actions to take on deployment failure
        failure {
            echo 'Customization Publish failed! Check the logs for details.'
            emailext(
                attachLog: true,
                subject: '$PROJECT_NAME: $BUILD_STATUS !!',
                mimeType: 'text/html',
                to: 'awsadmin@readywire.com',
                body: """
                <p>Hi Team,</p>
                <p>Automated Customization project publish failed in ${params.INSTANCE_ALIAS}.</p>
                <p>Build Status: <b>${currentBuild.result}</b>.</p>
                <p>Please review the attached log for more details.</p><br/>
                <p>Regards,<br/>SaaS team</p>
                """
            )
        }
    }
}
