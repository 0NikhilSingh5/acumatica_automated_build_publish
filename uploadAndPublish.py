import argparse
import requests
import json
import base64
import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import sys
import os
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)
logger = logging.getLogger("AcumaticaDeployment")


class DeploymentError(Exception):
    """Custom exception for deployment-related errors."""
    pass


@dataclass
class PackageConfig:
    """Data class to hold package configuration."""
    file_path: str
    project_level: int
    project_name: str
    project_description: str


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed command line arguments.
    """
    parser = argparse.ArgumentParser(description="Deploy packages to Acumatica")
    parser.add_argument("--instance-url", required=True, help="Acumatica instance URL")
    parser.add_argument("--username", required=True, help="Username for authentication")
    parser.add_argument("--password", required=True, help="Password for authentication")
    parser.add_argument("--package-dir", required=True, help="Directory containing packages")
    parser.add_argument("--config-file", help="JSON configuration file for packages")
    parser.add_argument("--wait-before-upload", type=int, default=3, 
                        help="Wait time in seconds before upload")
    parser.add_argument("--wait-before-publish", type=int, default=5, 
                        help="Wait time in seconds before publishing")
    return parser.parse_args()


class AcumaticaDeploymentClient:
    """
    Client for handling Acumatica deployments.
    
    Attributes:
        base_url (str): Base URL for Acumatica API endpoints.
        customization_url (str): URL for customization API.
        session (requests.Session): HTTP session for requests.
        username (str): Username for authentication.
        password (str): Password for authentication.
    """
    
    def __init__(self, instance_url: str, username: str, password: str):
        """
        Initialize the Acumatica deployment client.
        
        Args:
            instance_url (str): Acumatica instance URL.
            username (str): Username for authentication.
            password (str): Password for authentication.
        """
        self.base_url = f"{instance_url}/entity/"
        self.customization_url = f"{instance_url}/CustomizationApi"
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )
        self.username = username
        self.password = password

    def login(self) -> None:
        """
        Authenticate with Acumatica.
        
        Raises:
            DeploymentError: If authentication fails.
        """
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

    def logout(self) -> None:
        """
        Log out from Acumatica and close the session.
        """
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

    def upload_file(self, file_path: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload a package file to Acumatica.
        
        Args:
            file_path (str): Path to the package file.
            project_data (Dict[str, Any]): Project metadata.
            
        Returns:
            Dict[str, Any]: Result of the upload operation.
        """
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

    def publish_customizations(self, project_names: List[str], 
                               merge_with_existing: bool = False,
                               only_validation: bool = False,
                               only_db_updates: bool = False,
                               replay_previous: bool = False) -> Dict[str, Any]:
        """
        Publish customizations to Acumatica.
        
        Args:
            project_names (List[str]): List of project names to publish.
            merge_with_existing (bool): Whether to merge with existing packages.
            only_validation (bool): Whether to perform validation only.
            only_db_updates (bool): Whether to perform DB updates only.
            replay_previous (bool): Whether to replay previously executed scripts.
            
        Returns:
            Dict[str, Any]: Result of the publish operation.
        """
        publish_data = {
            "isMergeWithExistingPackages": merge_with_existing,
            "isOnlyValidation": only_validation,
            "isOnlyDbUpdates": only_db_updates,
            "isReplayPreviouslyExecutedScripts": replay_previous,
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

    def check_publish_status(self) -> Dict[str, Any]:
        """
        Check the status of the publish operation.
        
        Returns:
            Dict[str, Any]: Status information.
        """
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


def load_package_config(config_file: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load package configuration from a JSON file or return default configuration.
    
    Args:
        config_file (Optional[str]): Path to a JSON configuration file.
        
    Returns:
        List[Dict[str, Any]]: List of package configurations.
    """
    if config_file and os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Default configuration if no file provided
    return [
        {
            "file_pattern": "RW.Base.*.zip",
            "project_level": 1,
            "project_description": "This Package contains all screens but the GST related screens & dll"
        },
        {
            "file_pattern": "RW.Screens.Extension.Files.*.zip",
            "project_level": 2,
            "project_description": "Contains customized screens of Acumatica"
        },
        {
            "file_pattern": "RW.SiteMap.*.zip",
            "project_level": 3,
            "project_description": "Readywire Product Navigation"
        },
        {
            "file_pattern": "RW.Branding.*.zip",
            "project_level": 4,
            "project_description": "Readywire Branding Info"
        },
        {
            "file_pattern": "RW.Endpoints.*.zip",
            "project_level": 5,
            "project_description": "APIs package"
        },
        {
            "file_pattern": "RW.Security.*.zip",
            "project_level": 6,
            "project_description": "Roles & their access on screens"
        },
        {
            "file_pattern": "RW.BusinessEvents.*.zip",
            "project_level": 7,
            "project_description": "Business Events and corresponding Notification Templates"
        },
        {
            "file_pattern": "RW.FinancialReports.*.zip",
            "project_level": 8,
            "project_description": "Readywire financial reports"
        },
    ]


def find_package_files(base_directory: Path, config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Find package files based on configuration.
    
    Args:
        base_directory (Path): Directory containing package files.
        config (List[Dict[str, Any]]): Package configuration.
        
    Returns:
        List[Dict[str, Any]]: List of package configurations with file paths.
    """
    if not base_directory.exists():
        raise FileNotFoundError(f"Directory not found: {base_directory}")

    result = []
    for package_config in config:
        file_pattern = package_config["file_pattern"]
        matching_files = list(base_directory.glob(file_pattern))
        
        if not matching_files:
            logger.warning(f"No files found matching pattern: {file_pattern}")
            continue
            
        # Use the first matching file
        file_path = matching_files[0]
        project_name = file_path.stem
        
        project_data = {
            "projectLevel": package_config["project_level"],
            "projectName": project_name,
            "projectDescription": package_config["project_description"],
            "isReplaceIfExists": True
        }
        
        result.append({
            "file_path": str(file_path),
            "project_data": project_data
        })
    
    if not result:
        raise FileNotFoundError(f"No valid package files found in {base_directory}")
    
    return result


def deploy_packages(instance_url: str, username: str, password: str, package_dir: str, 
                    config_file: Optional[str] = None, wait_before_upload: int = 3, 
                    wait_before_publish: int = 5) -> bool:
    """
    Deploy packages to Acumatica.
    
    Args:
        instance_url (str): Acumatica instance URL.
        username (str): Username for authentication.
        password (str): Password for authentication.
        package_dir (str): Directory containing packages.
        config_file (Optional[str]): Package configuration file.
        wait_before_upload (int): Wait time in seconds before upload.
        wait_before_publish (int): Wait time in seconds before publishing.
        
    Returns:
        bool: True if deployment was successful, False otherwise.
    """
    base_directory = Path(package_dir)
    client = AcumaticaDeploymentClient(instance_url, username, password)
    
    # Load configuration and find files
    package_config = load_package_config(config_file)
    files_config = find_package_files(base_directory, package_config)
    project_names = [config["project_data"]["projectName"] for config in files_config]
    
    try:
        # Step 1: Login to Acumatica
        client.login()

        # Wait before upload
        logger.info("=" * 50)
        logger.info(f"Waiting {wait_before_upload} seconds before starting upload...")
        time.sleep(wait_before_upload)

        # Step 2: Upload files
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
        logger.info(f"Waiting {wait_before_publish} seconds before publishing...")
        time.sleep(wait_before_publish)

        # Step 3: Publish Customization Project
        logger.info("=" * 50)
        logger.info("Starting publication process...")
        publish_result = client.publish_customizations(project_names)
        if not publish_result["success"]:
            raise DeploymentError("Failed to start publishing")
        logger.info("=" * 50)

        # Step 4: Monitor publish status
        logger.info("=" * 50)
        logger.info("Monitoring publication status...")
        seen_logs = set()
        while True:
            status = client.check_publish_status()

            if not status["success"]:
                raise DeploymentError(
                    f"Error checking publish status: {status.get('error')}"
                )

            # Log any new messages
            for log_entry in status.get("logs", []):
                log_type = log_entry.get("logType", "").upper()
                message = log_entry.get("message", "")
                log_identifier = f"{log_type}:{message}"

                if log_identifier not in seen_logs:
                    logger.info(f"[{log_type}] {message}")
                    seen_logs.add(log_identifier)

            # Check if process is complete
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
        # Always attempt to logout if session exists
        if hasattr(client, 'session') and client.session.cookies:
            client.logout()

def main():
    """
    Main function to run the deployment process.
    """
    try:
        args = parse_arguments()
        success = deploy_packages(
            instance_url=args.instance_url,
            username=args.username,
            password=args.password,
            package_dir=args.package_dir,
            config_file=args.config_file,
            wait_before_upload=args.wait_before_upload,
            wait_before_publish=args.wait_before_publish
        )
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Critical error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()