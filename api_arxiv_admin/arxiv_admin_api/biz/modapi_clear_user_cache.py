"""Clear user cache using modapi."""

from typing import Optional
from arxiv.base import logging

from ..apis.modapi.modapi_client.api_client import ApiClient
from ..apis.modapi.modapi_client.api.debugging_api import DebuggingApi
from ..apis.modapi.modapi_client.configuration import Configuration

logger = logging.getLogger(__name__)


def _get_modapi_client(
    base_url: str = "https://services.dev.arxiv.org",
    auth_token: Optional[str] = None
) -> DebuggingApi:
    """Get a configured modapi debugging API client instance."""
    config = Configuration(host=base_url)

    # Set up authentication headers if provided
    api_client = ApiClient(configuration=config)

    # Create debugging API instance
    debugging_api = DebuggingApi(api_client=api_client)

    return debugging_api


async def modapi_clear_user_cache(
    user_id: int,
    base_url: str = "https://services.dev.arxiv.org",
    authorization: Optional[str] = None,
    modkey: Optional[str] = None,
    arxivng_session_id: Optional[str] = None
) -> Optional[dict]:
    """
    Clear the stored user cache for a given user ID using modapi.

    Args:
        user_id: The user ID to clear from cache
        base_url: The base URL for the modapi service
        authorization: Bearer token for authentication (will be prefixed with "Bearer ")
        modkey: Modkey header for authentication
        arxivng_session_id: Session cookie for authentication

    Returns:
        Response data from the API call, or None if there was an error

    Raises:
        ValueError: If user_id is invalid
        Exception: If the API call fails
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError(f"Invalid user_id: {user_id}. Must be a positive integer.")

    logger.info(f"Clearing user cache for user_id: {user_id}")

    try:
        debugging_api = _get_modapi_client(base_url=base_url, auth_token=authorization)

        # Call the modapi debugging endpoint
        result = debugging_api.debug_clear_stored_user_debug_clear_stored_user_get(
            clear_user_id=user_id,
            authorization=f"Bearer {authorization}" if authorization else None,
            modkey=modkey,
            arxivng_session_id=arxivng_session_id,
        )

        logger.info(f"Successfully cleared user cache for user_id: {user_id}")
        return result

    except Exception as e:
        logger.error(f"Failed to clear user cache for user_id {user_id}: {e}")
        raise


# Synchronous wrapper for compatibility
def modapi_clear_user_cache_sync(
    user_id: int,
    base_url: str = "https://services.dev.arxiv.org",
    authorization: Optional[str] = None,
    modkey: Optional[str] = None,
    arxivng_session_id: Optional[str] = None
) -> Optional[dict]:
    """
    Synchronous wrapper for clearing user cache.

    Args:
        user_id: The user ID to clear from cache
        base_url: The base URL for the modapi service
        authorization: Bearer token for authentication
        modkey: Modkey header for authentication
        arxivng_session_id: Session cookie for authentication

    Returns:
        Response data from the API call, or None if there was an error
    """
    import asyncio

    try:
        # Try to get existing event loop
        loop = asyncio.get_running_loop()
        # If we're in an async context, create a new task
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    modapi_clear_user_cache(
                        user_id=user_id,
                        base_url=base_url,
                        authorization=authorization,
                        modkey=modkey,
                        arxivng_session_id=arxivng_session_id
                    )
                )
                return future.result()
        else:
            return asyncio.run(
                modapi_clear_user_cache(
                    user_id=user_id,
                    base_url=base_url,
                    authorization=authorization,
                    modkey=modkey,
                    arxivng_session_id=arxivng_session_id
                )
            )
    except RuntimeError:
        # No event loop, safe to use asyncio.run
        return asyncio.run(
            modapi_clear_user_cache(
                user_id=user_id,
                base_url=base_url,
                authorization=authorization,
                modkey=modkey,
                arxivng_session_id=arxivng_session_id
            )
        )