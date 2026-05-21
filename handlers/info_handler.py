# ============================================================
# Group Manager Bot - Info Commands
# ============================================================

import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message

logger = logging.getLogger(__name__)


def _format_account_type(user) -> str:
    if not user:
        return "غير معروف"
    if getattr(user, "is_bot", False):
        return "بوت 🤖"
    if getattr(user, "is_premium", False):
        return "بريميوم ⭐"
    if getattr(user, "is_scam", False):
        return "محتال ⚠️"
    if getattr(user, "is_fake", False):
        return "مزيف ⚠️"
    if getattr(user, "is_verified", False):
        return "موثّق ✔️"
    return "عادي 👤"


def register_info_handler(app: Client):

    # ==========================================================
    # آيدي / ايدي / id
    # ==========================================================
    @app.on_message(filters.regex(r"^(آيدي|ايدي|id)$", flags=re.IGNORECASE))
    async def id_command(client, message: Message):
        if not message.from_user:
            return

        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user
            txt = "🆔 معلومات المستخدم:\n\n"
            txt += f"• الاسم: {target.first_name or '-'}\n"
            if target.username:
                txt += f"• اليوزر: @{target.username}\n"
            txt += f"• الآيدي: `{target.id}`\n"
            await message.reply_text(txt)
            return

        # No reply: show sender + chat info
        sender = message.from_user
        txt = f"🆔 معلوماتك:\n\n"
        txt += f"• الاسم: {sender.first_name or '-'}\n"
        if sender.username:
            txt += f"• اليوزر: @{sender.username}\n"
        txt += f"• آيديك: `{sender.id}`\n"
        if message.chat and message.chat.type.value != "private":
            txt += f"\n💬 معلومات المحادثة:\n"
            if message.chat.title:
                txt += f"• الاسم: {message.chat.title}\n"
            txt += f"• آيدي المحادثة: `{message.chat.id}`\n"
        await message.reply_text(txt)

    # ==========================================================
    # معلوماتي
    # ==========================================================
    @app.on_message(filters.regex(r"^معلوماتي$"))
    async def my_info(client, message: Message):
        if not message.from_user:
            return
        user = message.from_user
        txt = "👤 **معلوماتك:**\n\n"
        txt += f"• الاسم: {user.first_name or '-'}\n"
        if user.last_name:
            txt += f"• اسم العائلة: {user.last_name}\n"
        if user.username:
            txt += f"• اليوزر: @{user.username}\n"
        else:
            txt += "• اليوزر: لا يوجد\n"
        txt += f"• الآيدي: `{user.id}`\n"
        txt += f"• نوع الحساب: {_format_account_type(user)}\n"
        if user.language_code:
            txt += f"• لغة الجهاز: {user.language_code}\n"
        await message.reply_text(txt)

    # ==========================================================
    # معلومات (with reply)
    # ==========================================================
    @app.on_message(filters.regex(r"^معلومات$"))
    async def user_info(client, message: Message):
        if not message.from_user:
            return

        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text(
                "⚠️ رد على مستخدم لعرض معلوماته.\nأو اكتب ( معلوماتي ) لمعلوماتك."
            )

        user = message.reply_to_message.from_user
        txt = "👤 **معلومات المستخدم:**\n\n"
        txt += f"• الاسم: {user.first_name or '-'}\n"
        if user.last_name:
            txt += f"• اسم العائلة: {user.last_name}\n"
        if user.username:
            txt += f"• اليوزر: @{user.username}\n"
        else:
            txt += "• اليوزر: لا يوجد\n"
        txt += f"• الآيدي: `{user.id}`\n"
        txt += f"• نوع الحساب: {_format_account_type(user)}\n"
        if user.language_code:
            txt += f"• لغة الجهاز: {user.language_code}\n"
        await message.reply_text(txt)
