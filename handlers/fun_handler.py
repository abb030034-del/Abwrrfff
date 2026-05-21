# ============================================================
# Group Manager Bot - Fun Lists
# ============================================================

import re
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus
import db

logger = logging.getLogger(__name__)


# All 13 fun lists
FUN_LISTS = [
    {
        "db_key": "cake",
        "emoji": "🍰",
        "plural_label": "الكيك",
        "singular_variants": ["كيك", "كيكه", "كيكة"],
        "plural_variants": ["الكيك"],
    },
    {
        "db_key": "honey",
        "emoji": "🍯",
        "plural_label": "العسل",
        "singular_variants": ["عسل"],
        "plural_variants": ["العسل"],
    },
    {
        "db_key": "scammer",
        "emoji": "💩",
        "plural_label": "النصابين",
        "singular_variants": ["نصاب"],
        "plural_variants": ["النصابين"],
    },
    {
        "db_key": "donkey",
        "emoji": "🦓",
        "plural_label": "الحمير",
        "singular_variants": ["حمار"],
        "plural_variants": ["الحمير"],
    },
    {
        "db_key": "cow",
        "emoji": "🐄",
        "plural_label": "البقر",
        "singular_variants": ["بقرة", "بقره"],
        "plural_variants": ["البقر"],
    },
    {
        "db_key": "dog",
        "emoji": "🐩",
        "plural_label": "الكلاب",
        "singular_variants": ["كلب"],
        "plural_variants": ["الكلاب"],
    },
    {
        "db_key": "monkey",
        "emoji": "🐒",
        "plural_label": "القرود",
        "singular_variants": ["قرد"],
        "plural_variants": ["القرود"],
    },
    {
        "db_key": "goat",
        "emoji": "🐐",
        "plural_label": "التيوس",
        "singular_variants": ["تيس"],
        "plural_variants": ["التيوس"],
    },
    {
        "db_key": "bull",
        "emoji": "🐂",
        "plural_label": "الثور",
        "singular_variants": ["ثور"],
        "plural_variants": ["الثور", "الثيران"],
    },
    {
        "db_key": "chicken",
        "emoji": "🐓",
        "plural_label": "الدجاج",
        "singular_variants": ["دجاجة", "دجاجه"],
        "plural_variants": ["الدجاج"],
    },
    {
        "db_key": "queen",
        "emoji": "👑",
        "plural_label": "الملكات",
        "singular_variants": ["ملكة", "ملكه"],
        "plural_variants": ["الملكات"],
    },
    {
        "db_key": "hunter",
        "emoji": "🔫",
        "plural_label": "الصيادين",
        "singular_variants": ["صياد"],
        "plural_variants": ["الصيادين"],
    },
    {
        "db_key": "sheep",
        "emoji": "🐏",
        "plural_label": "الخرفان",
        "singular_variants": ["خروف"],
        "plural_variants": ["الخرفان"],
    },
]


def _all_singular():
    seen = []
    for L in FUN_LISTS:
        for v in L["singular_variants"]:
            if v not in seen:
                seen.append(v)
    return sorted(seen, key=len, reverse=True)


def _all_plural():
    seen = []
    for L in FUN_LISTS:
        for v in L["plural_variants"]:
            if v not in seen:
                seen.append(v)
    return sorted(seen, key=len, reverse=True)


_SINGULAR_ALT = "|".join(re.escape(w) for w in _all_singular())
_PLURAL_ALT = "|".join(re.escape(w) for w in _all_plural())

ADD_REGEX = r"^رفع (" + _SINGULAR_ALT + r")\s*$"
REMOVE_REGEX = r"^تنزيل (" + _SINGULAR_ALT + r")\s*$"
SHOW_REGEX = r"^قائم[ةه]\s+(" + _PLURAL_ALT + r")\s*$"
CLEAR_REGEX = r"^مسح قائم[ةه]\s+(" + _PLURAL_ALT + r")\s*$"


def _find_by_singular(word):
    word = word.strip()
    for L in FUN_LISTS:
        if word in L["singular_variants"]:
            return L
    return None


def _find_by_plural(word):
    word = word.strip()
    for L in FUN_LISTS:
        if word in L["plural_variants"]:
            return L
    return None


async def _is_admin(client, chat_id, user_id) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception:
        return False


def register_fun_handler(app: Client):

    # ==========================================================
    # رفع <اسم> (reply required)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(ADD_REGEX))
    async def fun_add(client, message: Message):
        if not message.from_user:
            return
        try:
            word = message.matches[0].group(1)
        except Exception:
            return
        list_def = _find_by_singular(word)
        if not list_def:
            return

        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text(
                f"⚠️ رد على مستخدم لرفعه في قائمة {list_def['emoji']} {list_def['plural_label']}"
            )

        target = message.reply_to_message.from_user
        if target.is_bot:
            return await message.reply_text("⚠️ لا يمكن رفع البوتات في القوائم.")

        try:
            if await db.is_in_fun_list(message.chat.id, list_def["db_key"], target.id):
                return await message.reply_text(
                    f"⚠️ {target.mention} موجود مسبقاً في قائمة {list_def['emoji']} {list_def['plural_label']}"
                )
            await db.add_to_fun_list(
                message.chat.id,
                list_def["db_key"],
                target.id,
                target.first_name or "مستخدم",
            )
            await message.reply_text(
                f"✅ تم رفع {target.mention} في قائمة {list_def['emoji']} {list_def['plural_label']}"
            )
        except Exception as e:
            logger.error(f"fun_add error: {e}")
            await message.reply_text(f"❌ حدث خطأ: {e}")

    # ==========================================================
    # تنزيل <اسم> (reply required)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(REMOVE_REGEX))
    async def fun_remove(client, message: Message):
        if not message.from_user:
            return
        try:
            word = message.matches[0].group(1)
        except Exception:
            return
        list_def = _find_by_singular(word)
        if not list_def:
            return

        if not message.reply_to_message or not message.reply_to_message.from_user:
            return await message.reply_text(
                f"⚠️ رد على مستخدم لتنزيله من قائمة {list_def['emoji']} {list_def['plural_label']}"
            )

        target = message.reply_to_message.from_user

        try:
            if not await db.is_in_fun_list(message.chat.id, list_def["db_key"], target.id):
                return await message.reply_text(
                    f"⚠️ {target.mention} غير موجود في قائمة {list_def['emoji']} {list_def['plural_label']}"
                )
            await db.remove_from_fun_list(
                message.chat.id, list_def["db_key"], target.id
            )
            await message.reply_text(
                f"✅ تم تنزيل {target.mention} من قائمة {list_def['emoji']} {list_def['plural_label']}"
            )
        except Exception as e:
            logger.error(f"fun_remove error: {e}")
            await message.reply_text(f"❌ حدث خطأ: {e}")

    # ==========================================================
    # قائمة <الجمع>
    # ==========================================================
    @app.on_message(filters.group & filters.regex(SHOW_REGEX))
    async def fun_show(client, message: Message):
        try:
            word = message.matches[0].group(1)
        except Exception:
            return
        list_def = _find_by_plural(word)
        if not list_def:
            return

        try:
            items = await db.get_fun_list(message.chat.id, list_def["db_key"])
        except Exception as e:
            logger.error(f"fun_show error: {e}")
            return await message.reply_text(f"❌ حدث خطأ: {e}")

        if not items:
            return await message.reply_text(
                f"⚠️ قائمة {list_def['emoji']} {list_def['plural_label']} فارغة."
            )

        txt = f"📋 قائمة {list_def['emoji']} {list_def['plural_label']}:\n\n"
        for i, item in enumerate(items, 1):
            name = item.get("user_name") or "مستخدم"
            uid = item.get("user_id")
            txt += f"{i}. [{name}](tg://user?id={uid})\n"
        txt += f"\n👥 العدد: {len(items)}"
        await message.reply_text(txt, disable_web_page_preview=True)

    # ==========================================================
    # مسح قائمة <الجمع> (admin only)
    # ==========================================================
    @app.on_message(filters.group & filters.regex(CLEAR_REGEX))
    async def fun_clear(client, message: Message):
        if not message.from_user:
            return
        try:
            word = message.matches[0].group(1)
        except Exception:
            return
        list_def = _find_by_plural(word)
        if not list_def:
            return

        if not await _is_admin(client, message.chat.id, message.from_user.id):
            return await message.reply_text(
                "❌ هذا الأمر يخص المشرف وفوق بس"
            )

        try:
            await db.clear_fun_list(message.chat.id, list_def["db_key"])
            await message.reply_text(
                f"✅ تم مسح قائمة {list_def['emoji']} {list_def['plural_label']}"
            )
        except Exception as e:
            logger.error(f"fun_clear error: {e}")
            await message.reply_text(f"❌ حدث خطأ: {e}")
