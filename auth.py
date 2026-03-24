"""Telegram user authorization."""
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config import TELEGRAM_USER_ID

logger = logging.getLogger(__name__)

ALLOWED_USER_ID = int(TELEGRAM_USER_ID) if TELEGRAM_USER_ID else None


def authorized_only(func):
    """Decorator to restrict bot access to authorized user only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if ALLOWED_USER_ID is None or user_id != ALLOWED_USER_ID:
            logger.warning(f"Unauthorized access attempt from user_id={user_id}")
            await update.message.reply_text(
                "⛔ אין לך הרשאה להשתמש בבוט הזה."
            )
            return
        return await func(update, context)
    return wrapper
