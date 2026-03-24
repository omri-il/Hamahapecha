"""Instagram Graph API client — two-step media publishing."""
import logging
import requests
from config import INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID

logger = logging.getLogger(__name__)

GRAPH_API_BASE = "https://graph.facebook.com/v21.0"


def create_media_container(image_url: str, caption: str) -> str:
    """Step 1: Create a media container with image URL and caption.
    Returns the container/creation ID."""
    url = f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
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
    url = f"{GRAPH_API_BASE}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
    params = {
        "creation_id": creation_id,
        "access_token": INSTAGRAM_ACCESS_TOKEN,
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
    """Full publish flow: create container → publish. Returns post ID."""
    container_id = create_media_container(image_url, caption)
    post_id = publish_media(container_id)
    return post_id


def check_token_valid() -> bool:
    """Verify the access token is still valid."""
    url = f"{GRAPH_API_BASE}/me"
    params = {"access_token": INSTAGRAM_ACCESS_TOKEN}
    try:
        resp = requests.get(url, params=params, timeout=10)
        return "id" in resp.json()
    except Exception:
        return False
