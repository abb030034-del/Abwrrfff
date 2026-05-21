# ============================================================
# Group Manager Bot - Whisper Inline Handler
# ============================================================

import re
import time
import random
import string
import logging
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

logger = logging.getLogger(__name__)

# In-memory whisper store: { whisper_id: {sender_id, sender_name, target, text, time} }
# target: lowercase username string ('ahmed') or 'all'
whispers_store = {}

WHISPER_TTL = 86400  # 24 hours


def _generate_whisper_id():
    return "".join(random.choices(string.ascii_letters + string.digits, k=10))


def _cleanup_whispers():
    """Remove whispers older than WHISPER_TTL seconds."""
    now = time.time()
    expired = [k for k, v in whispers_store.items() if now - v["time"] > WHISPER_TTL]
    for k in expired:
        whispers_store.pop(k, None)


def _parse_whisper(query: str):
    """Return (message_text, target_username_lower) or (None, None) if invalid."""
    if not query:
        return None, None
    q = query.strip()

    # Target at the end: "message @username"
    m = re.search(r"(.+?)\s+@(\w+)\s*$", q)
    if m:
        text = m.group(1).strip()
        target = m.group(2).lower()
        if text:
            return text, target

    # Target at the start: "@username message"
    m = re.match(r"^@(\w+)\s+(.+)$", q)
    if m:
        target = m.group(1).lower()
        text = m.group(2).strip()
        if text:
            return text, target

    return None, None


def register_whisper_handler(app: Client):

    # ==========================================================
    # Inline query
    # ==========================================================
    @app.on_inline_query()
    async def inline_handler(client, inline_query: InlineQuery):
        _cleanup_whispers()
        query = inline_query.query or ""
        text, target = _parse_whisper(query)

        if not text or not target:
            # Helpful usage hint
            return await inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        title="🤫 الهمسة",
                        description="اكتب: رسالتك @username  (أو @all للجميع)",
                        input_message_content=InputTextMessageContent(
                            "🤫 صيغة الهمسة:\n`<رسالة> @username`\nمثال: `سر صغير @ahmed`"
                        ),
                    )
                ],
                cache_time=1,
                is_personal=True,
            )

        # Build whisper
        whisper_id = _generate_whisper_id()
        sender = inline_query.from_user
        sender_id = sender.id if sender else 0
        sender_name = (sender.first_name if sender else None) or "مجهول"

        whispers_store[whisper_id] = {
            "sender_id": sender_id,
            "sender_name": sender_name,
            "target": target,  # 'all' or lowercase username
            "text": text,
            "time": time.time(),
        }

        target_display = "الجميع" if target == "all" else f"@{target}"

        result_text = (
            f"🤫 **همسة من** [{sender_name}](tg://user?id={sender_id})\n"
            f"📩 **إلى:** {target_display}\n\n"
            f"اضغط الزر بالأسفل لعرض الهمسة (للمستلم فقط)."
        )

        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("👁 عرض الهمسة", callback_data=f"whisper:{whisper_id}")]]
        )

        try:
            await inline_query.answer(
                results=[
                    InlineQueryResultArticle(
                        title=f"🤫 إرسال همسة إلى {target_display}",
                        description=f"اضغط لإرسال الهمسة (يراها فقط {target_display})",
                        input_message_content=InputTextMessageContent(
                            result_text, disable_web_page_preview=True
                        ),
                        reply_markup=buttons,
                    )
                ],
                cache_time=1,
                is_personal=True,
            )
        except Exception as e:
            logger.error(f"inline whisper answer error: {e}")

    # ==========================================================
    # Callback query for viewing the whisper
    # ==========================================================
    @app.on_callback_query(filters.regex(r"^whisper:(.+)$"))
    async def whisper_callback(client, callback_query: CallbackQuery):
        _cleanup_whispers()
        try:
            whisper_id = callback_query.matches[0].group(1)
        except Exception:
            return await callback_query.answer("❌ خطأ في الهمسة.", show_alert=True)

        data = whispers_store.get(whisper_id)
        if not data:
            return await callback_query.answer(
                "⚠️ هذه الهمسة منتهية أو غير موجودة.", show_alert=True
            )

        user = callback_query.from_user
        if not user:
            return await callback_query.answer("⚠️ غير معروف.", show_alert=True)

        target = data["target"]
        user_username = (user.username or "").lower()

        is_allowed = (
            target == "all"
            or user.id == data["sender_id"]
            or (user_username and user_username == target)
        )

        if not is_allowed:
            return await callback_query.answer(
                "🚫 هذه الهمسة ليست لك.", show_alert=True
            )

        # Show the whisper text in alert
        await callback_query.answer(data["text"], show_alert=True)
