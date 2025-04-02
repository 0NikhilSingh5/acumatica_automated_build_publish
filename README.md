# 📌 Automated Acumatica Customization Project Publish

## 📜 Overview
This repository contains an automated solution for deploying customization packages to Acumatica instances using Jenkins pipeline and Python.

The deployment tool consists of two main components:
1. A **Jenkins pipeline** that orchestrates the deployment process.
2. A **Python script** that handles the actual package upload and publication.

This solution allows for consistent, repeatable deployments across multiple Acumatica instances while providing notifications to stakeholders. 🚀

---

## 📂 Table of Contents

- [Prerequisites](##Prerequisites)
- [Directory Structure](#directory-structure)
- [Jenkins Pipeline](#jenkins-pipeline)
  - [Parameters](#parameters)
  - [Setup](#setup)
  - [Usage](#usage)
- [Python Deployment Script](#python-deployment-script)
  - [Features](#features)
  - [Arguments](#arguments)
  - [Customization](#customization)
- [Deployment Process](#deployment-process)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🛠 Prerequisites

- **Jenkins Server** with:
  - Email notification plugin 📧
  - Credentials plugin 🔑
- **Python 3.11+** with the following packages:
  ```sh
  pip install requests argparse
  ```
- Acumatica instance with accessible API endpoints
- Directory structure for package storage

## 📂 Directory Structure

```
C:\
├── Deployment-Scripts\
│   └── uploadAndPublish.py
├── Backups\
│   └── pkg-backups\
│       ├── DD-MM-YYYY-0\
│       │   ├── RW.Base.22.210.00x.zip
│       │   ├── RW.Screens.Extension.Files.23.213.0015.zip
│       │   └── ... (other package files)
│       └── ... (other dated backup folders)
└── Jenkins-Build\
    └── (Jenkins workspace)
```

## 🚀 Jenkins Pipeline

The **Jenkins pipeline (`pipeline.groovy`)** automates the deployment workflow with user-friendly parameters and notification capabilities.

### 🔹 Parameters

| Parameter       | Description |
|----------------|-------------|
| `INSTANCE_ALIAS` | The Acumatica instance to deploy to |
| `PACKAGE_DATE`  | Date of the package in DD-MM-YYYY-n format (n is iteration number) |
| `NOTIFY_USER`   | User to notify before and after deployment |

### 🔧 Setup

1. Create a new **Jenkins Pipeline** job.
2. Configure **SCM** to pull the `pipeline.groovy` script from your repository.
3. Add **Jenkins Credentials**:
   - **ID**: `deployment-credentials`
   - **Type**: Username with password
   - **Scope**: Global
   - **Description**: Credentials for Acumatica deployment.

### 📌 Usage

1. Navigate to the pipeline in Jenkins.
2. Click **"Build with Parameters"**.
3. Select the instance, package date, and notification settings.
4. Click **"Build"**.

The pipeline will:
1. Map the instance alias to the correct URL.
2. Configure notification settings.
3. Send a **start notification email** (if configured).
4. Deploy packages using the Python script.
5. Send a **completion notification email** (if configured).
6. Notify administrators of **success/failure**.

## 🐍 Python Deployment Script

The **`uploadAndPublish.py`** script handles package deployment via the Acumatica API.

### 🔹 Features

- **Authentication** 🔐: Logs into Acumatica using provided credentials.
- **File Uploading** 📤: Reads and encodes packages before uploading.
- **Publishing** 🚀: Triggers Acumatica's publish process and checks the status.
- **Error Handling** ⚠️: Handles login, upload, and publish failures gracefully.
- **Real-time Logging** 📜: Tracks deployment progress.

### 📌 Arguments

| Argument          | Description | Required |
|------------------|-------------|----------|
| `--instance-url` | URL of the Acumatica instance | ✅ Yes |
| `--username`     | Username for authentication | ✅ Yes |
| `--password`     | Password for authentication | ✅ Yes |
| `--package-date` | Package date directory (DD-MM-YYYY-n) | ✅ Yes |

### ✨ Customization

To customize package deployment:
1. Modify the **`get_files_config()`** function.
2. Adjust project levels (lower numbers are published first).
3. Update file paths, names, and descriptions.

## 🔄 Deployment Process

1. **Initialization**:
   - Jenkins pipeline starts with user-selected parameters.
   - Determines target URL and package directory.

2. **Pre-deployment Notification** 📩:
   - Sends notification email to selected user (if configured).

3. **Package Upload** 📤:
   - Python script authenticates with Acumatica.
   - Uploads each package zip file with metadata.
   - Validates upload success.

4. **Publication** 🚀:
   - Initiates publishing of all uploaded packages.
   - Monitors publication status with real-time logging.
   - Checks for completion or errors.

5. **Post-deployment Actions** ✅:
   - Logs out from the Acumatica instance.
   - Sends completion notification.
   - Cleans Jenkins workspace.

## 🛠 Troubleshooting

### ⚠️ Common Issues

- **Authentication Failure**: Verify credentials and permissions.
- **File Not Found**: Ensure package directory and files exist in the expected location.
- **Publication Errors**: Check Jenkins console output for error messages.

### 📜 Debug Logging

The Python script provides detailed logs in Jenkins, including:
- Authentication status
- File upload progress
- Publication progress and status
- Error details when failures occur

## 🤝 Contributing

1. **Fork** the repository.
2. Create a **feature branch**: `git checkout -b new-feature`.
3. **Commit changes**: `git commit -am 'Add new feature'`.
4. **Push to branch**: `git push origin new-feature`.
5. Submit a **pull request** to improve this tool.

Happy Deploying! 🚀🔥

