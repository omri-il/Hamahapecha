"""Hamahapecha Marketing Bot — repurpose Facebook posts to Instagram."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ConversationHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from config import TELEGRAM_BOT_TOKEN
from auth import authorized_only
from db import init_db, save_post, update_post_published, update_post_status, get_recent_posts
from gemini_helper import reformat_for_instagram
from instagram_api import publish_to_instagram, check_token_valid
from image_handler import download_and_process

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_IMAGE, WAITING_TEXT, PREVIEW = range(3)


# --- Command Handlers ---

@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ברוכים הבאים לבוט השיווק של המהפכה!\n\n"
        "הבוט ממיר פוסטים מפייסבוק לאינסטגרם.\n\n"
        "📌 פקודות:\n"
        "/newpost — פוסט חדש (שלח תמונה + טקסט)\n"
        "/history — פוסטים אחרונים\n"
        "/status — בדיקת חיבור לאינסטגרם\n"
        "/help — עזרה\n"
        "/cancel — ביטול פעולה"
    )


@authorized_only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 איך זה עובד:\n\n"
        "1. שלח /newpost\n"
        "2. שלח תמונה מהפוסט של יעקב\n"
        "3. העתק-הדבק את הטקסט מפייסבוק\n"
        "4. הבוט ימיר את הטקסט לפורמט אינסטגרם עם AI\n"
        "5. תאשר או תבקש גרסה חדשה\n"
        "6. הפוסט יפורסם באינסטגרם! 🎉"
    )


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    valid = check_token_valid()
    if valid:
        await update.message.reply_text("✅ החיבור לאינסטגרם תקין!")
    else:
        await update.message.reply_text(
            "❌ הטוקן של אינסטגרם לא תקין או פג תוקף.\n"
            "צריך לחדש את הטוקן ב-Meta Developer Console."
        )


@authorized_only
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    posts = get_recent_posts(10)
    if not posts:
        await update.message.reply_text("אין פוסטים עדיין. שלח /newpost כדי להתחיל!")
        return

    lines = ["📋 פוסטים אחרונים:\n"]
    for post in posts:
        status_icon = "✅" if post["status"] == "published" else "📝" if post["status"] == "draft" else "❌"
        text_preview = (post["original_text"] or "")[:50]
        date = post["created_at"][:10] if post["created_at"] else "?"
        lines.append(f"{status_icon} [{date}] {text_preview}...")

    await update.message.reply_text("\n".join(lines))


# --- New Post Conversation ---

@authorized_only
async def newpost_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 שלח את התמונה מהפוסט של יעקב בפייסבוק.\n\n"
        "(שלח /cancel לביטול)"
    )
    return WAITING_IMAGE


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("⚠️ אנא שלח תמונה (לא קובץ). נסה שוב:")
        return WAITING_IMAGE

    # Get the largest photo size
    photo = update.message.photo[-1]
    context.user_data["photo_file_id"] = photo.file_id

    await update.message.reply_text(
        "✅ תמונה התקבלה!\n\n"
        "📝 עכשיו העתק-הדבק את הטקסט מהפוסט של יעקב בפייסבוק:"
    )
    return WAITING_TEXT


async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    original_text = update.message.text
    context.user_data["original_text"] = original_text

    await update.message.reply_text("🤖 ממיר את הטקסט לפורמט אינסטגרם...")

    try:
        instagram_text = await reformat_for_instagram(original_text)
    except Exception as e:
        await update.message.reply_text(f"❌ שגיאה ב-AI: {e}\nנסה שוב עם /newpost")
        return ConversationHandler.END

    context.user_data["instagram_text"] = instagram_text

    # Save as draft
    post_id = save_post(original_text, instagram_text, context.user_data.get("photo_file_id", ""))
    context.user_data["post_id"] = post_id

    # Show preview with action buttons
    keyboard = [
        [InlineKeyboardButton("✅ פרסם באינסטגרם", callback_data="publish")],
        [InlineKeyboardButton("🔄 נסה גרסה חדשה", callback_data="regenerate")],
        [InlineKeyboardButton("❌ בטל", callback_data="cancel_post")],
    ]

    await update.message.reply_text(
        f"📱 תצוגה מקדימה לאינסטגרם:\n\n"
        f"{'─' * 30}\n"
        f"{instagram_text}\n"
        f"{'─' * 30}\n\n"
        f"מה לעשות?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PREVIEW


async def handle_preview_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == "publish":
        await query.edit_message_text("⏳ מפרסם באינסטגרם...")

        try:
            # Download and resize image
            local_path, public_url = await download_and_process(
                context.bot,
                context.user_data["photo_file_id"]
            )

            # Publish to Instagram
            ig_post_id = publish_to_instagram(
                public_url,
                context.user_data["instagram_text"]
            )

            # Update DB
            update_post_published(context.user_data["post_id"], ig_post_id)

            await query.edit_message_text(
                f"🎉 הפוסט פורסם בהצלחה באינסטגרם!\n"
                f"Post ID: {ig_post_id}"
            )
        except Exception as e:
            update_post_status(context.user_data["post_id"], "failed")
            await query.edit_message_text(f"❌ שגיאה בפרסום: {e}")

        return ConversationHandler.END

    elif action == "regenerate":
        await query.edit_message_text("🔄 מייצר גרסה חדשה...")

        try:
            instagram_text = await reformat_for_instagram(context.user_data["original_text"])
            context.user_data["instagram_text"] = instagram_text

            keyboard = [
                [InlineKeyboardButton("✅ פרסם באינסטגרם", callback_data="publish")],
                [InlineKeyboardButton("🔄 נסה גרסה חדשה", callback_data="regenerate")],
                [InlineKeyboardButton("❌ בטל", callback_data="cancel_post")],
            ]

            await query.edit_message_text(
                f"📱 תצוגה מקדימה חדשה:\n\n"
                f"{'─' * 30}\n"
                f"{instagram_text}\n"
                f"{'─' * 30}\n\n"
                f"מה לעשות?",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return PREVIEW

        except Exception as e:
            await query.edit_message_text(f"❌ שגיאה ב-AI: {e}")
            return ConversationHandler.END

    elif action == "cancel_post":
        update_post_status(context.user_data["post_id"], "cancelled")
        await query.edit_message_text("🚫 הפוסט בוטל.")
        return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 הפעולה בוטלה.")
    return ConversationHandler.END


# --- Error Handler ---

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")


# --- Main ---

def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return

    init_db()
    logger.info("Starting Hamahapecha bot...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # New post conversation
    newpost_conv = ConversationHandler(
        entry_points=[CommandHandler("newpost", newpost_start)],
        states={
            WAITING_IMAGE: [MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, receive_image)],
            WAITING_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text)],
            PREVIEW: [CallbackQueryHandler(handle_preview_action, pattern="^(publish|regenerate|cancel_post)$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(newpost_conv)
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("history", history_command))
    app.add_error_handler(error_handler)

    logger.info("Bot is running!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
