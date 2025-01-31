import os
from pyrogram import Client, filters
from pyrogram.types import Message
from helper.database import db  # Import the database helper

# Store user states temporarily
user_states = {}

# Command: /profile
@Client.on_message(filters.command("profile"))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        await message.reply_photo(
            photo=profile["photo"],
            caption=(
                f"**Profile Card**\n"
                f"👤 **Name:** {profile['name']}\n"
                f"🌍 **Location:** {profile['city']}, {profile['country']}\n"
                f"🎂 **Age:** {profile['age']}"
            ),
        )
    else:
        await message.reply("You haven't set your profile yet. Set it using /set_profile.")

# Command: /set_profile
@Client.on_message(filters.command("set_profile"))
async def set_profile_handler(client: Client, message: Message):
    user_id = message.from_user.id
    user_states[user_id] = {"step": "photo"}
    await message.reply("Please send your profile picture.")

# Handle /skip command
@Client.on_message(filters.command("skip"))
async def skip_step(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_states:
        return

    step = user_states[user_id]["step"]

    if step in ["name", "city", "country", "age"]:
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
    }
    await db.save_profile(user_id, profile_data)
    del user_states[user_id]
    await message.reply("✅ Your profile has been saved! Use /profile to view it.")
