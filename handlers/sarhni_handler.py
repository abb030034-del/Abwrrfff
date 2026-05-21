# ============================================================
# Group Manager Bot - Sarhni (Anonymous Honesty) Handler
# ============================================================

import re
import time
import random
import string
import logging
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

logger = logging.getLogger(__name__)

# {link_id: {'target_id', 'target_name', 'target_mention', 'time'}}
sarhni_links = {}
# {sender_user_id: {'target_id', 'target_name', 'time'}}
sarhni_sessions = {}

LINK_TTL = 7 * 86400   # 7 days
SESSION_TTL = 30 * 60  # 30 minutes


def _gen_id(n=10):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _cleanup():
    now = time.time()
    for k in [k for k, v in sarhni_links.items() if now - v["time"] > LINK_TTL]:
        sarhni_links.pop(k, None)
    for k in [k for k, v in sarhni_sessions.items() if now - v["time"] > SESSION_TTL]:
        sarhni_sessions.pop(k, None)


def register_sarhni_handler(app: Client):

    # ==========================================================
    # In group: صارحني → creates a sarhni link button
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^صارحني$"))
    async def sarhni_group(client, message: Message):
        _cleanup()
        if not message.from_user:
            return

        target_user = message.from_user
        # If reply, target is the replied-to user
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user

        if target_user.is_bot:
            return await message.reply_text("⚠️ لا يمكن إرسال صراحة لبوت.")

        link_id = _gen_id()
        sarhni_links[link_id] = {
            "target_id": target_user.id,
            "target_name": target_user.first_name or "مستخدم",
            "time": time.time(),
        }

        try:
            me = await client.get_me()
            bot_username = me.username
        except Exception:
            from config import BOT_USERNAME

            bot_username = BOT_USERNAME

        link = f"https://t.me/{bot_username}?start=sarhni{link_id}"
        buttons = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✉️ صارحه الآن", url=link)]]
        )
        await message.reply_text(
            f"🤫 **صراحة!**\nاضغط الزر بالأسفل لإرسال رسالة سرية إلى "
            f"[{target_user.first_name}](tg://user?id={target_user.id})",
            reply_markup=buttons,
            disable_web_page_preview=True,
        )

    # ==========================================================
    # Intercept /start sarhni<ID> in private (group=-1 so it runs first)
    # ==========================================================
    @app.on_message(
        filters.private & filters.command("start"),
        group=-1,
    )
    async def sarhni_start_intercept(client, message: Message):
        _cleanup()
        if not message.from_user:
            return
        if not message.command or len(message.command) < 2:
            return  # Let default start handle it

        arg = message.command[1]
        if not arg.startswith("sarhni"):
            return  # Not a sarhni payload, let default start handle it

        link_id = arg[len("sarhni"):]
        data = sarhni_links.get(link_id)
        if not data:
            await message.reply_text(
                "⚠️ هذا الرابط منتهي أو غير صالح."
            )
            raise StopPropagation

        if message.from_user.id == data["target_id"]:
            await message.reply_text(
                "⚠️ لا يمكنك إرسال صراحة لنفسك."
            )
            raise StopPropagation

        sarhni_sessions[message.from_user.id] = {
            "target_id": data["target_id"],
            "target_name": data["target_name"],
            "time": time.time(),
        }

        await message.reply_text(
            f"🤫 **صراحة إلى {data['target_name']}**\n\n"
            f"أرسل الآن رسالتك السرية وسأقوم بإيصالها له بدون كشف هويتك.\n\n"
            f"اكتب ( الغاء ) للإلغاء."
        )
        raise StopPropagation

    # ==========================================================
    # Private message handler for active sarhni session (group=-1)
    # ==========================================================
    @app.on_message(
        filters.private & ~filters.service & ~filters.command(["start"]),
        group=-1,
    )
    async def sarhni_session_handler(client, message: Message):
        _cleanup()
        if not message.from_user:
            return
        session = sarhni_sessions.get(message.from_user.id)
        if not session:
            return  # No active session, let other handlers process

        text = (message.text or message.caption or "").strip()

        if text == "الغاء":
            sarhni_sessions.pop(message.from_user.id, None)
            await message.reply_text("✅ تم إلغاء الصراحة.")
            raise StopPropagation

        if not message.text:
            await message.reply_text(
                "⚠️ أرسل الرسالة بشكل نصي فقط.\nاكتب ( الغاء ) للإلغاء."
            )
            raise StopPropagation

        if len(text) > 2000:
            await message.reply_text("⚠️ الرسالة طويلة جداً (الحد 2000 حرف).")
            raise StopPropagation

        try:
            await client.send_message(
                session["target_id"],
                f"🤫 **وصلتك صراحة جديدة:**\n\n{text}",
            )
            await message.reply_text("✅ تم إرسال صراحتك بنجاح بدون كشف هويتك!")
        except Exception as e:
            logger.error(f"sarhni send error: {e}")
            await message.reply_text(
                "❌ تعذّر إرسال الصراحة. ربما لم يبدأ المستخدم محادثة مع البوت."
            )
        finally:
            sarhni_sessions.pop(message.from_user.id, None)

        raise StopPropagation
