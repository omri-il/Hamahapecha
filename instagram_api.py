"""Instagram Graph API client — two-step media publishing with auto token refresh."""
import logging
import requests
from pathlib import Path

import config

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v25.0"
# Refresh token when less than 7 days remain
REFRESH_THRESHOLD_SECONDS = 7 * 24 * 60 * 60


def _get_token():
    """Get the current access token."""
    return config.INSTAGRAM_ACCESS_TOKEN


def _update_env_token(new_token: str):
    """Update the .env file with a new access token."""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        logger.warning(".env file not found, cannot save refreshed token")
        return

    lines = env_path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        if line.startswith("INSTAGRAM_ACCESS_TOKEN="):
            new_lines.append(f"INSTAGRAM_ACCESS_TOKEN={new_token}")
        else:
            new_lines.append(line)
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    logger.info("Saved refreshed token to .env")


def _get_token_expiry() -> int | None:
    """Check when the current token expires. Returns seconds until expiry, or None on error."""
    token = _get_token()
    app_token = f"{config.META_APP_ID}|{config.META_APP_SECRET}"
    try:
        resp = requests.get(
            f"{GRAPH_API_BASE}/debug_token",
            params={"input_token": token, "access_token": app_token},
            timeout=10,
        )
        data = resp.json().get("data", {})
        expires_at = data.get("expires_at", 0)
        if expires_at == 0:
            return None
        import time
        return expires_at - int(time.time())
    except Exception as e:
        logger.error(f"Failed to check token expiry: {e}")
        return None


def refresh_token_if_needed() -> bool:
    """Check token expiry and refresh if within threshold. Returns True if refreshed."""
    if not config.META_APP_ID or not config.META_APP_SECRET:
        logger.warning("META_APP_ID/META_APP_SECRET not set, cannot auto-refresh token")
        return False

    seconds_left = _get_token_expiry()
    if seconds_left is None:
        logger.warning("Could not determine token expiry")
        return False

    days_left = seconds_left / 86400
    logger.info(f"Instagram token expires in {days_left:.1f} days")

    if seconds_left > REFRESH_THRESHOLD_SECONDS:
        return False

    # Refresh the token
    logger.info("Token expiring soon, refreshing...")
    try:
        resp = requests.get(
            f"{GRAPH_API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": config.META_APP_ID,
                "client_secret": config.META_APP_SECRET,
                "fb_exchange_token": _get_token(),
            },
            timeout=15,
        )
        data = resp.json()
        new_token = data.get("access_token")
        if not new_token:
            error_msg = data.get("error", {}).get("message", str(data))
            logger.error(f"Token refresh failed: {error_msg}")
            return False

        # Update in-memory and on disk
        config.INSTAGRAM_ACCESS_TOKEN = new_token
        _update_env_token(new_token)
        logger.info("Token refreshed successfully (valid for ~60 days)")
        return True

    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        return False


def create_media_container(image_url: str, caption: str) -> str:
    """Step 1: Create a media container with image URL and caption.
    Returns the container/creation ID."""
    url = f"{GRAPH_API_BASE}/{config.INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": _get_token(),
    }
    resp = requests.post(url, params=params, timeout=30)
    data = resp.json()

    if "id" not in data:
        error_msg = data.get("error", {}).get("message", str(data))
        logger.error(f"Failed to create media container: {error_msg}")
        raise Exception(f"Instagram API error: {error_msg}")

    logger.info(f"Media container created: {data['id']}")
    return data["id"]


def publish_media(creation_id: str) -> str:
    """Step 2: Publish the media container. Returns the published post ID."""
    url = f"{GRAPH_API_BASE}/{config.INSTAGRAM_ACCOUNT_ID}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": _get_token(),
    }
    resp = requests.post(url, params=params, timeout=30)
    data = resp.json()

    if "id" not in data:
        error_msg = data.get("error", {}).get("message", str(data))
        logger.error(f"Failed to publish media: {error_msg}")
        raise Exception(f"Instagram publish error: {error_msg}")

    logger.info(f"Post published: {data['id']}")
    return data["id"]


def publish_to_instagram(image_url: str, caption: str) -> str:
    """Full publish flow: refresh token if needed → create container → publish."""
    refresh_token_if_needed()
    container_id = create_media_container(image_url, caption)
    post_id = publish_media(container_id)
    return post_id


def check_token_valid() -> bool:
    """Verify the access token is still valid."""
    url = f"{GRAPH_API_BASE}/me"
    params = {"access_token": _get_token()}
    try:
        resp = requests.get(url, params=params, timeout=10)
        return "id" in resp.json()
    except Exception:
        return False
