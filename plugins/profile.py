import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db  # Import database helper

# Temporary storage for user states during profile setup
user_states = {}

@Client.on_message(filters.command("set_profile"))
async def set_profile_handler(client: Client, message: Message):
    user_id = message.from_user.id

    user_states[user_id] = {
        "step": "photo"
    }

    await message.reply("📸 Please send your **profile picture**.")

@Client.on_message(filters.command("profile"))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        edit_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✏ Edit Profile", callback_data="edit_profile")]]
        )

        await message.reply_photo(
            photo=profile.get("photo", "https://envs.sh/On-.jpg"),
            caption=(
                f"📌 **Your Profile**\n"
                f"👤 **Real Name:** {profile['name']}\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"📍 **Location:** {profile['city']}, {profile['country']}\n"
                f"🎂 **Age:** {profile['age']}\n"
            ),
            reply_markup=edit_button
        )
    else:
        await message.reply("⚠ You haven't set your profile yet. Use /set_profile to create one.")

@Client.on_message(filters.command("del_profile"))
async def delete_profile(client: Client, message: Message):
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        await db.delete_profile(user_id)  # Deleting profile from database
        await message.reply("✅ **Your profile has been deleted successfully.**")
    else:
        await message.reply("⚠ You don't have a profile set up yet.")

@Client.on_message(filters.command("cancel"))
async def cancel_setup(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]

        # Remove partially saved profile if exists
        await db.delete_partial_profile(user_id)

        await message.reply("❌ **Profile setup canceled.**")
    else:
        await message.reply("⚠ You're not in profile setup mode.")

@Client.on_callback_query(filters.regex("edit_profile"))
async def edit_profile(client: Client, callback_query):
    user_id = callback_query.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        user_states[user_id] = {
            "step": "photo",
            "photo": profile["photo"],
            "name": profile["name"],
            "city": profile["city"],
            "country": profile["country"],
            "age": profile["age"],
        }
        await callback_query.message.reply("✏ Editing profile! **Send your new profile picture** or use /skip.")
    else:
        await callback_query.message.reply("⚠ You haven't set your profile yet. Use /set_profile.")

@Client.on_message(filters.command("skip"))
async def skip_step(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    step = user_states[user_id]["step"]

    # Retain existing values instead of setting "Confidential"
    existing_data = await db.get_profile(user_id)
    if existing_data and step in existing_data:
        user_states[user_id][step] = existing_data[step]
    else:
        user_states[user_id][step] = "Confidential"

    next_step = {
        "name": "city",
        "city": "country",
        "country": "age",
        "age": "save"
    }[step]

    if next_step == "save":
        await save_profile(user_id, message)
    else:
        user_states[user_id]["step"] = next_step
        await message.reply(f"✅ **{step.capitalize()} skipped!** Now, enter your **{next_step}** (or use /skip).")

@Client.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id]["step"] == "photo":
        user_states[user_id]["photo"] = message.photo.file_id
        user_states[user_id]["step"] = "name"
        await message.reply("✅ **Photo saved!** Now, send your **real name**. (or use /skip)")

@Client.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    step = user_states[user_id]["step"]

    if step in ["name", "city", "country", "age"]:
        if step == "age" and not message.text.isdigit():
            await message.reply("⚠ **Please enter a valid age** (numbers only). (or use /skip)")
            return

        user_states[user_id][step] = message.text if step != "age" else int(message.text)
        next_step = {
            "name": "city",
            "city": "country",
            "country": "age",
            "age": "save"
        }[step]

        if next_step == "save":
            await save_profile(user_id, message)
        else:
            user_states[user_id]["step"] = next_step
            await message.reply(f"✅ **{step.capitalize()} saved!** Now, enter your **{next_step}** (or use /skip).")

async def save_profile(user_id, message):
    """Save the collected profile data to the database."""
    profile_data = {
        "user_id": user_id,
        "photo": user_states[user_id].get("photo", "https://envs.sh/On-.jpg"),
        "name": user_states[user_id].get("name", "Confidential"),
        "city": user_states[user_id].get("city", "Confidential"),
        "country": user_states[user_id].get("country", "Confidential"),
        "age": user_states[user_id].get("age", "Confidential"),
    }
    await db.save_profile(user_id, profile_data)
    del user_states[user_id]

    # ✅ **Final confirmation message**
    await message.reply("✅ **Profile saved!** Use /profile to view it.")

# 📌 Command: /user <username/user_id>
@Client.on_message(filters.private & filters.command("user"))
async def user_profile(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("⚠ **Please provide a username or user ID.**\nExample: `/user @username` or `/user 12345678`")
        return

    target = args[0]

    try:
        if target.startswith("@"):
            target_user = await client.get_users(target)
            target_id = target_user.id
        else:
            if not target.isdigit():
                await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
                return
            target_id = int(target)
    except Exception:
        await message.reply("⚠ **User not found.** Please check the username.")
        return

    requester_id = message.from_user.id

    # Check if the requester has blocked the target user
    blocked_users = await db.get_blocked_users(requester_id) or []
    if target_id in blocked_users:
        await message.reply("🚫 **You have blocked this user.** Unblock them first to view their profile.")
        return

    # Check if the target user has blocked the requester
    target_blocked_users = await db.get_blocked_users(target_id) or []
    if requester_id in target_blocked_users:
        await message.reply("🚫 **This user has blocked you.** You cannot view their profile.")
        return

    # Fetch profile from the database
    profile = await db.get_profile(target_id)
    if profile:
        await message.reply_photo(
            photo=profile.get("photo", "https://envs.sh/On-.jpg"),
            caption=(
                f"📌 **User Profile**\n"
                f"👤 **Real Name:** {profile['name']}\n"
                f"🆔 **User ID:** `{target_id}`\n"
                f"📍 **Location:** {profile['city']}, {profile['country']}\n"
                f"🎂 **Age:** {profile['age']}\n"
            )
        )
    else:
        await message.reply("⚠ **This user has not set up their profile.**")

# 📌 Command: /block <username/user_id>
@Client.on_message(filters.private & filters.command("block"))
async def block_user(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("⚠ **Please provide a username or user ID to block.**\nExample: `/block @username` or `/block 12345678`")
        return

    target = args[0]

    try:
        if target.startswith("@"):
            target_user = await client.get_users(target)
            target_id = target_user.id
        else:
            if not target.isdigit():
                await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
                return
            target_id = int(target)
    except Exception:
        await message.reply("⚠ **User not found.** Please check the username.")
        return

    requester_id = message.from_user.id

    if target_id == requester_id:
        await message.reply("⚠ **You cannot block yourself!**")
        return

    blocked_users = await db.get_blocked_users(requester_id) or []
    if target_id in blocked_users:
        await message.reply("⚠ **This user is already blocked.**")
        return

    await db.block_user(requester_id, target_id)
    await message.reply(f"🚫 **User `{target_id}` has been blocked.** They will no longer see your profile.")

# 📌 Command: /unblock <username/user_id>
@Client.on_message(filters.private & filters.command("unblock"))
async def unblock_user(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("⚠ **Please provide a username or user ID to unblock.**\nExample: `/unblock @username` or `/unblock 12345678`")
        return

    target = args[0]

    try:
        if target.startswith("@"):
            target_user = await client.get_users(target)
            target_id = target_user.id
        else:
            if not target.isdigit():
                await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
                return
            target_id = int(target)
    except Exception:
        await message.reply("⚠ **User not found.** Please check the username.")
        return

    requester_id = message.from_user.id

    blocked_users = await db.get_blocked_users(requester_id) or []
    if target_id not in blocked_users:
        await message.reply("⚠ **This user is not in your block list.**")
        return

    await db.unblock_user(requester_id, target_id)
    await message.reply(f"✅ **User `{target_id}` has been unblocked.** They can now see your profile.")

# 📌 Command: /blocklist (View blocked users)
@Client.on_message(filters.private & filters.command("blocklist"))
async def view_blocklist(client: Client, message: Message):
    user_id = message.from_user.id
    blocked_users = await db.get_blocked_users(user_id) or []

    if not blocked_users:
        await message.reply("✅ **You have not blocked anyone.**")
    else:
        blocked_list_text = "\n".join([f"🔹 `{uid}`" for uid in blocked_users])
        await message.reply(f"🚫 **Blocked Users:**\n{blocked_list_text}")
