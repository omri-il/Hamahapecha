"""Gemini AI content reformatter — converts Facebook posts to Instagram format."""
import logging
import google.generativeai as genai
from config import GEMINI_API_KEY, REGISTRATION_FORM_URL

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

SYSTEM_PROMPT = f"""אתה מומחה לשיווק ברשתות חברתיות עבור תוכנית לימודים אקדמית בישראל.
התפקיד שלך: להמיר פוסטים מפייסבוק לפורמט אינסטגרם.

על התוכנית:
- "המהפכה" — תואר שני בחדשנות פדגוגית, מכללת בית ברל
- מובלת על ידי יעקב הכט, מייסד החינוך הדמוקרטי בישראל
- קהל יעד: מורים, אנשי חינוך, יזמים שרוצים לשנות את מערכת החינוך

כללים:
1. כתוב בעברית, שמור על הקול והטון המקורי של הכותב
2. השורה הראשונה חייבת לתפוס תשומת לב (זה מה שנראה בפיד)
3. קצר את הטקסט — מקסימום 2200 תווים (גבול אינסטגרם)
4. הוסף 15-20 האשטגים רלוונטיים בסוף (עברית + אנגלית):
   דוגמאות: #חינוך #מהפכהבחינוך #חדשנותפדגוגית #תוארשני #ביתברל #יעקבהכט #חינוךדמוקרטי #education #pedagogicalinnovation #teachersofinstagram #edtech #israelieducation
5. {"שמור על הלינק לטופס ההרשמה: " + REGISTRATION_FORM_URL if REGISTRATION_FORM_URL else "אם יש קריאה לפעולה (הרשמה, לינק) — שמור עליה"}
6. השתמש באימוג'ים במידה — לא יותר מדי
7. הוסף שורות ריקות בין פסקאות לקריאות נוחה
8. אל תשנה עובדות או ציטוטים מהפוסט המקורי

פלט: רק את טקסט הפוסט לאינסטגרם, בלי הסברים נוספים."""


async def reformat_for_instagram(facebook_text: str) -> str:
    """Take a Facebook post text and reformat it for Instagram."""
    try:
        response = await model.generate_content_async(
            f"{SYSTEM_PROMPT}\n\nפוסט הפייסבוק המקורי:\n\n{facebook_text}"
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise
