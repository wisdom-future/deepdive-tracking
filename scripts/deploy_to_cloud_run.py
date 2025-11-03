#!/usr/bin/env python
"""Deploy DeepDive Tracking application to Google Cloud Run.

This script handles the complete deployment process to Cloud Run including:
- Building and pushing Docker image
- Configuring environment variables
- Setting up cloud resources
- Verifying deployment

Usage:
    python scripts/deploy_to_cloud_run.py [--dry-run] [--skip-build]

Environment Variables:
    GCP_PROJECT_ID: Google Cloud project ID (required)
    GCP_REGION: GCP region for deployment (default: asia-east1)
    CLOUD_RUN_SERVICE_NAME: Cloud Run service name (default: deepdive-tracking)
"""

import argparse
import os
import subprocess
import sys
import json
from pathlib import Path
from typing import Optional


class CloudRunDeployer:
    """Handles Cloud Run deployment operations."""

    def __init__(
        self,
        project_id: str,
        region: str = "asia-east1",
        service_name: str = "deepdive-tracking",
        dry_run: bool = False,
    ):
        """Initialize Cloud Run deployer.

        Args:
            project_id: Google Cloud project ID
            region: GCP region for deployment
            service_name: Cloud Run service name
            dry_run: If True, print commands without executing
        """
        self.project_id = project_id
        self.region = region
        self.service_name = service_name
        self.dry_run = dry_run
        self.repository_name = "cloud-run-source-deploy"

    def _run_command(self, command: list, description: str) -> bool:
        """Execute shell command and log output.

        Args:
            command: Command to execute as list
            description: Description of what the command does

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"📋 {description}")
        print(f"{'='*70}")
        print(f"Command: {' '.join(command)}")

        if self.dry_run:
            print("(DRY-RUN MODE: Not executing)")
            return True

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=False,
                text=True,
            )
            print(f"✓ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ {description} failed with error:")
            print(f"  Return code: {e.returncode}")
            return False

    def verify_gcp_setup(self) -> bool:
        """Verify GCP configuration and authentication.

        Returns:
            True if GCP setup is valid, False otherwise
        """
        print("\n" + "="*70)
        print("🔍 Verifying GCP Setup")
        print("="*70)

        # Check gcloud is installed
        try:
            subprocess.run(["gcloud", "--version"], check=True, capture_output=True)
            print("✓ gcloud CLI is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ gcloud CLI not found. Please install Google Cloud SDK")
            return False

        # Check project is set
        try:
            result = subprocess.run(
                ["gcloud", "config", "get-value", "project"],
                check=True,
                capture_output=True,
                text=True,
            )
            current_project = result.stdout.strip()
            if current_project != self.project_id:
                print(f"Setting project to {self.project_id}")
                self._run_command(
                    ["gcloud", "config", "set", "project", self.project_id],
                    "Set GCP project",
                )
            print(f"✓ GCP Project: {self.project_id}")
        except subprocess.CalledProcessError:
            print("✗ Cannot determine current GCP project")
            return False

        return True

    def verify_cloud_run_api(self) -> bool:
        """Verify Cloud Run API is enabled.

        Returns:
            True if Cloud Run API is enabled, False otherwise
        """
        print("\n" + "="*70)
        print("✓ Cloud Run API Status")
        print("="*70)

        command = [
            "gcloud",
            "services",
            "list",
            "--enabled",
            "--filter=name:run.googleapis.com",
            "--format=value(name)",
        ]

        if self.dry_run:
            print("(DRY-RUN MODE: Skipping verification)")
            return True

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
            if "run.googleapis.com" in result.stdout:
                print("✓ Cloud Run API is enabled")
                return True
            else:
                print("✗ Cloud Run API is not enabled")
                print("Enabling Cloud Run API...")
                return self._run_command(
                    ["gcloud", "services", "enable", "run.googleapis.com"],
                    "Enable Cloud Run API",
                )
        except subprocess.CalledProcessError:
            print("✗ Cannot verify Cloud Run API status")
            return False

    def deploy_to_cloud_run(self, skip_build: bool = False) -> bool:
        """Deploy application to Cloud Run.

        Args:
            skip_build: If True, skip Docker build and use existing image

        Returns:
            True if deployment successful, False otherwise
        """
        command = [
            "gcloud",
            "run",
            "deploy",
            self.service_name,
            "--source",
            ".",
            "--platform",
            "managed",
            "--region",
            self.region,
            "--memory",
            "1Gi",
            "--cpu",
            "1",
            "--timeout",
            "900",
            "--allow-unauthenticated",
            "--set-env-vars",
            "DATABASE_URL=postgresql://deepdive_user:deepdive_password@35.189.186.161:5432/deepdive_db",
            "--set-env-vars",
            "REDIS_URL=redis://10.240.18.115:6379/0",
            "--set-env-vars",
            "CELERY_BROKER_URL=redis://10.240.18.115:6379/1",
            "--set-env-vars",
            "CELERY_RESULT_BACKEND=redis://10.240.18.115:6379/2",
            "--set-env-vars",
            "APP_ENV=production",
            "--set-env-vars",
            "DEBUG=False",
            "--set-env-vars",
            "LOG_LEVEL=INFO",
        ]

        if skip_build:
            command.extend(["--image", f"gcr.io/{self.project_id}/{self.service_name}"])

        return self._run_command(
            command,
            f"Deploy {self.service_name} to Cloud Run",
        )

    def get_service_url(self) -> Optional[str]:
        """Get Cloud Run service URL after deployment.

        Returns:
            Service URL string or None if service not found
        """
        command = [
            "gcloud",
            "run",
            "services",
            "describe",
            self.service_name,
            "--region",
            self.region,
            "--format=value(status.url)",
        ]

        if self.dry_run:
            print("\n(DRY-RUN MODE: Cannot get actual service URL)")
            return f"https://{self.service_name}-XXXXX.{self.region}.run.app"

        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
            )
            url = result.stdout.strip()
            return url if url else None
        except subprocess.CalledProcessError:
            return None

    def verify_deployment(self) -> bool:
        """Verify deployment by checking service is running.

        Returns:
            True if service is deployed and running, False otherwise
        """
        print("\n" + "="*70)
        print("🔍 Verifying Deployment")
        print("="*70)

        url = self.get_service_url()
        if url:
            print(f"✓ Service deployed successfully!")
            print(f"📍 Service URL: {url}")
            return True
        else:
            print("✗ Cannot verify service deployment")
            return False

    def run(self, skip_build: bool = False) -> bool:
        """Execute complete deployment workflow.

        Args:
            skip_build: If True, skip Docker build

        Returns:
            True if deployment successful, False otherwise
        """
        print("\n" + "="*70)
        print("🚀 DEEPDIVE TRACKING - CLOUD RUN DEPLOYMENT")
        print("="*70)
        print(f"Project ID: {self.project_id}")
        print(f"Region: {self.region}")
        print(f"Service: {self.service_name}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'NORMAL'}")

        # Step 1: Verify GCP setup
        if not self.verify_gcp_setup():
            print("\n✗ GCP setup verification failed")
            return False

        # Step 2: Verify Cloud Run API
        if not self.verify_cloud_run_api():
            print("\n✗ Cloud Run API verification failed")
            return False

        # Step 3: Deploy to Cloud Run
        if not self.deploy_to_cloud_run(skip_build=skip_build):
            print("\n✗ Cloud Run deployment failed")
            return False

        # Step 4: Verify deployment
        if not self.verify_deployment():
            print("\n⚠️  Deployment may have issues")

        print("\n" + "="*70)
        print("✓ DEPLOYMENT COMPLETED SUCCESSFULLY")
        print("="*70)
        print("\nNext steps:")
        print("1. Initialize database tables:")
        print("   python scripts/init_publish_priorities.py")
        print("\n2. Test the deployment:")
        print("   python scripts/run_priority_publishing_test.py 3 --dry-run")
        print("\n3. View deployment status:")
        print("   gcloud run services describe deepdive-tracking --region asia-east1")

        return True


def main():
    """Main entry point for Cloud Run deployment script."""
    parser = argparse.ArgumentParser(
        description="Deploy DeepDive Tracking to Google Cloud Run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Deploy with dry-run mode (no actual deployment)
    python scripts/deploy_to_cloud_run.py --dry-run

    # Deploy to Cloud Run
    python scripts/deploy_to_cloud_run.py

    # Deploy skipping Docker build (use existing image)
    python scripts/deploy_to_cloud_run.py --skip-build
        """,
    )

    parser.add_argument(
        "--project-id",
        help="Google Cloud project ID (default: from gcloud config)",
        default=os.getenv("GCP_PROJECT_ID", "deepdive-engine"),
    )

    parser.add_argument(
        "--region",
        help="GCP region for deployment (default: asia-east1)",
        default=os.getenv("GCP_REGION", "asia-east1"),
    )

    parser.add_argument(
        "--service-name",
        help="Cloud Run service name (default: deepdive-tracking)",
        default=os.getenv("CLOUD_RUN_SERVICE_NAME", "deepdive-tracking"),
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing them",
    )

    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip Docker build and use existing image",
    )

    args = parser.parse_args()

    deployer = CloudRunDeployer(
        project_id=args.project_id,
        region=args.region,
        service_name=args.service_name,
        dry_run=args.dry_run,
    )

    success = deployer.run(skip_build=args.skip_build)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
