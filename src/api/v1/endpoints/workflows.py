"""Workflow automation API endpoints for Cloud Scheduler."""

import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

router = APIRouter(prefix="/workflows", tags=["workflows"])

logger = logging.getLogger(__name__)


def run_workflow_script(workflow_type: str) -> Dict[str, Any]:
    """Execute the daily workflow script.

    Args:
        workflow_type: Type of workflow ('daily' or 'weekly')

    Returns:
        Dict with workflow execution status
    """
    try:
        # Get project root (workflows.py is in src/api/v1/endpoints/, so need 4 parents to get to project root)
        project_root = Path(__file__).parent.parent.parent.parent.parent
        workflow_script = project_root / "scripts" / "publish" / "daily_complete_workflow.py"

        if not workflow_script.exists():
            logger.error(f"Workflow script not found: {workflow_script}")
            return {
                "status": "error",
                "message": f"Workflow script not found: {workflow_script}",
                "timestamp": datetime.now().isoformat()
            }

        logger.info(f"Executing {workflow_type} workflow: {workflow_script}")

        # Run the workflow script
        result = subprocess.run(
            ["python", str(workflow_script)],
            capture_output=True,
            text=True,
            timeout=900,  # 15 minutes
            cwd=str(project_root)
        )

        logger.info(f"Workflow exit code: {result.returncode}")

        # Check if there's a results JSON file
        logs_dir = project_root / "logs"
        workflow_result = None

        if logs_dir.exists():
            # Find the most recent workflow log
            log_files = sorted(logs_dir.glob("workflow_*.json"), reverse=True)
            if log_files:
                try:
                    with open(log_files[0], 'r', encoding='utf-8') as f:
                        workflow_result = json.load(f)
                    logger.info(f"Workflow completed with status: {workflow_result.get('status')}")
                except Exception as e:
                    logger.warning(f"Could not read workflow result: {e}")

        # Return structured response
        if result.returncode == 0:
            return {
                "status": "success",
                "workflow_type": workflow_type,
                "message": f"{workflow_type.capitalize()} workflow completed successfully",
                "timestamp": datetime.now().isoformat(),
                "result": workflow_result
            }
        else:
            return {
                "status": "failed",
                "workflow_type": workflow_type,
                "message": f"{workflow_type.capitalize()} workflow failed",
                "timestamp": datetime.now().isoformat(),
                "error": result.stderr[:500] if result.stderr else None,
                "result": workflow_result
            }

    except subprocess.TimeoutExpired:
        logger.error(f"{workflow_type.capitalize()} workflow timeout (15 minutes)")
        return {
            "status": "timeout",
            "workflow_type": workflow_type,
            "message": f"{workflow_type.capitalize()} workflow timeout after 15 minutes",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"{workflow_type.capitalize()} workflow error: {e}", exc_info=True)
        return {
            "status": "error",
            "workflow_type": workflow_type,
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.post(
    "/daily",
    summary="Trigger daily workflow",
    description="Execute daily workflow: Data Collection → AI Scoring → Email → GitHub",
    response_model=Dict[str, Any]
)
async def trigger_daily_workflow(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger the daily news workflow.

    This endpoint is called by Cloud Scheduler every day at 9:00 AM Beijing Time.

    Workflow steps:
    1. Data Collection - Collect latest AI news from all sources
    2. AI Scoring - Score collected news with OpenAI
    3. Email Publishing - Send top news to subscribers
    4. GitHub Publishing - Publish to GitHub Pages

    Returns:
        Dict with workflow execution status
    """
    logger.info("Daily workflow triggered via Cloud Scheduler")

    # Run workflow synchronously for Cloud Scheduler (it needs the response)
    result = run_workflow_script("daily")

    return result


@router.post(
    "/weekly",
    summary="Trigger weekly workflow",
    description="Execute weekly report workflow: Data Collection → AI Scoring → Weekly Report → Email → GitHub",
    response_model=Dict[str, Any]
)
async def trigger_weekly_workflow(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger the weekly news digest workflow.

    This endpoint is called by Cloud Scheduler every Sunday at 10:00 AM Beijing Time.

    Workflow steps:
    1. Data Collection - Collect latest AI news from all sources
    2. AI Scoring - Score collected news with OpenAI
    3. Weekly Report - Generate weekly digest and analysis
    4. Email Publishing - Send weekly report to subscribers
    5. GitHub Publishing - Publish to GitHub Pages

    Returns:
        Dict with workflow execution status
    """
    logger.info("Weekly workflow triggered via Cloud Scheduler")

    # Run workflow synchronously for Cloud Scheduler (it needs the response)
    result = run_workflow_script("weekly")

    return result


@router.get(
    "/status",
    summary="Get workflow execution status",
    description="Check the status of the most recent workflow execution",
    response_model=Dict[str, Any]
)
async def get_workflow_status() -> Dict[str, Any]:
    """Get the status of the most recent workflow execution.

    Returns:
        Dict with the latest workflow result from logs
    """
    try:
        project_root = Path(__file__).parent.parent.parent.parent
        logs_dir = project_root / "logs"

        if not logs_dir.exists():
            return {
                "status": "no_logs",
                "message": "No workflow logs found",
                "timestamp": datetime.now().isoformat()
            }

        # Find the most recent workflow log
        log_files = sorted(logs_dir.glob("workflow_*.json"), reverse=True)
        if not log_files:
            return {
                "status": "no_logs",
                "message": "No workflow logs found",
                "timestamp": datetime.now().isoformat()
            }

        # Read the most recent log
        with open(log_files[0], 'r', encoding='utf-8') as f:
            workflow_result = json.load(f)

        return {
            "status": "success",
            "message": "Latest workflow status retrieved",
            "timestamp": datetime.now().isoformat(),
            "result": workflow_result,
            "log_file": log_files[0].name
        }

    except Exception as e:
        logger.error(f"Error reading workflow status: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }
