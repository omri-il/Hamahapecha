"""Image handling — download from Telegram, resize for Instagram, serve publicly."""
import os
import uuid
import logging
from PIL import Image
from config import IMAGE_DIR, IMAGE_HOST_URL

logger = logging.getLogger(__name__)

# Instagram recommended sizes
IG_SQUARE = (1080, 1080)
IG_PORTRAIT = (1080, 1350)


def ensure_image_dir():
    os.makedirs(IMAGE_DIR, exist_ok=True)


async def download_and_process(bot, file_id: str, mode: str = "portrait") -> tuple[str, str]:
    """Download image from Telegram, resize for IG, return (local_path, public_url).

    Args:
        bot: telegram Bot instance
        file_id: Telegram file_id of the photo
        mode: "square" (1080x1080) or "portrait" (1080x1350)
    """
    ensure_image_dir()
    filename = f"{uuid.uuid4().hex}.jpg"
    local_path = os.path.join(IMAGE_DIR, filename)

    # Download from Telegram
    tg_file = await bot.get_file(file_id)
    await tg_file.download_to_drive(local_path)
    logger.info(f"Downloaded image to {local_path}")

    # Resize for Instagram
    target = IG_PORTRAIT if mode == "portrait" else IG_SQUARE
    resize_image(local_path, target)

    public_url = f"{IMAGE_HOST_URL}/{filename}"
    return local_path, public_url


def resize_image(path: str, target_size: tuple[int, int]):
    """Resize image to target size, maintaining aspect ratio with white padding."""
    img = Image.open(path)
    img = img.convert("RGB")

    # Calculate scaling to fit within target while maintaining aspect ratio
    target_w, target_h = target_size
    img_w, img_h = img.size
    scale = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Create white background and paste centered
    background = Image.new("RGB", target_size, (255, 255, 255))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    background.paste(img, (offset_x, offset_y))

    background.save(path, "JPEG", quality=95)
    logger.info(f"Resized image to {target_size}")
