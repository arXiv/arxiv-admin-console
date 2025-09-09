"""
Send notification messages to the arXiv messaging service via Pub/Sub
"""

import json
import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from google.cloud import pubsub_v1
from google.oauth2 import service_account
from google.auth.transport.requests import Request


from enum import Enum

# Import EventType from the main server module
class EventType(Enum):
    NOTIFICATION = "NOTIFICATION"
    ALERT = "ALERT"
    WARNING = "WARNING"
    INFO = "INFO"


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
        logger=None
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
        response = requests.post(url, headers=headers, json=payload)
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


def send_notification(
        subject: str,
        message: str,
        user_id: Optional[Union[str, List[str]]] = None,
        email_to: Optional[str] = None,
        sender: str = "no-reply@arxiv.org",
        event_type: Union[EventType, str] = EventType.NOTIFICATION,
        metadata: Optional[Dict[str, Any]] = None,
        project_id: Optional[str] = None,
        topic_name: str = "notification-events",
        logger=None
) -> str:
    """
    Send a notification message to the arXiv messaging service via Pub/Sub

    Args:
        subject: Message subject line
        message: Message content
        user_id: Target user identifier(s) - can be single string or list of strings (for registered users)
        email_to: Direct email address (for email gateway mode)
        sender: Sender email address (default: no-reply@arxiv.org)
        event_type: Event type (EventType enum or string: NOTIFICATION, ALERT, WARNING, INFO)
        metadata: Optional metadata dictionary
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var or arxiv-development)
        topic_name: Pub/Sub topic name (default: notification-events)
        logger: Logger object for structured logging

    Returns:
        str: Published message ID

    Raises:
        Exception: If message publishing fails or neither user_id nor email_to provided
    """
    # Validate that either user_id or email_to is provided
    if not user_id and not email_to:
        raise Exception("Either user_id or email_to must be provided")

    # Default project ID
    if not project_id:
        project_id = os.getenv('GCP_PROJECT_ID', 'arxiv-development')

    # Default metadata
    if metadata is None:
        metadata = {}

    # Create publisher client with explicit credentials
    try:
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
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
        if logger:
            logger.error("Failed to create Pub/Sub client", extra={"error": str(e)})
        raise Exception(f"Failed to create Pub/Sub client: {str(e)}")

    # Generate unique event ID
    if user_id:
        if isinstance(user_id, list):
            identifier = f"multi-{len(user_id)}-users"
        else:
            identifier = user_id
    else:
        identifier = email_to
    event_id = f"event-{identifier}-{int(datetime.now().timestamp())}"

    # Convert EventType enum to string value if needed
    event_type_str = event_type.value if isinstance(event_type, EventType) else event_type

    # Create event message
    event_data = {
        "event_id": event_id,
        "user_id": user_id,
        "event_type": event_type_str,
        "message": message,
        "sender": sender,
        "subject": subject,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metadata": metadata
    }

    # Add email_to field for email gateway mode
    if email_to:
        event_data["email_to"] = email_to

    # Convert to JSON and encode
    message_json = json.dumps(event_data)
    message_bytes = message_json.encode('utf-8')

    # Log the notification attempt
    if logger:
        if isinstance(user_id, list):
            logger.info("Sending multi-user notification",
                        extra={
                            "user_count": len(user_id),
                            "users": user_id[:5],  # Log first 5 users to avoid spam
                            "subject": subject,
                            "event_type": event_type,
                            "sender": sender,
                            "topic": topic_name,
                            "project_id": project_id
                        })
        else:
            logger.info("Sending notification",
                        extra={
                            "user_id": user_id,
                            "subject": subject,
                            "event_type": event_type,
                            "sender": sender,
                            "topic": topic_name,
                            "project_id": project_id
                        })

    try:
        # Try publishing via Python client first
        future = publisher.publish(topic_path, message_bytes)
        message_id = future.result()

        # Log success
        if logger:
            logger.info("Notification published successfully via Python client",
                        extra={
                            "message_id": message_id,
                            "event_id": event_id,
                            "user_id": user_id,
                            "topic_path": topic_path
                        })

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

                if logger:
                    logger.info("Notification published successfully via REST API fallback",
                                extra={
                                    "message_id": message_id,
                                    "event_id": event_id,
                                    "user_id": user_id,
                                    "topic_path": topic_path,
                                    "method": "rest_api_fallback"
                                })

                return message_id

            except Exception as rest_error:
                if logger:
                    logger.error("Both Python client and REST API failed",
                                 extra={
                                     "python_error": str(e),
                                     "rest_error": str(rest_error)
                                 })
                raise Exception(f"Failed to publish via both methods - Python client: {str(e)}, REST API: {str(rest_error)}")

        # No fallback available, re-raise original error
        if logger:
            logger.error("Failed to publish notification",
                         extra={
                             "user_id": user_id,
                             "subject": subject,
                             "error": str(e),
                             "topic_path": topic_path,
                             "error_type": type(e).__name__
                         })

        raise Exception(f"Failed to publish to {topic_path}: {str(e)}")
