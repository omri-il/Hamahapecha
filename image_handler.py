"""Image handling — download from Telegram, transform with Nano Banana Pro for Instagram."""
import os
import uuid
import base64
import logging
from google import genai
from config import IMAGE_DIR, IMAGE_HOST_URL, GEMINI_API_KEY

logger = logging.getLogger(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)
NANO_BANANA_MODEL = "gemini-3-pro-image-preview"


def ensure_image_dir():
    os.makedirs(IMAGE_DIR, exist_ok=True)


async def download_and_process(bot, file_id: str, mode: str = "portrait") -> tuple[str, str]:
    """Download image from Telegram, transform with Nano Banana Pro for IG.

    Args:
        bot: telegram Bot instance
        file_id: Telegram file_id of the photo
        mode: "square" (1:1) or "portrait" (4:5)
    """
    ensure_image_dir()

    # Download from Telegram to temp file
    temp_filename = f"temp_{uuid.uuid4().hex}.jpg"
    temp_path = os.path.join(IMAGE_DIR, temp_filename)
    tg_file = await bot.get_file(file_id)
    await tg_file.download_to_drive(temp_path)
    logger.info(f"Downloaded image to {temp_path}")

    # Transform with Nano Banana Pro
    output_filename = f"{uuid.uuid4().hex}.jpg"
    output_path = os.path.join(IMAGE_DIR, output_filename)

    try:
        await transform_for_instagram(temp_path, output_path, mode)
        # Clean up temp file
        os.remove(temp_path)
    except Exception as e:
        logger.warning(f"Nano Banana Pro failed ({e}), falling back to Pillow resize")
        _pillow_resize(temp_path, output_path, mode)
        os.remove(temp_path)

    public_url = f"{IMAGE_HOST_URL}/{output_filename}"
    return output_path, public_url


async def transform_for_instagram(input_path: str, output_path: str, mode: str = "portrait"):
    """Use Nano Banana Pro to intelligently adapt image for Instagram."""
    # Read image as base64
    with open(input_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    if mode == "square":
        aspect = "1:1 (1080x1080)"
        dimensions = "square"
    else:
        aspect = "4:5 (1080x1350)"
        dimensions = "portrait"

    prompt = (
        f"Adapt this image for an Instagram {dimensions} post ({aspect} aspect ratio). "
        f"Keep the original content and style intact. "
        f"Make it visually appealing for social media — ensure good composition, "
        f"vibrant colors, and that the main subject fills the frame well. "
        f"Do not add any text or watermarks. Output the image only."
    )

    response = client.models.generate_content(
        model=NANO_BANANA_MODEL,
        contents=[
            prompt,
            {"mime_type": "image/jpeg", "data": image_data}
        ]
    )

    # Extract generated image from response
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = base64.b64decode(part.inline_data.data)
            with open(output_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Nano Banana Pro transformed image saved to {output_path}")
            return

    raise Exception("No image returned from Nano Banana Pro")


def _pillow_resize(input_path: str, output_path: str, mode: str = "portrait"):
    """Fallback: simple Pillow resize with white padding."""
    from PIL import Image

    target_size = (1080, 1080) if mode == "square" else (1080, 1350)
    img = Image.open(input_path).convert("RGB")

    target_w, target_h = target_size
    img_w, img_h = img.size
    scale = min(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    background = Image.new("RGB", target_size, (255, 255, 255))
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2
    background.paste(img, (offset_x, offset_y))

    background.save(output_path, "JPEG", quality=95)
    logger.info(f"Pillow fallback: resized image to {target_size}")
