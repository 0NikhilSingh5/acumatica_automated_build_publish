pipeline {
    agent any

    parameters {
        choice(
            name: 'INSTANCE_ALIAS',
            choices: '''ACER QA 22R2
Automation 22R2
Dev 22R2
Hyundai Dev 22R2
Hyundai Training 22R2
Maruti Training 22R2
Restore 1
Restore 2
TATA-Training 22R2
Temp-BuildTest 22R2''',
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
    environment {
        TEMP_BUILD_URL = 'https://qa.readywire.com/temp22r2BuildTest'
        TRAINING_URL = 'https://tatatraining22r2.readywire.com'
        AUTO_URL = 'https://auto22r2.readywire.com'
        HYUNDAI_URL = 'https://hyundaidev22r2.readywire.com'
        HYUNDAI_TRAINING_URL = 'https://hyundaitraining22r2.readywire.com'
        MARUTI_TRAINING_URL = 'https://msiltraining22r2.readywire.com'
        DEV_URL = 'https://dev.readywire.com'
        ACER_QA_URL = 'https://qa.readywire.com/maruti-acermotors'
        RESTORE1_URL = 'https://restore1.readywire.com'
        RESTORE2_URL = 'https://restore2.readywire.com'
    }

    stages {
        stage('Set URL') {
            steps {
                script {
                    if (env.INSTANCE_ALIAS == 'Temp-BuildTest 22R2') {
                        env.SELECTED_URL = env.TEMP_BUILD_URL
                    } else if (env.INSTANCE_ALIAS == 'TATA-Training 22R2') {
                        env.SELECTED_URL = env.TRAINING_URL
                    } else if (env.INSTANCE_ALIAS == 'Automation 22R2') {
                        env.SELECTED_URL = env.AUTO_URL
                    } else if (env.INSTANCE_ALIAS == 'Hyundai Dev 22R2') {
                        env.SELECTED_URL = env.HYUNDAI_URL
                    } else if (env.INSTANCE_ALIAS == 'Hyundai Training 22R2') {
                        env.SELECTED_URL = env.HYUNDAI_TRAINING_URL
                    } else if (env.INSTANCE_ALIAS == 'Maruti Training 22R2') {
                        env.SELECTED_URL = env.MARUTI_TRAINING_URL
                    } else if (env.INSTANCE_ALIAS == 'Dev 22R2') {
                        env.SELECTED_URL = env.DEV_URL
                    }else if (env.INSTANCE_ALIAS == 'ACER QA 22R2') {
                        env.SELECTED_URL = env.ACER_QA_URL
                    }else if (env.INSTANCE_ALIAS == 'Restore 1') {
                        env.SELECTED_URL = env.RESTORE1_URL
                    }else if (env.INSTANCE_ALIAS == 'Restore 2') {
                        env.SELECTED_URL = env.RESTORE2_URL
                    }else {
                        error('Invalid Selection!')
                    }
                    echo "Selected URL: ${env.SELECTED_URL}"

                    def packagePath = "C:\\Backups\\pkg-backups\\${params.PACKAGE_DATE}"
                    echo "Package Directory: ${packagePath}"

                    def dirListing = bat(script: """@echo off
setlocal enabledelayedexpansion
set count=1
for /f "tokens=1,2,3,4,*" %%a in ('dir "${packagePath}\\*.*" ^| findstr /R "^[0-9]" ^| findstr /V "<DIR>"') do (echo [!count!] %%a %%b %%c %%e
set /a count=!count!+1)""", returnStdout: true).trim()
                    echo "Directory listing:\n${dirListing}"
                }
            }
        }

        stage('Set Email') {
            steps {
                script {
                    if (params.NOTIFY_USER == 'Do not notify') {
                        env.NOTIFICATION_EMAIL = ''
                        env.SHOULD_NOTIFY = 'false'
                    } else if (params.NOTIFY_USER == 'Arpitha K') {
                        env.NOTIFICATION_EMAIL = 'arpithak@readywire.com'
                        env.SHOULD_NOTIFY = 'true'
                    } else {
                        env.NOTIFICATION_EMAIL = 'nikhils@readywire.com'
                        env.SHOULD_NOTIFY = 'true'
                    }
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

        stage('Deploy Packages') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'pkgadmin', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                    bat '@echo off && cd "C:/Jenkins-Build" && "C:\\Program Files\\Python313\\python.exe" customizationPublish.py --instance-url "' + env.SELECTED_URL + '" --username "%USERNAME%" --password "%PASSWORD%" --package-date "' + params.PACKAGE_DATE.trim() + '"'
                }
            }
        }
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
    post {
        always {
            cleanWs()
        }
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