import argparse
import requests
import json
import base64
import logging
import time
from typing import List, Dict
from pathlib import Path
import sys

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("AcumaticaDeployment")


class DeploymentError(Exception):
    pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="Deploy packages to Acumatica")
    parser.add_argument("--instance-url", required=True, help="Acumatica instance URL")
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument("--package-date", required=True, help="Package date directory")
    return parser.parse_args()


class AcumaticaDeploymentClient:
    def __init__(self, instance_url: str, username: str, password: str):
        self.base_url = f"{instance_url}/entity/"
        self.customization_url = f"{instance_url}/CustomizationApi"
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self.username = username
        self.password = password

    #! Login
    def login(self) -> None:
        try:
            logger.info("=" * 50)
            logger.info("Authenticating with Acumatica...")
            response = self.session.post(
                f"{self.base_url}auth/login",
                json={"name": self.username, "password": self.password},
            )
            response.raise_for_status()
            logger.info("Authentication successful")
            logger.info("=" * 50)
        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise DeploymentError(f"Authentication failed: {str(e)}")

    #! Logout
    def logout(self) -> None:
        try:
            logger.info("=" * 50)
            logger.info("Logging out...")
            response = self.session.post(f"{self.base_url}auth/logout")
            response.raise_for_status()
            logger.info("Logout successful")
            logger.info("=" * 50)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Logout encountered an issue: {str(e)}")
        finally:
            self.session.close()

    def upload_file(self, file_path: str, project_data: Dict) -> Dict:
        try:
            logger.info("=" * 50)
            logger.info(f"Uploading package: {project_data['projectName']}")
            with open(file_path, "rb") as file:
                encoded_content = base64.b64encode(file.read()).decode("utf-8")
            project_data["projectContentBase64"] = encoded_content

            url = f"{self.customization_url}/Import"
            response = self.session.post(url=url, json=project_data)
            response.raise_for_status()

            logger.info(f"Upload successful for package: {project_data['projectName']}")
            logger.info("=" * 50)
            return {"success": True, "project_name": project_data["projectName"]}
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {e}")
            return {
                "success": False,
                "project_name": project_data["projectName"],
                "error": str(e),
            }

    def publish_customizations(self, project_names: List[str]) -> Dict:
        publish_data = {
            "isMergeWithExistingPackages": False,
            "isOnlyValidation": False,
            "isOnlyDbUpdates": False,
            "isReplayPreviouslyExecutedScripts": False,
            "projectNames": project_names,
            "tenantMode": "Current",
        }
        try:
            logger.info("=" * 50)
            logger.info("Starting publication process...")
            url = f"{self.customization_url}/publishBegin"
            response = self.session.post(url=url, data=json.dumps(publish_data))
            response.raise_for_status()
            logger.info("Publishing started successfully")
            logger.info("=" * 50)
            return {"success": True}
        except Exception as e:
            logger.error(f"Failed to start publishing: {str(e)}")
            return {"success": False, "error": str(e)}

    def check_publish_status(self) -> Dict:
        try:
            url = f"{self.customization_url}/publishEnd"
            response = self.session.post(url=url, json={})
            response.raise_for_status()

            status_data = response.json()
            return {
                "success": True,
                "is_complete": status_data.get("isCompleted", False),
                "is_failed": status_data.get("isFailed", False),
                "logs": status_data.get("log", []),
            }
        except Exception as e:
            logger.error(f"Error checking status: {str(e)}")
            return {
                "success": False,
                "is_complete": False,
                "is_failed": True,
                "error": str(e),
            }


#! Retrieve configuration for files to upload
def get_files_config(base_directory: Path, instance_url: str) -> List[Dict]:
    if not base_directory.exists():
        raise FileNotFoundError(f"Directory not found: {base_directory}")

    urls_for_base_21 = [
        "https://qa.readywire.com/maruti-acermotors",
        "https://dev.readywire.com",
    ]
    base_version = (
        "21" if any(url in instance_url for url in urls_for_base_21) else "20"
    )
    base_package_name = f"RW.Base.22.210.00{base_version}"

    project_configs = [
        {
            "file_path": f"{base_package_name}.zip",
            "project_data": {
                "projectLevel": 1,
                "projectName": base_package_name,
                "projectDescription": "This Package contains all screens but the GST related screens & dll",
            },
        },
        {
            "file_path": "RW.Screens.Extension.Files.23.213.0015.zip",
            "project_data": {
                "projectLevel": 2,
                "projectName": "RW.Screens.Extension.Files.23.213.0015",
                "projectDescription": "Contains customized screens of Acumatica",
            },
        },
        {
            "file_path": "RW.SiteMap.23.213.0015.zip",
            "project_data": {
                "projectLevel": 3,
                "projectName": "RW.SiteMap.23.213.0015",
                "projectDescription": "Readywire Product Navigation",
            },
        },
        {
            "file_path": "RW.Branding.23.213.0015.zip",
            "project_data": {
                "projectLevel": 4,
                "projectName": "RW.Branding.23.213.0015",
                "projectDescription": "Readywire Branding Info",
            },
        },
        {
            "file_path": "RW.Endpoints.23.213.0015.zip",
            "project_data": {
                "projectLevel": 5,
                "projectName": "RW.Endpoints.23.213.0015",
                "projectDescription": "APIs package",
            },
        },
        {
            "file_path": "RW.Security.23.213.0015.zip",
            "project_data": {
                "projectLevel": 6,
                "projectName": "RW.Security.23.213.0015",
                "projectDescription": "Roles & their access on screens",
            },
        },
        {
            "file_path": "RW.BusinessEvents.23.213.0015.zip",
            "project_data": {
                "projectLevel": 7,
                "projectName": "RW.BusinessEvents.23.213.0015",
                "projectDescription": "Business Events and corresponding Notification Templates",
            },
        },
        {
            "file_path": "RW.FinancialReports.23.213.0015.zip",
            "project_data": {
                "projectLevel": 8,
                "projectName": "RW.FinancialReports.23.213.0015",
                "projectDescription": "Readywire financial reports",
            },
        },
    ]

    configs = []
    for config in project_configs:
        file_path = base_directory / config["file_path"]
        if not file_path.exists():
            logger.warning(f"Customization project file not found: {file_path}")
            continue
        config["file_path"] = str(file_path)
        config["project_data"]["isReplaceIfExists"] = True
        configs.append(config)

    if not configs:
        raise FileNotFoundError(f"No valid package files found in {base_directory}")
    return configs


def deploy_packages(instance_url: str, username: str, password: str, package_date: str):

    base_directory = Path(rf"C:\Backups\pkg-backups\{package_date}")
    client = AcumaticaDeploymentClient(instance_url, username, password)
    files_config = get_files_config(base_directory, instance_url)
    project_names = [config["project_data"]["projectName"] for config in files_config]

    try:
        client.login()

        # Wait before upload
        logger.info("=" * 50)
        logger.info("Waiting 3 seconds before starting upload...")
        time.sleep(3)

        #! Upload files
        logger.info("=" * 50)
        logger.info("Starting package uploads...")
        upload_results = []
        for config in files_config:
            result = client.upload_file(config["file_path"], config["project_data"])
            upload_results.append(result)
            if not result["success"]:
                raise DeploymentError(f"Upload failed for {result['project_name']}")
        logger.info("=" * 50)

        # Wait before publishing
        logger.info("=" * 50)
        logger.info("Waiting 5 seconds before publishing...")
        time.sleep(5)

        #! Publish Customization Project
        logger.info("=" * 50)
        logger.info("Starting publication process...")
        publish_result = client.publish_customizations(project_names)
        if not publish_result["success"]:
            raise DeploymentError("Failed to start publishing")
        logger.info("=" * 50)

        #! Monitor publish status
        logger.info("=" * 50)
        logger.info("Monitoring publication status...")
        seen_logs = set()
        while True:
            status = client.check_publish_status()

            if not status["success"]:
                raise DeploymentError(
                    f"Error checking publish status: {status.get('error')}"
                )

            for log_entry in status.get("logs", []):
                log_type = log_entry.get("logType", "").upper()
                message = log_entry.get("message", "")
                log_identifier = f"{log_type}:{message}"

                if log_identifier not in seen_logs:
                    logger.info(f"[{log_type}] {message}")
                    seen_logs.add(log_identifier)

            if status["is_complete"]:
                if status["is_failed"]:
                    raise DeploymentError("Publishing completed with errors")
                logger.info("Publishing completed successfully!")
                logger.info("=" * 50)
                break

            time.sleep(5)  # Check status every 5 seconds

        logger.info("=" * 50)
        logger.info("Deployment completed successfully!")
        logger.info("=" * 50)
        return True

    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return False
    finally:
        if client.session.cookies:
            client.logout()


def main():
    try:
        args = parse_arguments()
        success = deploy_packages(
            instance_url=args.instance_url,
            username=args.username,
            password=args.password,
            package_date=args.package_date,
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
