import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db

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
        is_premium = "Yes" if profile.get("is_premium", "No") == "Yes" else "No"
        city = profile.get("city", "Not Set")
        country = profile.get("country", "Not Set")
        age = profile.get("age", "Not Set")
        photo = profile.get("photo", "https://envs.sh/On-.jpg")

        await message.reply_photo(
            photo=photo,
            caption=(
                f"📌 **User Profile**\n"
                f"👤 **Real Name:** {name}\n"
                f"🆔 **User ID:** `{target_id}`\n"
                f"📍 **Location:** {city}, {country}\n"
                f"🎂 **Age:** {age}\n"
                f"💎 **Premium User:** {is_premium}"
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

# 📌 Command: /start
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)  

    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('Uᴩᴅᴀᴛᴇꜱ', url='https://t.me/AutoRenameUpdates'),
        InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Elites_Assistance')
    ]])

    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)
