"""GCP Secret Manager utilities for loading secrets into environment variables."""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def load_gcp_secret(secret_name: str, project_id: Optional[str] = None) -> Optional[str]:
    """
    Load a secret from GCP Secret Manager.

    Args:
        secret_name: Name of the secret
        project_id: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)

    Returns:
        Secret value or None if not found/not in GCP environment

    Raises:
        ImportError: If google-cloud-secret-manager is not installed
    """
    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.warning("google-cloud-secret-manager not installed, skipping GCP secret loading")
        return None

    # Get project ID
    if not project_id:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        logger.debug("GOOGLE_CLOUD_PROJECT not set, skipping GCP secret loading")
        return None

    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})
        secret_value = response.payload.data.decode("UTF-8")
        logger.debug(f"✓ Loaded secret '{secret_name}' from GCP Secret Manager")
        return secret_value
    except Exception as e:
        logger.warning(f"Failed to load secret '{secret_name}' from GCP: {str(e)}")
        return None


def load_gcp_secrets_to_env(project_id: Optional[str] = None):
    """
    Load all required secrets from GCP Secret Manager and set as environment variables.

    This function loads secrets and sets them as environment variables if they're not already set.

    Args:
        project_id: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
    """
    secrets_map = {
        # Email configuration
        "gmail-user": "SMTP_USER",
        "gmail-app-password": "SMTP_PASSWORD",
        "email-list": "EMAIL_LIST",

        # GitHub configuration
        "github-token": "GITHUB_TOKEN",
        "github-repo": "GITHUB_REPO",
        "github-username": "GITHUB_USERNAME",

        # WeChat configuration
        "wechat-app-id": "WECHAT_APP_ID",
        "wechat-app-secret": "WECHAT_APP_SECRET",

        # AI APIs
        "openai-api-key": "OPENAI_API_KEY",
        "grok-api-key": "XAI_API_KEY",
    }

    logger.info("Loading secrets from GCP Secret Manager...")

    loaded_count = 0
    for secret_name, env_var in secrets_map.items():
        # Skip if already set
        if os.getenv(env_var):
            logger.debug(f"✓ {env_var} already set, skipping")
            continue

        secret_value = load_gcp_secret(secret_name, project_id)
        if secret_value:
            os.environ[env_var] = secret_value
            loaded_count += 1
            logger.info(f"✓ Set {env_var} from GCP Secret Manager")

    if loaded_count > 0:
        logger.info(f"✓ Loaded {loaded_count} secrets from GCP Secret Manager")
    else:
        logger.debug("No secrets loaded from GCP Secret Manager (might not be in GCP environment)")
