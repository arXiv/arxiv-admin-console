"""
Send notification messages to the arXiv messaging service via Pub/Sub
"""

import json
import logging
import os
import httpx
from typing import Optional
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from pydantic import BaseModel


def _get_access_token(credentials_path: str) -> str:
    """Get access token using service account credentials"""
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/pubsub']
    )
    credentials.refresh(Request())
    return credentials.token


def _send_via_rest_api(
        project_id: str,
        topic_name: str,
        message_data: str,
        credentials_path: str,
        logger: Optional[logging.Logger]=None
) -> str:
    """Send message via REST API as fallback"""
    try:
        # Get access token
        access_token = _get_access_token(credentials_path)

        # Prepare REST API call
        url = f"https://pubsub.googleapis.com/v1/projects/{project_id}/topics/{topic_name}:publish"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Prepare message payload
        import base64
        encoded_data = base64.b64encode(message_data.encode('utf-8')).decode('utf-8')
        payload = {
            'messages': [
                {
                    'data': encoded_data
                }
            ]
        }

        # Make the request
        response = httpx.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        message_id = result.get('messageIds', [None])[0]

        if logger:
            logger.info("Message published via REST API", extra={"message_id": message_id})

        return message_id

    except Exception as e:
        if logger:
            logger.error("REST API publish failed", extra={"error": str(e)})
        raise


def post_pubsub_event(
        message: dict | BaseModel,
        project_id: Optional[str] = None,
        topic_name: str = "unnamed-topic",
        logger: Optional[logging.Logger] = None,
        dump_options: Optional[dict] = None,
        creds_name: Optional[str] = None,
) -> str:
    """
    Send a notification message to the arXiv messaging service via Pub/Sub

    Args:
        message: Message content as a pydantic model instance
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var or arxiv-development)
        topic_name: Pub/Sub topic name (default: notification-events)
        logger: Logger object for structured logging
        dump_options: Options for JSON serialization (default: {})

    Returns:
        str: Published message ID

    Raises:
        Exception: If message publishing fails or neither user_id nor email_to provided
    """
    # Default project ID
    if not project_id:
        project_id = os.getenv('GCP_PROJECT_ID', 'arxiv-development')

    extra = {
        "topic": topic_name,
        "project_id": project_id
    }

    if dump_options is None:
        dump_options = {}

    if creds_name is None:
        creds_name = 'GOOGLE_APPLICATION_CREDENTIALS'

    # Create publisher client with explicit credentials
    try:
        credentials_path = os.getenv(creds_name)
        if credentials_path and os.path.exists(credentials_path):
            from google.oauth2 import service_account
            # Specify the Pub/Sub scopes explicitly
            scopes = ['https://www.googleapis.com/auth/pubsub']
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
            publisher = pubsub_v1.PublisherClient(credentials=credentials)
        else:
            publisher = pubsub_v1.PublisherClient()

        topic_path = publisher.topic_path(project_id, topic_name)

    except Exception as e:
        extra.update({"error": str(e)})
        if logger:
            logger.error("Failed to create Pub/Sub client", extra=extra)
        raise Exception(f"Failed to create Pub/Sub client: {str(e)}")

    # Convert to JSON and encode
    if isinstance(message, dict):
        message_json = json.dumps(message, **dump_options)
    elif isinstance(message, BaseModel):
        message_json = message.model_dump_json(**dump_options)
    else:
        raise Exception(f"Unsupported message type: {type(message)}")

    # Log the notification attempt
    if logger:
        logger.info("Sending message", extra=extra)

    message_bytes = message_json.encode('utf-8')
    try:
        # Try publishing via Python client first
        future = publisher.publish(topic_path, message_bytes)
        message_id = future.result()
        extra.update({"message_id": message_id})

        # Log success
        if logger:
            logger.info("Event published successfully via Python client",
                        extra=extra)
        return message_id

    except Exception as e:
        # Try REST API fallback if Python client fails
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if credentials_path and os.path.exists(credentials_path):
            if logger:
                logger.warning("Python client failed, trying REST API fallback",
                               extra={"error": str(e)})

            try:
                message_id = _send_via_rest_api(
                    project_id, topic_name, message_json, credentials_path, logger
                )
                extra.update({"message_id": message_id})

                if logger:
                    logger.info("Notification published successfully via REST API fallback", extra=extra)
                return message_id

            except Exception as rest_error:
                extra.update({"error": str(e)})
                if logger:
                    logger.error("Both Python client and REST API failed", extra=extra)
                raise Exception(f"Failed to publish via both methods - Python client: {str(e)}, REST API: {str(rest_error)}")

        # No fallback available, re-raise original error
        if logger:
            logger.error("Failed to publish notification", extra=extra)

        raise Exception(f"Failed to publish to {topic_path}: {str(e)}")
