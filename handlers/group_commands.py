# ============================================================
# Group Manager Bot
# Author: LearningBotsOfficial (https://github.com/LearningBotsOfficial) 
# Support: https://t.me/LearningBotsCommunity
# Channel: https://t.me/learning_bots
# YouTube: https://youtube.com/@learning_bots
# License: Open-source (keep credits, no resale)
# ============================================================

from pyrogram import Client, filters
from pyrogram.types import Message, ChatMemberUpdated, ChatPermissions, ChatPrivileges
from pyrogram.enums import ChatMemberStatus
from pyrogram.raw import types
import logging
import db

DEFAULT_WELCOME = "👋 مرحباً {first_name} في {title}!"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)



# ==========================================================
# Global helper
# ==========================================================

async def is_power(client, chat_id: int, user_id) -> bool:
    if user_id is None:
        return False
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


async def extract_target_user(client, message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    text = message.text or message.caption or ""
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return None

    arg = parts[1].strip()

    try:
        if arg.startswith("@"):
            return await client.get_users(arg)
        elif arg.isdigit():
            return await client.get_users(int(arg))
    except Exception:
        return None
    return None


async def handle_welcome(client, chat_id: int, users: list, chat_title: str):
    status = await db.get_welcome_status(chat_id)
    if not status:
        return

    welcome_text = await db.get_welcome_message(chat_id) or DEFAULT_WELCOME

    # Load rules (lazy, may be None)
    try:
        rules_text = await db.get_rules(chat_id)
    except Exception:
        rules_text = None
    rules_block = rules_text if rules_text else ""

    for user in users:
        if not user or getattr(user, "is_bot", False):
            continue
        try:
            text = welcome_text.format(
                username=user.username or user.first_name,
                first_name=user.first_name,
                mention=f"[{user.first_name}](tg://user?id={user.id})",
                title=chat_title,
                القوانين=rules_block,
            )
        except KeyError:
            text = DEFAULT_WELCOME.format(first_name=user.first_name, title=chat_title)

        try:
            await client.send_message(chat_id, text)
        except Exception as e:
            logger.error(f"🚨 فشل إرسال رسالة الترحيب: {e}")




def register_group_commands(app: Client):

    # ==========================================================
    # welcome event
    # ==========================================================
    
    @app.on_chat_member_updated()
    async def member_update(client: Client, cmu: ChatMemberUpdated):
    
        if not cmu.new_chat_member:
            return
    
        user = cmu.new_chat_member.user
        new_status = cmu.new_chat_member.status

        # Skip bots (including ourselves)
        if not user or getattr(user, "is_bot", False):
            return
    
        if new_status == ChatMemberStatus.MEMBER:
    
            await handle_welcome(
                client,
                cmu.chat.id,
                [user],
                cmu.chat.title,
            )
    
    
    # ==========================================================
    # welcome toggle
    # ==========================================================
    
    @app.on_message(filters.group & filters.regex(r"^ترحيب"))
    async def welcome_toggle(client, message: Message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف أو المالك يمكنه استخدام هذا الأمر.")
    
        parts = (message.text or message.caption or "").split(maxsplit=1)
        if len(parts) < 2 or parts[1].lower() not in ["on", "off"]:
            return await message.reply_text("⚙️ الاستخدام: /welcome on/off")
    
        status = parts[1].lower() == "on"
        await db.set_welcome_status(message.chat.id, status)
    
        await message.reply_text(
            "✅ رسائل الترحيب مفعّلة." if status else "⚠️ رسائل الترحيب معطّلة."
        )
    
    
    # ==========================================================
    # set welcome
    # ========================================================== 
    
    @app.on_message(filters.group & filters.regex(r"^تعيين_ترحيب"))
    async def set_welcome(client, message: Message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("⚠️ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        parts = (message.text or message.caption or "").split(maxsplit=1)
        if len(parts) < 2:
            return await message.reply_text("🤖 الاستخدام: /setwelcome <رسالة>")
    
        await db.set_welcome_message(message.chat.id, parts[1])
        await message.reply_text("✅ تم حفظ رسالة الترحيب المخصصة!")
    
    
    # ==========================================================
    # lock
    # ==========================================================
    
    @app.on_message(filters.group & filters.regex(r"^قفل"))
    async def lock_command(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        parts = (message.text or message.caption or "").split(maxsplit=1)
        if len(parts) < 2:
            return await message.reply_text("⚙️ الاستخدام: /lock <نوع>")
    
        lock_type = parts[1].lower()
        valid = ["url", "sticker", "media", "username", "forward"]
    
        if lock_type not in valid:
            return await message.reply_text(f"⚠️ الأنواع المتاحة: {', '.join(valid)}")
    
        await db.set_lock(message.chat.id, lock_type, True)
        await message.reply_text(f"🔒 تم قفل {lock_type}!")
    
    
    # ==========================================================
    # unlock
    # ==========================================================
    
    @app.on_message(filters.group & filters.regex(r"^فتح"))
    async def unlock_command(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        parts = (message.text or message.caption or "").split(maxsplit=1)
        if len(parts) < 2:
            return await message.reply_text("⚙️ الاستخدام: /unlock <نوع>")
    
        lock_type = parts[1].lower()
        valid = ["url", "sticker", "media", "username", "forward"]
    
        if lock_type not in valid:
            return await message.reply_text(f"⚠️ الأنواع المتاحة: {', '.join(valid)}")
    
        await db.set_lock(message.chat.id, lock_type, False)
        await message.reply_text(f"🔓 تم فتح {lock_type}!")
    
    
    # ==========================================================
    # locks list
    # ==========================================================
    
    @app.on_message(filters.group & filters.regex(r"^الاقفال"))
    async def locks_list(client, message):
        locks = await db.get_locks(message.chat.id)
        if not locks:
            return await message.reply_text("🤖 لا توجد أقفال نشطة.")
    
        text = "🔐 **الأقفال:**\n\n"
        for k, v in locks.items():
            text += f"• {k}: {'✅' if v else '❌'}\n"
    
        await message.reply_text(text)
    
    
    # ==========================================================
    # enforce lock
    # ==========================================================
    
    @app.on_message(filters.group & ~filters.service, group=1)
    async def enforce_locks(client, message):
        if not message.from_user:
            return
        try:
            member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return
        except:
            return
    
        locks = await db.get_locks(message.chat.id)
        if not locks:
            return
    
        if locks.get("url") and message.text:
            if message.entities:
                for ent in message.entities:
                    if ent.type in ["url", "text_link"]:
                        return await message.delete()
            if "t.me/" in message.text.lower():
                return await message.delete()
    
        if locks.get("sticker") and message.sticker:
            return await message.delete()
    
        if locks.get("media") and (message.photo or message.video or message.document):
            return await message.delete()
    
        if locks.get("username") and message.text and "@" in message.text:
            return await message.delete()
    
        if locks.get("forward") and message.forward_from:
            return await message.delete()
    
    
    # ==========================================================
    # kick
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^طرد"))
    async def kick_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/kick @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تنفيذ هذا الإجراء على المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك طرد نفسك.")
    
        try:
            await client.ban_chat_member(message.chat.id, user.id)
            await client.unban_chat_member(message.chat.id, user.id)
            await message.reply_text(f"👢 تم طرد {user.mention}.")
        except Exception as e:
            await message.reply_text(f"❌ فشل الطرد: {e}")
    
    
    # ==========================================================
    # ban
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^حظر"))
    async def ban_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/ban @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تنفيذ هذا الإجراء على المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك حظر نفسك.")
    
        try:
            await client.ban_chat_member(message.chat.id, user.id)
            await message.reply_text(f"🚨 تم حظر {user.mention}.")
        except Exception as e:
            await message.reply_text(f"❌ فشل الحظر: {e}")
    
    
    # ==========================================================
    # unban
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^رفع_حظر"))
    async def unban_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/unban @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تنفيذ هذا الإجراء على المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك رفع حظر نفسك.")
    
        try:
            await client.unban_chat_member(message.chat.id, user.id)
            await message.reply_text(f"✅ تم رفع حظر {user.mention}.")
        except Exception as e:
            await message.reply_text(f"❌ فشل رفع الحظر: {e}")
    
    
    # ==========================================================
    # mute
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^كتم"))
    async def mute_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/mute @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تنفيذ هذا الإجراء على المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك كتم نفسك.")
    
        try:
            await client.restrict_chat_member(
                message.chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await message.reply_text(f"🔇 تم كتم {user.mention}.")
        except Exception as e:
            await message.reply_text(f"❌ فشل الكتم: {e}")
    
    
    # ==========================================================
    # unmute
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^رفع_كتم"))
    async def unmute_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/unmute @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تنفيذ هذا الإجراء على المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك رفع كتم نفسك.")
    
        try:
            await client.restrict_chat_member(
                message.chat.id,
                user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                ),
            )
            await message.reply_text(f"🔊 تم رفع كتم {user.mention}.")
        except Exception as e:
            await message.reply_text(f"❌ فشل رفع الكتم: {e}")
    
    
    # ==========================================================
    # warn
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^تحذير"))
    async def warn_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/warn @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن تحذير المشرفين.")
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك تحذير نفسك.")
    
        warns = await db.add_warn(message.chat.id, user.id)
        if warns >= 3:
            await client.restrict_chat_member(
                message.chat.id,
                user.id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            await message.reply_text(f"🚫 وصل {user.mention} إلى 3 تحذيرات وتم كتمه.")
        else:
            await message.reply_text(f"⚠️ لدى {user.mention} الآن {warns}/3 تحذيرات.")
    
    
    # ==========================================================
    # warns
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^التحذيرات"))
    async def warns_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/warns @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن عرض تحذيرات المشرفين.")
    
        warns = await db.get_warns(message.chat.id, user.id)
        await message.reply_text(f"⚠️ لدى {user.mention} {warns}/3 تحذيرات.")
    
    
    # ==========================================================
    # resetwarns
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^مسح_تحذيرات"))
    async def resetwarns_user(client, message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب `/resetwarns @username`")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
        if target_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await message.reply_text("⚠️ لا يمكن إعادة تعيين تحذيرات المشرفين.")
    
        await db.reset_warns(message.chat.id, user.id)
        await message.reply_text(f"✅ تم مسح تحذيرات {user.mention}.")
          
    
          
    # ==========================================================
    # Promote Command
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^ترقية"))
    async def promote_user(client: Client, message: Message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف أو المالك يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب '/ترقية @username'")
    
        target_member = await client.get_chat_member(message.chat.id, user.id)
    
        if target_member.status == ChatMemberStatus.OWNER:
            return await message.reply_text("⚠️ لا يمكن ترقية مالك المجموعة.")
    
        if user.id == message.from_user.id:
            return await message.reply_text("⚠️ لا يمكنك ترقية نفسك.")
    
        try:
            privileges = ChatPrivileges(
                can_manage_chat=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=False,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True,
                can_post_messages=False,
                can_edit_messages=False,
                is_anonymous=False
            )
    
            await client.promote_chat_member(
                chat_id=message.chat.id,
                user_id=user.id,
                privileges=privileges
            )
            await message.reply_text(f"✅ تمت ترقية {user.mention} إلى مشرف.")
    
        except Exception as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                await message.reply_text("⚠️ لا يمكن الترقية: المستخدم ليس عضواً في هذه المجموعة.")
            elif "CHAT_ADMIN_REQUIRED" in str(e):
                await message.reply_text("⚠️ يجب أن يكون البوت مشرفاً بصلاحية 'إضافة مشرفين' للترقية.")
            else:
                await message.reply_text(f"❌ فشلت الترقية: {e}")
        
        
    # ==========================================================
    # Demote Command
    # ==========================================================
    @app.on_message(filters.group & filters.regex(r"^تخفيض"))
    async def demote_user(client: Client, message: Message):
        if not message.from_user or not await is_power(client, message.chat.id, message.from_user.id):
            return await message.reply_text("❌ فقط المشرف يمكنه استخدام هذا الأمر.")
    
        user = await extract_target_user(client, message)
        if not user:
            return await message.reply_text("⚠️ الاستخدام: رد على مستخدم أو اكتب '/تخفيض @username'")
    
        try:
            target_member = await client.get_chat_member(message.chat.id, user.id)
        except Exception as e:
            if "USER_NOT_PARTICIPANT" in str(e):
                return await message.reply_text("❌ لا يمكن التخفيض: المستخدم ليس عضواً في هذه المجموعة.")
            return await message.reply_text(f"⚠️ فشل التخفيض: {e}")
    
        if target_member.status == ChatMemberStatus.OWNER:
            return await message.reply_text("⚠️ لا يمكنك تخفيض مالك المجموعة.")
    
        if target_member.status not in [ChatMemberStatus.ADMINISTRATOR]:
            return await message.reply_text("⚠️ المستخدم ليس مشرفاً.")
    
        if user.id == message.from_user.id:
            return await message.reply_text("❌ لا يمكنك تخفيض نفسك.")
    
        try:
            no_privileges = ChatPrivileges(
                can_manage_chat=False,
                can_delete_messages=False,
                can_manage_video_chats=False,
                can_restrict_members=False,
                can_promote_members=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_post_messages=False,
                can_edit_messages=False,
                is_anonymous=False
            )
    
            await client.promote_chat_member(
                chat_id=message.chat.id,
                user_id=user.id,
                privileges=no_privileges
            )
            await message.reply_text(f"✅ تم تخفيض {user.mention} من المشرفين.")
    
        except Exception as e:
            if "CHAT_ADMIN_REQUIRED" in str(e):
                await message.reply_text("❌ يجب أن يكون البوت مشرفاً بصلاحية 'إضافة مشرفين' للتخفيض.")
            else:
                await message.reply_text(f"⚠️ فشل التخفيض: {e}")
