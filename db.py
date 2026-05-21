# ============================================================
# Group Manager Bot
# Author: LearningBotsOfficial (https://github.com/LearningBotsOfficial) 
# Support: https://t.me/LearningBotsCommunity
# Channel: https://t.me/learning_bots
# YouTube: https://youtube.com/@learning_bots
# License: Open-source (keep credits, no resale)
# ============================================================


import motor.motor_asyncio
from config import MONGO_URI, DB_NAME
import logging

client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

logging.info("✅ MongoDB initialized")

# ==========================================================
# 🟢 Welcome
# ==========================================================

async def set_welcome_message(chat_id, text: str):
    await db.welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"message": text}},
        upsert=True
    )

async def get_welcome_message(chat_id):
    data = await db.welcome.find_one({"chat_id": chat_id})
    return data.get("message") if data else None

async def set_welcome_status(chat_id, status: bool):
    await db.welcome.update_one(
        {"chat_id": chat_id},
        {"$set": {"enabled": status}},
        upsert=True
    )

async def get_welcome_status(chat_id) -> bool:
    data = await db.welcome.find_one({"chat_id": chat_id})
    return bool(data.get("enabled", True)) if data else True


# ==========================================================
# 🔒 Lock
# ==========================================================

async def set_lock(chat_id, lock_type, status: bool):
    await db.locks.update_one(
        {"chat_id": chat_id},
        {"$set": {f"locks.{lock_type}": status}},
        upsert=True
    )

async def get_locks(chat_id):
    data = await db.locks.find_one({"chat_id": chat_id})
    return data.get("locks", {}) if data else {}


# ==========================================================
# ⚠️ Warn
# ==========================================================

async def add_warn(chat_id: int, user_id: int) -> int:
    data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    warns = data.get("count", 0) + 1 if data else 1

    await db.warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": warns}},
        upsert=True
    )
    return warns

async def get_warns(chat_id: int, user_id: int) -> int:
    data = await db.warns.find_one({"chat_id": chat_id, "user_id": user_id})
    return data.get("count", 0) if data else 0

async def reset_warns(chat_id: int, user_id: int):
    await db.warns.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"count": 0}},
        upsert=True
    )


# ==========================================================
# 🧹 Cleanup
# ==========================================================

async def clear_group_data(chat_id: int):
    await db.welcome.delete_one({"chat_id": chat_id})
    await db.locks.delete_one({"chat_id": chat_id})
    await db.warns.delete_many({"chat_id": chat_id})


# ==========================================================
# 👤 User
# ==========================================================

async def add_user(user_id, first_name):
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"first_name": first_name}},
        upsert=True
    )

async def get_all_users():
    users = []
    async for document in db.users.find({}, {"_id": 0, "user_id": 1}):
        if "user_id" in document:
            users.append(document["user_id"])
    return users


# ==========================================================
# 💬 Custom Filters (Replies)
# ==========================================================

async def add_filter(chat_id, keyword, response_type, response_content, caption=None):
    """
    response_type: 'text', 'photo', 'video', 'sticker', 'audio', 'document', 'animation', 'voice'
    response_content: file_id or text
    caption: optional caption for media
    """
    await db.filters.update_one(
        {"chat_id": chat_id, "keyword": keyword},
        {"$set": {
            "chat_id": chat_id,
            "keyword": keyword,
            "type": response_type,
            "content": response_content,
            "caption": caption,
        }},
        upsert=True,
    )


async def get_filter(chat_id, keyword):
    return await db.filters.find_one({"chat_id": chat_id, "keyword": keyword})


async def get_all_filters(chat_id):
    return await db.filters.find({"chat_id": chat_id}).to_list(length=None)


async def delete_filter(chat_id, keyword):
    await db.filters.delete_one({"chat_id": chat_id, "keyword": keyword})


async def delete_all_filters(chat_id):
    await db.filters.delete_many({"chat_id": chat_id})


# ==========================================================
# 🎭 Fun Lists
# ==========================================================

async def add_to_fun_list(chat_id, list_name, user_id, user_name):
    await db.fun_lists.update_one(
        {"chat_id": chat_id, "list_name": list_name, "user_id": user_id},
        {"$set": {"user_name": user_name}},
        upsert=True,
    )


async def remove_from_fun_list(chat_id, list_name, user_id):
    await db.fun_lists.delete_one(
        {"chat_id": chat_id, "list_name": list_name, "user_id": user_id}
    )


async def get_fun_list(chat_id, list_name):
    return await db.fun_lists.find(
        {"chat_id": chat_id, "list_name": list_name}
    ).to_list(length=None)


async def is_in_fun_list(chat_id, list_name, user_id):
    return bool(
        await db.fun_lists.find_one(
            {"chat_id": chat_id, "list_name": list_name, "user_id": user_id}
        )
    )


async def clear_fun_list(chat_id, list_name):
    await db.fun_lists.delete_many({"chat_id": chat_id, "list_name": list_name})


# ==========================================================
# 📋 Rules
# ==========================================================

async def set_rules(chat_id, text):
    await db.rules.update_one(
        {"chat_id": chat_id},
        {"$set": {"text": text}},
        upsert=True,
    )


async def get_rules(chat_id):
    data = await db.rules.find_one({"chat_id": chat_id})
    return data.get("text") if data else None


async def clear_rules(chat_id):
    await db.rules.delete_one({"chat_id": chat_id})


# ==========================================================
# 🧭 User States (multi-step conversations)
# ==========================================================

async def set_user_state(user_id, chat_id, state, extra=None):
    await db.user_states.update_one(
        {"user_id": user_id, "chat_id": chat_id},
        {"$set": {"state": state, "extra": extra}},
        upsert=True,
    )


async def get_user_state(user_id, chat_id):
    return await db.user_states.find_one({"user_id": user_id, "chat_id": chat_id})


async def clear_user_state(user_id, chat_id):
    await db.user_states.delete_one({"user_id": user_id, "chat_id": chat_id})
