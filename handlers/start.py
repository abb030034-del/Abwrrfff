# ============================================================
#Group Manager Bot
# Author: LearningBotsOfficial (https://github.com/LearningBotsOfficial) 
# Support: https://t.me/LearningBotsCommunity
# Channel: https://t.me/learning_bots
# YouTube: https://youtube.com/@learning_bots
# License: Open-source (keep credits, no resale)
# ============================================================


from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from config import BOT_USERNAME, SUPPORT_GROUP, UPDATE_CHANNEL, START_IMAGE, OWNER_ID
import db

def register_handlers(app: Client):

# ==========================================================
# Start Message
# ==========================================================
    async def send_start_menu(message, user):
        text = f"""

   ✨ أهلاً {user}! ✨

👋 أنا نومад 🤖 

المميزات:
─────────────────────────────
- حماية ذكية من السبام وحجب الروابط
- نظام قفل متكيف (روابط، وسائط، لغة والمزيد)
- حماية معيارية وقابلة للتوسع
- واجهة أنيقة مع أزرار تفاعلية

» المزيد من المميزات قادمة قريباً ...
"""

        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("⚒️ أضفني للمجموعة ⚒️", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")],
            [
                InlineKeyboardButton("⌂ الدعم ⌂", url=SUPPORT_GROUP),
                InlineKeyboardButton("⌂ التحديثات ⌂", url=UPDATE_CHANNEL),
            ],
            [
                InlineKeyboardButton("※ المالك ※", url=f"tg://user?id={OWNER_ID}"),
                InlineKeyboardButton("المستودع", url="https://github.com/LearningBotsOfficial/Nomade"),
                
            ],
            [InlineKeyboardButton("📚 قائمة الأوامر 📚", callback_data="help")]
        ])

        # If /start command, send a new photo
        if message.text:
            await message.reply_photo(START_IMAGE, caption=text, reply_markup=buttons)
        else:
            # If callback, edit the same message
            media = InputMediaPhoto(media=START_IMAGE, caption=text)
            await message.edit_media(media=media, reply_markup=buttons)

# ==========================================================
# Start Command
# ==========================================================
    @app.on_message(filters.private & (filters.command("start") | filters.regex(r"^ابدأ")))
    async def start_command(client, message):
        user = message.from_user
        await db.add_user(user.id, user.first_name)
        await send_start_menu(message, user.first_name)

# ==========================================================
# Help Menu Message
# ==========================================================
    async def send_help_menu(message):
        text = """
╔══════════════════╗
     قائمة المساعدة
╚══════════════════╝

اختر قسماً للاطلاع على الأوامر:
─────────────────────────────
"""
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⌂ الترحيب ⌂", callback_data="greetings"),
                InlineKeyboardButton("⌂ الأقفال ⌂", callback_data="locks"),
            ],
            [
                InlineKeyboardButton("⌂ الإدارة ⌂", callback_data="moderation")
            ],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_start")]
        ])

        media = InputMediaPhoto(media=START_IMAGE, caption=text)
        await message.edit_media(media=media, reply_markup=buttons)

# ==========================================================
# Help Callback_query
# ==========================================================
    @app.on_callback_query(filters.regex("help"))
    async def help_callback(client, callback_query):
        await send_help_menu(callback_query.message)
        await callback_query.answer()

# ==========================================================
# back to start Callback_query
# ==========================================================
    @app.on_callback_query(filters.regex("back_to_start"))
    async def back_to_start_callback(client, callback_query):
        user = callback_query.from_user.first_name
        await send_start_menu(callback_query.message, user)
        await callback_query.answer()

# ==========================================================
# Greetings Callback_query
# ==========================================================
    @app.on_callback_query(filters.regex("greetings"))
    async def greetings_callback(client, callback_query):
        text = """
╔══════════════════╗
    ⚙ نظام الترحيب
╚══════════════════╝

أوامر إدارة رسائل الترحيب:

- /تعيين_ترحيب <نص> : تعيين رسالة ترحيب مخصصة للمجموعة
- /ترحيب on      : تفعيل رسائل الترحيب
- /ترحيب off     : إيقاف رسائل الترحيب

المتغيرات المتاحة:
- {username} : اسم المستخدم على تيليغرام
- {first_name} : الاسم الأول للمستخدم
- {id} : معرف المستخدم
- {mention} : الإشارة للمستخدم في الرسالة

مثال:
 /setwelcome مرحباً {first_name}! أهلاً بك في {title}!
"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="help")]
        ])
        media = InputMediaPhoto(media=START_IMAGE, caption=text)
        await callback_query.message.edit_media(media=media, reply_markup=buttons)
        await callback_query.answer()

# ==========================================================
# Locks callback_query
# ==========================================================
    @app.on_callback_query(filters.regex("locks"))
    async def locks_callback(client, callback_query):
        text = """
╔══════════════════╗
     ⚙ نظام الأقفال
╚══════════════════╝

أوامر إدارة الأقفال:

- /lock <نوع>    : تفعيل قفل في المجموعة
- /unlock <نوع>  : إلغاء قفل في المجموعة
- /الاقفال          : عرض الأقفال النشطة حالياً

أنواع الأقفال المتاحة:
- url       : حجب الروابط
- sticker   : حجب الملصقات
- media     : حجب الصور/الفيديوهات/الصور المتحركة
- username  : حجب الرسائل التي تحتوي على إشارات @username
- language  : حجب الرسائل غير العربية

مثال:
 /قفل url       : يحجب أي رسائل تحتوي على روابط
 /فتح ملصق : يسمح بالملصقات مرة أخرى
"""
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="help")]
        ])
        media = InputMediaPhoto(media=START_IMAGE, caption=text)
        await callback_query.message.edit_media(media=media, reply_markup=buttons)
        await callback_query.answer()

# ==========================================================
# Moderation Callback_query
# ==========================================================
    @app.on_callback_query(filters.regex("moderation"))
    async def info_callback(client, callback_query):
        try:
            text = """
╔══════════════════╗
      ⚙️ نظام الإدارة
╚══════════════════╝

أدر مجموعتك بسهولة باستخدام هذه الأوامر:

¤ /kick <مستخدم> — طرد مستخدم  
¤ /ban <مستخدم> — حظر دائم  
¤ /unban <مستخدم> — رفع الحظر  
¤ /mute <مستخدم> — كتم الرسائل  
¤ /unmute <مستخدم> — السماح بالرسائل مجدداً  
¤ /warn <مستخدم> — إضافة تحذير (3 = كتم)  
¤ /warns <مستخدم> — عرض التحذيرات  
¤ /resetwarns <مستخدم> — مسح جميع التحذيرات  
¤ /promote <مستخدم> — ترقية لمشرف
¤ /demote <مستخدم> — إزالة من المشرفين  

💡 مثال:
رد على مستخدم أو اكتب  
<code>/حظر @username</code>

"""
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="help")]
            ])
    
            media = InputMediaPhoto(media=START_IMAGE, caption=text)
            await callback_query.message.edit_media(media=media, reply_markup=buttons)
            await callback_query.answer()
    
        except Exception as e:
            print(f"Error in info_callback: {e}")
            await callback_query.answer("❌ حدث خطأ ما.", show_alert=True)
    

# ==========================================================
# Broadcast Command
# ==========================================================
    @app.on_message(filters.private & filters.regex(r"^بث"))
    async def broadcast_message(client, message):
        if not message.reply_to_message:
            await message.reply_text("⚠️ يرجى الرد على رسالة لبثها.")
            return

        if message.from_user.id != OWNER_ID:
            await message.reply_text("❌ فقط مالك البوت يمكنه استخدام هذا الأمر.")
            return

        text_to_send = message.reply_to_message.text or message.reply_to_message.caption
        if not text_to_send:
            await message.reply_text("⚠️ الرسالة المردود عليها لا تحتوي على نص للإرسال.")
            return

        users = await db.get_all_users()
        sent, failed = 0, 0

        await message.reply_text(f"جارٍ البث لـ {len(users)} مستخدم...")

        for user_id in users:
            try:
                await client.send_message(user_id, text_to_send)
                sent += 1
            except Exception:
                failed += 1

        await message.reply_text(f"✅ اكتمل البث!\n\n تم الإرسال: {sent}\nفشل: {failed}")

# ==========================================================
# stats Command
# ==========================================================
    @app.on_message(filters.private & filters.regex(r"^احصائيات"))
    async def stats_command(client, message):
        if message.from_user.id != OWNER_ID:
            return await message.reply_text("❌ فقط مالك البوت يمكنه استخدام هذا الأمر")

        users = await db.get_all_users()
        return await message.reply_text(f"💡 إجمالي المستخدمين: {len(users)}")

# ==========================================================
# Commands list (/اوامر | اوامر | الاوامر)
# ==========================================================
    COMMANDS_TEXT = """╔══════════════════╗
    📋 قائمة الأوامر الكاملة
╚══════════════════╝

🛡️ **أوامر الإدارة:**
▸ طرد — طرد مستخدم
▸ حظر — حظر مستخدم
▸ رفع_حظر — رفع الحظر
▸ كتم — كتم مستخدم
▸ رفع_كتم — رفع الكتم
▸ تحذير — تحذير مستخدم (3 = كتم)
▸ التحذيرات — عرض التحذيرات
▸ مسح_تحذيرات — مسح التحذيرات
▸ ترقية — ترقية لمشرف
▸ تخفيض — إزالة من المشرفين

🔒 **أوامر الأقفال:**
▸ قفل [url/sticker/media/username/forward] — تفعيل قفل
▸ فتح [url/sticker/media/username/forward] — إلغاء قفل
▸ الاقفال — عرض الأقفال

👋 **أوامر الترحيب:**
▸ ترحيب on/off — تفعيل/تعطيل
▸ تعيين_ترحيب [نص] — تعيين رسالة الترحيب

📋 **القوانين:**
▸ وضع قوانين — تعيين القوانين
▸ القوانين — عرض القوانين
▸ مسح القوانين — مسح القوانين

💬 **الردود المخصصة:**
▸ اضف رد — إضافة رد تلقائي
▸ مسح رد — مسح رد
▸ الردود — عرض الردود
▸ مسح الردود — مسح كل الردود

🎭 **قوائم المرح:**
▸ رفع كيك🍰 / تنزيل كيك / قائمة الكيك
▸ رفع عسل🍯 / تنزيل عسل / قائمة العسل
▸ رفع نصاب💩 / تنزيل نصاب / قائمة النصابين
▸ رفع حمار🦓 / تنزيل حمار / قائمة الحمير
▸ رفع بقرة🐄 / تنزيل بقرة / قائمة البقر
▸ رفع كلب🐩 / تنزيل كلب / قائمة الكلاب
▸ رفع قرد🐒 / تنزيل قرد / قائمة القرود
▸ رفع تيس🐐 / تنزيل تيس / قائمة التيوس
▸ رفع ثور🐂 / تنزيل ثور / قائمة الثور
▸ رفع دجاجة🐓 / تنزيل دجاجة / قائمة الدجاج
▸ رفع ملكة👑 / تنزيل ملكة / قائمة الملكات
▸ رفع صياد🔫 / تنزيل صياد / قائمة الصيادين
▸ رفع خروف🐏 / تنزيل خروف / قائمة الخرفان
▸ مسح قائمة [X] — مسح القائمة (للادمن فقط)

ℹ️ **معلومات:**
▸ آيدي — معرفة ID
▸ معلوماتي — معلومات عنك
▸ معلومات — معلومات عن مستخدم

📖 **القرآن الكريم:**
▸ سورة [اسم السورة] — رابط استماع السورة

🤫 **الهمسة:**
▸ اكتب في الإنلاين: @بوت رسالة @username

💬 **الصراحة:**
▸ صارحني — احصل على رابط صارحني

☆
"""

    @app.on_message(filters.regex(r"^(/?(?:اوامر|الاوامر))$"))
    async def commands_list(client, message):
        try:
            await message.reply_text(COMMANDS_TEXT)
        except Exception as e:
            print(f"commands_list error: {e}")
