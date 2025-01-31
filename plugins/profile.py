import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db  # Import the database helper

# Store user states temporarily
user_states = {}

# Command: /profile
@Client.on_message(filters.command("profile"))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        # Creating an "Edit Profile" button
        edit_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✏ Edit Profile", callback_data="edit_profile")]]
        )

        await message.reply_photo(
            photo=profile["photo"],
            caption=(
                f"**Profile Card**\n"
                f"👤 **Real Name:** {profile['name']}\n"
                f"📛 **Telegram Name:** {profile['first_name']} {profile['last_name']}\n"
                f"🆔 **User ID:** `{user_id}`\n"
                f"🗂 **DC Number:** `{profile['dc_id']}`\n"
                f"🌍 **Location:** {profile['city']}, {profile['country']}\n"
                f"🎂 **Age:** {profile['age']}\n"
                f"💎 **Premium:** {'Yes' if profile['is_premium'] else 'No'}"
            ),
            reply_markup=edit_button
        )
    else:
        await message.reply("You haven't set your profile yet. Set it using /set_profile.")

# Command: /set_profile
@Client.on_message(filters.command("set_profile"))
async def set_profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user = message.from_user
    
    # Get basic user info
    user_states[user_id] = {
        "step": "photo",
        "first_name": user.first_name or "N/A",
        "last_name": user.last_name or "N/A",
        "dc_id": user.dc_id or "Unknown",
        "is_premium": user.is_premium or False
    }
    
    await message.reply("Please send your profile picture.")

# Handle /cancel command
@Client.on_message(filters.command("cancel"))
async def cancel_setup(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        await message.reply("Profile setup has been canceled.")
    else:
        await message.reply("You're not in profile setup mode.")

# Handle edit button
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
            "first_name": profile["first_name"],
            "last_name": profile["last_name"],
            "dc_id": profile["dc_id"],
            "is_premium": profile["is_premium"]
        }
        await callback_query.message.reply("Editing profile! Please send your new profile picture or use /skip.")
    else:
        await callback_query.message.reply("You haven't set your profile yet. Use /set_profile.")

# Handle /skip command
@Client.on_message(filters.command("skip"))
async def skip_step(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    step = user_states[user_id]["step"]

    if step in ["name", "city", "country", "age"]:
        # Use previously saved data
        user_states[user_id][step] = user_states[user_id].get(step, "Confidential")

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
            await message.reply(f"{step.capitalize()} skipped! Now, enter your {next_step}. (or use /skip)")

# Handle photo upload
@Client.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_states and user_states[user_id]["step"] == "photo":
        user_states[user_id]["photo"] = message.photo.file_id
        user_states[user_id]["step"] = "name"
        await message.reply("Great! Now send your real name. (or use /skip)")

# Handle text responses
@Client.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    step = user_states[user_id]["step"]

    if step in ["name", "city", "country", "age"]:
        if step == "age" and not message.text.isdigit():
            await message.reply("Please enter a valid age (numbers only). (or use /skip)")
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
            await message.reply(f"Now, enter your {next_step}. (or use /skip)")

async def save_profile(user_id, message):
    """Save the collected profile data to the database."""
    profile_data = {
        "user_id": user_id,
        "photo": user_states[user_id]["photo"],
        "name": user_states[user_id].get("name", "Confidential"),
        "city": user_states[user_id].get("city", "Confidential"),
        "country": user_states[user_id].get("country", "Confidential"),
        "age": user_states[user_id].get("age", "Confidential"),
        "first_name": user_states[user_id].get("first_name", "N/A"),
        "last_name": user_states[user_id].get("last_name", "N/A"),
        "dc_id": user_states[user_id].get("dc_id", "Unknown"),
        "is_premium": user_states[user_id].get("is_premium", False),
    }
    await db.save_profile(user_id, profile_data)
    del user_states[user_id]
    await message.reply("✅ Your profile has been saved! Use /profile to view it.")
