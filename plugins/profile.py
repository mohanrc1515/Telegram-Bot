import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime  # For birthday validation and age calculation
from helper.database import db  # Import database helper

# Temporary storage for user states during profile setup
user_states = {}

def calculate_age(birthday: str) -> int:
    """Calculate age from birthday (YYYY-MM-DD format)."""
    today = datetime.today()
    birth_date = datetime.strptime(birthday, "%Y-%m-%d")
    age = today.year - birth_date.year

    # Adjust age if birthday hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age

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
        # Format birthday for display
        birthday = profile.get("birthday", "Not set")
        if birthday != "Not set":
            age = calculate_age(birthday)  # Calculate age
            birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%d %b %Y") + f" ({age})"  # Add age in brackets

        # Create inline buttons
        buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✏ Edit", callback_data="edit_profile"),
                 InlineKeyboardButton("📝 Bio", callback_data=f"show_bio_{user_id}")]
            ]
        )

        await message.reply_photo(
            photo=profile.get("photo", "https://envs.sh/On-.jpg"),
            caption=(
                f"👤 **Name:** {profile['name']}\n"
                f"📍 **Location:** {profile['location']}\n"
                f"🎂 **Birthday:** {birthday}\n\n"
                f"🆔 **User ID:** `{user_id}`"
            ),
            reply_markup=buttons
        )
    else:
        await message.reply("⚠ You haven't set your profile yet. Use /set_profile to create one.")

@Client.on_message(filters.command("editbio"))
async def edit_bio(client: Client, message: Message):
    user_id = message.from_user.id
    profile = await db.get_profile(user_id)

    if profile:
        await message.reply("✏ **Please send your new bio (max 200 characters):**")
        user_states[user_id] = {"step": "edit_bio"}  # Set state for bio editing
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
            "location": profile["location"],
            "birthday": profile["birthday"],
            "bio": profile["bio"],
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

    # Retain existing values instead of setting "Not set"
    existing_data = await db.get_profile(user_id)
    if existing_data and step in existing_data:
        user_states[user_id][step] = existing_data[step]
    else:
        user_states[user_id][step] = "Not set"

    next_step = {
        "photo": "name",
        "name": "location",
        "location": "birthday",
        "birthday": "bio",
        "bio": "save"
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

    if step in ["name", "location", "birthday", "bio", "edit_bio"]:
        if step == "birthday":
            try:
                # Validate birthday format (YYYY-MM-DD)
                datetime.strptime(message.text, "%Y-%m-%d")
            except ValueError:
                await message.reply("⚠ **Invalid date format!** Please use `YYYY-MM-DD`. (or use /skip)")
                return

        if step in ["bio", "edit_bio"]:
            if len(message.text) > 200:
                await message.reply("⚠ **Bio must be 200 characters or less.** Please shorten it.")  # Removed show_alert
                return

        if step == "edit_bio":
            # Update bio directly
            profile = await db.get_profile(user_id)
            if profile:
                profile["bio"] = message.text
                await db.save_profile(user_id, profile)
                del user_states[user_id]
                await message.reply("✅ **Bio updated successfully!** Use /profile to view it.")
            return

        user_states[user_id][step] = message.text
        next_step = {
            "name": "location",
            "location": "birthday",
            "birthday": "bio",
            "bio": "save"
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
        "name": user_states[user_id].get("name", "Not set"),
        "location": user_states[user_id].get("location", "Not set"),
        "birthday": user_states[user_id].get("birthday", "Not set"),
        "bio": user_states[user_id].get("bio", "Not set"),
    }
    await db.save_profile(user_id, profile_data)
    del user_states[user_id]

    # ✅ **Final confirmation message**
    await message.reply("✅ **Profile saved!** Use /profile to view it.")


@Client.on_message(filters.command("check"))
async def view_user_profile(client, message):
    # Check if the user provided a username or user ID
    if len(message.command) < 2:
        await message.reply("⚠ **Usage:** `/check <user_id or username>`")
        return

    target = message.command[1]

    try:
        # Try to parse the target as a user ID
        user_id = int(target)
        user = await client.get_users(user_id)
    except ValueError:
        # If it's not a user ID, assume it's a username
        try:
            user = await client.get_users(target)
        except Exception as e:
            await message.reply("⚠ **User not found.** Please check the username or user ID.")
            return
    except Exception as e:
        await message.reply(f"⚠ **An error occurred:** {e}")
        return

    # Fetch the profile from the database
    profile = await db.get_profile(user.id)

    if profile:
        # Format birthday for display
        birthday = profile.get("birthday", "Not set")
        if birthday != "Not set":
            age = calculate_age(birthday)  # Calculate age
            birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%d %b %Y") + f" ({age})"  # Add age in brackets

        # Create inline buttons (horizontal alignment: Edit | Bio)
        buttons = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("📝 Bio", callback_data=f"show_bio_{user.id}")
                ]
            ]
        )

        await message.reply_photo(
            photo=profile.get("photo", "https://envs.sh/On-.jpg"),
            caption=(
                f"👤 **Name:** {profile['name']}\n"
                f"📍 **Location:** {profile['location']}\n"
                f"🎂 **Birthday:** {birthday}\n\n"
                f"🆔 **User ID:** `{user.id}`"
            ),
            reply_markup=buttons
        )
    else:
        await message.reply("⚠ **This user hasn't set up their profile yet.**")


@Client.on_callback_query(filters.regex(r"^show_bio_(\d+)$"))
async def show_bio(client: Client, callback_query):
    user_id = int(callback_query.data.split("_")[2])  # Extract user ID from callback data
    profile = await db.get_profile(user_id)

    if profile and profile.get("bio", "Not set") != "Not set":
        await callback_query.answer(profile["bio"], show_alert=True)
    else:
        await callback_query.answer("⚠ No bio set yet!", show_alert=True)
