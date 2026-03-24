# Hamahapecha — Marketing Growth Tool

## About
Marketing automation platform for **"Hamahapecha"** (המהפכה) — a Master's degree program in pedagogical innovation at **Beit Berl College**, Israel.

**Program Head:** Yaakov Hecht
**Marketing Role:** Omri Iram — increase registrations for next year's cohort

## Current Marketing Flow
1. Yaakov posts on his **personal Facebook** — images + ideas about pedagogical innovation
2. Posts include a CTA linking to a **registration form**
3. People fill in their details
4. Yaakov has **1-on-1 conversations** with leads

## Goals
- **Repurpose** Yaakov's Facebook posts → Instagram (new account)
- **Increase conversion rate** of form registrations
- **Analytics** — track post performance, registration funnel
- **Monitor** registration status and lead pipeline

## What's Built

### Telegram Bot (bot.py)
A Telegram bot for repurposing Facebook posts to Instagram. Flow:
1. `/newpost` → send image → paste Facebook text
2. Gemini AI rewrites text for Instagram format (Hebrew, hashtags, emojis)
3. Preview with approve / regenerate / cancel buttons
4. Publishes to Instagram via Graph API

**Commands:** `/start`, `/newpost`, `/history`, `/status`, `/help`, `/cancel`

### Project Files
- `bot.py` — Main Telegram bot with conversation flow
- `config.py` — Environment variables (Telegram, Gemini, Instagram, image hosting)
- `auth.py` — Telegram user authorization
- `db.py` — SQLite database for tracking posts
- `gemini_helper.py` — Gemini 2.5 Flash for text reformatting (FB→IG)
- `image_handler.py` — Nano Banana Pro (gemini-3-pro-image-preview) for image transformation, Pillow fallback
- `instagram_api.py` — Instagram Graph API publishing
- `hamahapecha-bot.service` — systemd service file
- `.env.example` — Required environment variables template

### AI Models Used
- **Text:** `gemini-2.5-flash` — rewrites Facebook posts for Instagram format
- **Image:** `gemini-3-pro-image-preview` (Nano Banana Pro) — intelligently adapts images to Instagram dimensions (4:5 portrait or 1:1 square), falls back to Pillow resize on failure

### Environment Variables (in .env)
- `TELEGRAM_BOT_TOKEN` — Bot token
- `TELEGRAM_USER_ID` — Authorized user ID
- `GEMINI_API_KEY` — Google AI API key
- `INSTAGRAM_ACCESS_TOKEN` — Meta Graph API token
- `INSTAGRAM_ACCOUNT_ID` — Instagram business account ID
- `IMAGE_HOST_URL` — Public URL where VPS serves images (default: http://147.79.114.195:8090)
- `IMAGE_DIR` — Local path for image storage (default: /var/www/hamahapecha/images)
- `REGISTRATION_FORM_URL` — Link to registration form (included in posts)

## Tech Stack
- **Language:** Python 3
- **Bot Framework:** python-telegram-bot 21.9
- **AI:** Google Gemini (google-generativeai + google-genai)
- **Image Processing:** Pillow (fallback)
- **Database:** SQLite
- **Deployment:** systemd service on VPS

## Planned Features (Not Yet Built)
- [ ] Facebook post scraper (from Yaakov's profile/page)
- [ ] Instagram post scheduler (repurpose content)
- [ ] Registration form analytics/monitoring
- [ ] Dashboard for tracking leads and conversions
- [ ] Content calendar / planning tools

## Instagram Setup (In Progress)

### Done
- [x] Facebook Page created: https://www.facebook.com/profile.php?id=100083596033122
- [x] Instagram account exists (needs to be Business/Creator type)

### Next Steps (resume here)
1. **Link Instagram to Facebook Page:** Facebook Page → Settings → Linked Accounts → Instagram → Connect
2. **Meta Developer Console:** Create App → Add Instagram Graph API → Generate Page Access Token with permissions: `instagram_basic`, `instagram_content_publish`, `pages_read_engagement`
3. **Extend token:** Convert short-lived token (1hr) to long-lived token (60 days)
4. **Fill `.env`:** Set `INSTAGRAM_ACCESS_TOKEN` and `INSTAGRAM_ACCOUNT_ID`
5. **Deploy to VPS:** Copy project, install deps, configure systemd service, set up nginx for image hosting on port 8090

## Links
- **GitHub:** https://github.com/omri-il/Hamahapecha
- **Facebook Page:** https://www.facebook.com/profile.php?id=100083596033122
- **Instagram:** TBD (needs to be linked to FB Page)
- **Registration Form:** TBD

## Last Updated
2026-03-24 — Instagram setup in progress: FB Page created, next step is linking IG account + Meta API tokens
