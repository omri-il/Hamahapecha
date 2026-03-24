import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_USER_ID = os.environ.get("TELEGRAM_USER_ID", "")

# Gemini AI
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Instagram Graph API
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
INSTAGRAM_ACCOUNT_ID = os.environ.get("INSTAGRAM_ACCOUNT_ID", "")

# Image hosting (VPS serves images for IG API to fetch)
IMAGE_HOST_URL = os.environ.get("IMAGE_HOST_URL", "http://147.79.114.195:8090")
IMAGE_DIR = os.environ.get("IMAGE_DIR", "/var/www/hamahapecha/images")

# Registration form URL
REGISTRATION_FORM_URL = os.environ.get("REGISTRATION_FORM_URL", "")
