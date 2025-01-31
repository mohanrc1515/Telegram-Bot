import os
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import db  # Import database helper

# 📌 Command: /user <username/user_id>
@Client.on_message(filters.command("user"))
async def user_profile(client: Client, message: Message):
    args = message.command[1:]  # Extract username or user_id
    if not args:
        await message.reply("⚠ **Please provide a username or user ID.**\nExample: `/user @username` or `/user 12345678`")
        return

    target = args[0]
    
    # Get target user ID
    if target.startswith("@"):
        target_user = await client.get_users(target)
        if not target_user:
            await message.reply("⚠ **User not found.** Please check the username.")
            return
        target_id = target_user.id
    else:
        if not target.isdigit():
            await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
            return
        target_id = int(target)

    requester_id = message.from_user.id

    # Check if the requester has blocked the target user
    blocked_users = await db.get_blocked_users(requester_id)
    if target_id in blocked_users:
        await message.reply("🚫 **You have blocked this user.** Unblock them first to view their profile.")
        return

    # Check if the target user has blocked the requester
    target_blocked_users = await db.get_blocked_users(target_id)
    if requester_id in target_blocked_users:
        await message.reply("🚫 **This user has blocked you.** You cannot view their profile.")
        return

    # Fetch profile from the database
    profile = await db.get_profile(target_id)
    if profile:
        first_name = profile.get("first_name", "N/A")
        last_name = profile.get("last_name", "N/A")
        is_premium = "Yes" if profile.get("is_premium", "No") == "Yes" else "No"
        dc_id = profile.get("dc_id", "Unknown")

        await message.reply_photo(
            photo=profile.get("photo", "https://example.com/default.jpg"),
            caption=(
                f"📌 **User Profile**\n"
                f"👤 **Real Name:** {profile['name']}\n"
                f"📛 **Telegram Name:** {first_name} {last_name}\n"
                f"🆔 **User ID:** `{target_id}`\n"
                f"🗂 **DC Number:** `{dc_id}`\n"
                f"📍 **Location:** {profile['city']}, {profile['country']}\n"
                f"🎂 **Age:** {profile['age']}\n"
                f"💎 **Premium User:** {is_premium}"
            )
        )
    else:
        await message.reply("⚠ **This user has not set up their profile.**")

# 📌 Command: /block <username/user_id>
@Client.on_message(filters.command("block"))
async def block_user(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("⚠ **Please provide a username or user ID to block.**\nExample: `/block @username` or `/block 12345678`")
        return

    target = args[0]

    # Get target user ID
    if target.startswith("@"):
        target_user = await client.get_users(target)
        if not target_user:
            await message.reply("⚠ **User not found.** Please check the username.")
            return
        target_id = target_user.id
    else:
        if not target.isdigit():
            await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
            return
        target_id = int(target)

    requester_id = message.from_user.id

    if target_id == requester_id:
        await message.reply("⚠ **You cannot block yourself!**")
        return

    # Add to blocked list
    await db.block_user(requester_id, target_id)
    await message.reply(f"🚫 **User `{target_id}` has been blocked.** They will no longer see your profile.")

# 📌 Command: /unblock <username/user_id>
@Client.on_message(filters.command("unblock"))
async def unblock_user(client: Client, message: Message):
    args = message.command[1:]
    if not args:
        await message.reply("⚠ **Please provide a username or user ID to unblock.**\nExample: `/unblock @username` or `/unblock 12345678`")
        return

    target = args[0]

    # Get target user ID
    if target.startswith("@"):
        target_user = await client.get_users(target)
        if not target_user:
            await message.reply("⚠ **User not found.** Please check the username.")
            return
        target_id = target_user.id
    else:
        if not target.isdigit():
            await message.reply("⚠ **Invalid user ID.** User IDs must be numeric.")
            return
        target_id = int(target)

    requester_id = message.from_user.id

    # Remove from blocked list
    success = await db.unblock_user(requester_id, target_id)
    if success:
        await message.reply(f"✅ **User `{target_id}` has been unblocked.** They can now see your profile.")
    else:
        await message.reply("⚠ **This user is not in your block list.**")

# 📌 Command: /blocklist (View blocked users)
@Client.on_message(filters.command("blocklist"))
async def view_blocklist(client: Client, message: Message):
    user_id = message.from_user.id
    blocked_users = await db.get_blocked_users(user_id)

    if not blocked_users:
        await message.reply("✅ **You have not blocked anyone.**")
    else:
        blocked_list_text = "\n".join([f"🔹 `{uid}`" for uid in blocked_users])
        await message.reply(f"🚫 **Blocked Users:**\n{blocked_list_text}")
