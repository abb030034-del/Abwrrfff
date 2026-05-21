# ============================================================
# Group Manager Bot - Custom Filters (Replies)
# ============================================================

from pyrogram import Client, filters, StopPropagation
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
import db
import logging

logger = logging.getLogger(__name__)


async def _is_admin(client, chat_id, user_id) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


def register_filters_handler(app: Client):

    # ==========================================================
    # اضف رد - start (step 1)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^اضف رد$"))
    async def add_filter_start(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")
        await db.set_user_state(
            message.from_user.id, message.chat.id, "add_filter_step1"
        )
        await message.reply_text("📝 تمام، أرسل الكلمة اللي تبي الرد عليها:\n\nاكتب ( الغاء ) للإلغاء.")
        raise StopPropagation

    # ==========================================================
    # مسح رد - start
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^مسح رد$"))
    async def del_filter_start(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")
        filters_list = await db.get_all_filters(message.chat.id)
        if not filters_list:
            return await message.reply_text("⚠️ مافيه ردود مضافة")
        await db.set_user_state(
            message.from_user.id, message.chat.id, "del_filter_step1"
        )
        await message.reply_text("📝 أرسل الكلمة اللي تبي تمسح ردها:\n\nاكتب ( الغاء ) للإلغاء.")
        raise StopPropagation

    # ==========================================================
    # عرض الردود
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^الردود$"))
    async def list_filters(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")
        filters_list = await db.get_all_filters(message.chat.id)
        if not filters_list:
            return await message.reply_text("⚠️ مافيه ردود مضافة")
        txt = "📋 الردود المضافة:\n\n"
        for i, f in enumerate(filters_list, 1):
            txt += f"{i}. {f['keyword']} ← ({f['type']})\n"
        await message.reply_text(txt)

    # ==========================================================
    # مسح الردود (all)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^مسح الردود$"))
    async def clear_filters(client, message: Message):
        if not message.from_user:
            return
        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ هذا الأمر يخص المشرف وفوق بس")
        await db.delete_all_filters(message.chat.id)
        await message.reply_text("✅ تم مسح جميع الردود")

    # ==========================================================
    # State handler (multi-step add/delete) - runs before commands
    # ==========================================================
    @app.on_message(filters.group & ~filters.service, group=-3)
    async def filter_state_handler(client, message: Message):
        if not message.from_user:
            return
        try:
            state_data = await db.get_user_state(message.from_user.id, message.chat.id)
        except Exception as e:
            logger.error(f"get_user_state error: {e}")
            return
        if not state_data:
            return

        state = state_data.get("state")
        # Only handle filter-related states here
        if state not in ("add_filter_step1", "add_filter_step2", "del_filter_step1"):
            return

        text = (message.text or message.caption or "").strip()

        # Allow cancel
        if text == "الغاء":
            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text("✅ تم الإلغاء")
            raise StopPropagation

        # Step 1: receive the keyword
        if state == "add_filter_step1":
            if not text:
                await message.reply_text("⚠️ أرسل الكلمة المفتاحية بشكل نصي.")
                raise StopPropagation
            if len(text) > 100:
                await message.reply_text("⚠️ الكلمة طويلة جداً، اكتب أقل من 100 حرف")
                raise StopPropagation
            await db.set_user_state(
                message.from_user.id,
                message.chat.id,
                "add_filter_step2",
                extra=text.lower(),
            )
            await message.reply_text(
                f"✅ الكلمة: **{text}**\n\nالآن أرسل الرد (نص، صورة، فيديو، ستيكر، صوت، ملف):\n\nاكتب ( الغاء ) للإلغاء."
            )
            raise StopPropagation

        # Step 2: receive the response content
        if state == "add_filter_step2":
            keyword = state_data.get("extra")
            if not keyword:
                await db.clear_user_state(message.from_user.id, message.chat.id)
                await message.reply_text("⚠️ حدث خطأ، حاول مرة أخرى")
                raise StopPropagation

            try:
                if message.photo:
                    caption = message.caption or None
                    await db.add_filter(
                        message.chat.id, keyword, "photo", message.photo.file_id, caption
                    )
                elif message.video:
                    caption = message.caption or None
                    await db.add_filter(
                        message.chat.id, keyword, "video", message.video.file_id, caption
                    )
                elif message.sticker:
                    await db.add_filter(
                        message.chat.id, keyword, "sticker", message.sticker.file_id
                    )
                elif message.audio:
                    caption = message.caption or None
                    await db.add_filter(
                        message.chat.id, keyword, "audio", message.audio.file_id, caption
                    )
                elif message.animation:
                    caption = message.caption or None
                    await db.add_filter(
                        message.chat.id, keyword, "animation", message.animation.file_id, caption
                    )
                elif message.document:
                    caption = message.caption or None
                    await db.add_filter(
                        message.chat.id, keyword, "document", message.document.file_id, caption
                    )
                elif message.voice:
                    await db.add_filter(
                        message.chat.id, keyword, "voice", message.voice.file_id
                    )
                elif message.text:
                    await db.add_filter(message.chat.id, keyword, "text", message.text)
                else:
                    await message.reply_text(
                        "⚠️ نوع الرد غير مدعوم. أرسل نص أو صورة أو فيديو أو ستيكر أو صوت أو ملف."
                    )
                    raise StopPropagation
            except StopPropagation:
                raise
            except Exception as e:
                logger.error(f"add_filter error: {e}")
                await db.clear_user_state(message.from_user.id, message.chat.id)
                await message.reply_text(f"❌ فشل حفظ الرد: {e}")
                raise StopPropagation

            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text(f"✅ تم إضافة الرد على ( {keyword} ) بنجاح!")
            raise StopPropagation

        # Delete filter: receive keyword
        if state == "del_filter_step1":
            if not text:
                await message.reply_text("⚠️ أرسل الكلمة بشكل نصي.")
                raise StopPropagation
            key = text.lower()
            existing = await db.get_filter(message.chat.id, key)
            if not existing:
                await db.clear_user_state(message.from_user.id, message.chat.id)
                await message.reply_text(f"⚠️ الكلمة ( {text} ) مو مضافة في الردود")
                raise StopPropagation
            await db.delete_filter(message.chat.id, key)
            await db.clear_user_state(message.from_user.id, message.chat.id)
            await message.reply_text(f"✅ تم مسح رد ( {text} ) بنجاح!")
            raise StopPropagation

    # ==========================================================
    # Auto-trigger filters
    # ==========================================================
    @app.on_message(filters.group & filters.text & ~filters.service, group=10)
    async def trigger_filters(client, message: Message):
        if not message.from_user:
            return
        if not message.text:
            return

        # Skip when user is in an active filter-state to avoid double handling
        try:
            state_data = await db.get_user_state(
                message.from_user.id, message.chat.id
            )
            if state_data and state_data.get("state") in (
                "add_filter_step1",
                "add_filter_step2",
                "del_filter_step1",
                "set_rules_step1",
            ):
                return
        except Exception:
            pass

        text = message.text.strip().lower()
        if not text:
            return

        try:
            filter_data = await db.get_filter(message.chat.id, text)
        except Exception as e:
            logger.error(f"get_filter error: {e}")
            return

        if not filter_data:
            # Substring match against any saved keyword
            try:
                all_filters = await db.get_all_filters(message.chat.id)
            except Exception:
                return
            for f in all_filters:
                kw = (f.get("keyword") or "").lower()
                if kw and kw in text:
                    filter_data = f
                    break

        if not filter_data:
            return

        ftype = filter_data.get("type")
        content = filter_data.get("content")
        caption = filter_data.get("caption")

        try:
            if ftype == "text":
                await message.reply_text(content)
            elif ftype == "photo":
                await message.reply_photo(content, caption=caption)
            elif ftype == "video":
                await message.reply_video(content, caption=caption)
            elif ftype == "sticker":
                await message.reply_sticker(content)
            elif ftype == "audio":
                await message.reply_audio(content, caption=caption)
            elif ftype == "document":
                await message.reply_document(content, caption=caption)
            elif ftype == "animation":
                await message.reply_animation(content, caption=caption)
            elif ftype == "voice":
                await message.reply_voice(content)
        except Exception as e:
            logger.error(f"trigger_filters reply error: {e}")
