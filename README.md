# acumatica_autoamted_build_publish
# Acumatica Package Deployment Tool

This repository contains an automated solution for deploying customization packages to Acumatica instances using Jenkins pipeline and Python.

## Overview

The deployment tool consists of two main components:
1. A Jenkins pipeline that orchestrates the deployment process
2. A Python script that handles the actual package upload and publication

This solution allows for consistent, repeatable deployments across multiple Acumatica instances while providing notifications to stakeholders.

## Table of Contents

- [Prerequisites](#prerequisites)
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

## Prerequisites

- Jenkins server with:
  - Email notification plugin
  - Credentials plugin
- Python 3.11+ with the following packages:
  - requests
  - argparse
- Acumatica instance with accessible API endpoints
- Directory structure for package storage

## Directory Structure

```
C:\
├── Deployment-Scripts\
│   └── deployPackage.py
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

## Jenkins Pipeline

The Jenkins pipeline (`Jenkinsfile`) automates the deployment workflow with user-friendly parameters and notification capabilities.

### Parameters

| Parameter | Description |
|-----------|-------------|
| `INSTANCE_ALIAS` | The Acumatica instance to deploy to |
| `PACKAGE_DATE` | Date of the package in DD-MM-YYYY-n format (n is iteration number) |
| `NOTIFY_USER` | User to notify before and after deployment |

### Setup

1. Create a new Jenkins Pipeline job
2. Configure SCM to pull the Jenkinsfile from your repository
3. Add credentials in Jenkins:
   - ID: `deployment-credentials` 
   - Type: Username with password
   - Scope: Global
   - Description: Credentials for Acumatica deployment

### Usage

1. Navigate to the pipeline in Jenkins
2. Click "Build with Parameters"
3. Select the instance, package date, and notification settings
4. Click "Build"

The pipeline will:
1. Map the instance alias to the correct URL
2. Configure notification settings
3. Send a start notification email (if configured)
4. Deploy packages using the Python script
5. Send a completion notification email (if configured) 
6. Send a success/failure notification to administrators

## Python Deployment Script

The `deployPackage.py` script handles the actual package upload and publication process via the Acumatica API.

### Features

- Authentication with Acumatica instance
- Package upload with appropriate project metadata
- Publication of uploaded customization packages
- Real-time status monitoring with detailed logging
- Error handling and reporting

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--instance-url` | URL of the Acumatica instance | Yes |
| `--username` | Username for authentication | Yes |
| `--password` | Password for authentication | Yes |
| `--package-date` | Package date directory (DD-MM-YYYY-n) | Yes |

### Customization

The script determines which packages to upload based on the package date directory and the target instance. The upload order and metadata are defined in the `get_files_config()` function.

To customize the packages deployed:
1. Modify the `project_configs` list in the `get_files_config()` function
2. Adjust project levels as needed (lower numbers are published first)
3. Update file paths, names, and descriptions

## Deployment Process

1. **Initialization**:
   - Jenkins pipeline starts with user-selected parameters
   - Determines target URL and package directory

2. **Pre-deployment Notification**:
   - Sends notification email to selected user (if configured)

3. **Package Upload**:
   - Python script authenticates with the Acumatica instance
   - Uploads each package zip file with metadata
   - Validates upload success

4. **Publication**:
   - Initiates publication of all uploaded packages
   - Monitors publication status with real-time logging
   - Checks for completion or errors

5. **Post-deployment Actions**:
   - Logs out from the Acumatica instance
   - Sends completion notification
   - Cleans Jenkins workspace

## Troubleshooting

### Common Issues

- **Authentication Failure**: Verify credentials are correct and the user has sufficient permissions.
- **File Not Found**: Ensure package directory and files exist in the expected location.
- **Publication Errors**: Check the Jenkins console output for specific error messages from Acumatica.

### Debug Logging

The Python script uses detailed logging that appears in the Jenkins console. The logs include:
- Authentication status
- File upload progress
- Publication progress and status
- Error details when failures occur

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin new-feature`
5. Submit a pull request
