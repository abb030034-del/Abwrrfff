# ============================================================
# Group Manager Bot - Rules
# ============================================================

import logging
from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
import db

logger = logging.getLogger(__name__)


async def _is_admin(client, chat_id, user_id) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


def register_rules_handler(app: Client):

    # ==========================================================
    # وضع قوانين (admin, multi-step)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^وضع قوانين$"))
    async def set_rules_start(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")
        await db.set_user_state(
            message.from_user.id, message.chat.id, "set_rules_step1"
        )
        await message.reply_text(
            "📝 أرسل نص القوانين الجديد للمجموعة:\n\nاكتب ( الغاء ) للإلغاء."
        )
        raise StopPropagation

    # ==========================================================
    # القوانين (show)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^القوانين$"))
    async def show_rules(client, message: Message):
        try:
            text = await db.get_rules(message.chat.id)
        except Exception as e:
            logger.error(f"get_rules error: {e}")
            return await message.reply_text(f"❌ حدث خطأ: {e}")

        if not text:
            return await message.reply_text("⚠️ لا توجد قوانين مضافة لهذه المجموعة.")

        title = message.chat.title or "المجموعة"
        await message.reply_text(f"📋 **قوانين {title}:**\n\n{text}")

    # ==========================================================
    # مسح القوانين (admin)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^مسح القوانين$"))
    async def clear_rules(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")

        try:
            existing = await db.get_rules(message.chat.id)
            if not existing:
                return await message.reply_text("⚠️ لا توجد قوانين لمسحها.")
            await db.clear_rules(message.chat.id)
            await message.reply_text("✅ تم مسح قوانين المجموعة.")
        except Exception as e:
            logger.error(f"clear_rules error: {e}")
            await message.reply_text(f"❌ حدث خطأ: {e}")

    # ==========================================================
    # Rules state handler - runs before commands
    # ==========================================================
    @app.on_message(filters.group & ~filters.service, group=-2)
    async def rules_state_handler(client, message: Message):
        if not message.from_user:
            return
        try:
            state_data = await db.get_user_state(
                message.from_user.id, message.chat.id
            )
        except Exception as e:
            logger.error(f"rules state get error: {e}")
            return
        if not state_data:
            return
        if state_data.get("state") != "set_rules_step1":
            return

        text = (message.text or message.caption or "").strip()

        if text == "الغاء":
            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text("✅ تم الإلغاء")
            raise StopPropagation

        if not text:
            await message.reply_text("⚠️ أرسل نص القوانين.")
            raise StopPropagation

        if len(text) > 3000:
            await message.reply_text("⚠️ النص طويل جداً (الحد الأقصى 3000 حرف).")
            raise StopPropagation

        try:
            await db.set_rules(message.chat.id, text)
            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text("✅ تم حفظ قوانين المجموعة بنجاح.")
        except Exception as e:
            logger.error(f"set_rules error: {e}")
            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text(f"❌ فشل حفظ القوانين: {e}")
        raise StopPropagation
