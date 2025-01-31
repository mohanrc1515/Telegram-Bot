import logging
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.database import db
from helper.utils import calculate_age
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state management for profile setup
user_states = {}

# Helper function to validate date format
def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

# Helper function to calculate time difference
def calculate_time_difference(last_time: datetime) -> str:
    current_time = datetime.now()
    time_difference = current_time - last_time
    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{days} days, {hours} hours, and {minutes} minutes"

# Command: /nofap
@Client.on_message(filters.command("nofap"))
async def nofap_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        last_fap_time = await db.get_last_fap_time(user_id)
        if not last_fap_time:
            await message.reply("When was your last time? (Please provide the date and time in format: YYYY-MM-DD HH:MM)")
            return

        time_difference = calculate_time_difference(last_fap_time)
        await message.reply(f"You haven't fapped for **{time_difference}**. Stay strong! 💪")
    except Exception as e:
        logger.error(f"Error in nofap_command for user {user_id}: {e}")
        await message.reply("An error occurred while processing your request. Please try again later.")

# Command: /fapped
@Client.on_message(filters.command("fapped"))
async def fapped_command(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        await db.set_last_fap_time(user_id, datetime.now())
        await message.reply("Your timer has been reset. Stay strong next time! 💪")
    except Exception as e:
        logger.error(f"Error in fapped_command for user {user_id}: {e}")
        await message.reply("An error occurred while resetting your timer. Please try again later.")

# Handle text messages for setting last fap time
@Client.on_message(filters.text & ~filters.command(["nofap", "fapped"]))
async def handle_text_messages(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        last_fap_time = await db.get_last_fap_time(user_id)
        if not last_fap_time:
            date_str = message.text.strip()
            if validate_date(date_str):
                last_fap_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                await db.set_last_fap_time(user_id, last_fap_time)
                await message.reply("Your last fap time has been recorded. Use /nofap to check your progress!")
            else:
                await message.reply("Invalid date format. Please use the format: YYYY-MM-DD HH:MM")
    except Exception as e:
        logger.error(f"Error in handle_text_messages for user {user_id}: {e}")
        await message.reply("An error occurred while processing your input. Please try again.")

# Command: /set_profile
@Client.on_message(filters.command("set_profile"))
async def set_profile_handler(client: Client, message: Message):
    user_id = message.from_user.id

    user_states[user_id] = {"step": "photo"}
    await message.reply("📸 Please send your **profile picture**.")

# Command: /profile
@Client.on_message(filters.command("profile"))
async def profile_handler(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        profile = await db.get_profile(user_id)
        if profile:
            birthday = profile.get("birthday", "Not set")
            if birthday != "Not set":
                age = calculate_age(birthday)
                birthday = datetime.strptime(birthday, "%Y-%m-%d").strftime("%d %b %Y") + f" ({age})"

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
    except Exception as e:
        logger.error(f"Error in profile_handler for user {user_id}: {e}")
        await message.reply("An error occurred while fetching your profile. Please try again later.")

# Command: /editbio
@Client.on_message(filters.command("editbio"))
async def edit_bio(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        profile = await db.get_profile(user_id)
        if profile:
            await message.reply("✏ **Please send your new bio (max 200 characters):**")
            user_states[user_id] = {"step": "edit_bio"}
        else:
            await message.reply("⚠ You haven't set your profile yet. Use /set_profile to create one.")
    except Exception as e:
        logger.error(f"Error in edit_bio for user {user_id}: {e}")
        await message.reply("An error occurred while editing your bio. Please try again later.")

# Command: /del_profile
@Client.on_message(filters.command("del_profile"))
async def delete_profile(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        profile = await db.get_profile(user_id)
        if profile:
            await db.delete_profile(user_id)
            await message.reply("✅ **Your profile has been deleted successfully.**")
        else:
            await message.reply("⚠ You don't have a profile set up yet.")
    except Exception as e:
        logger.error(f"Error in delete_profile for user {user_id}: {e}")
        await message.reply("An error occurred while deleting your profile. Please try again later.")

# Handle profile photo
@Client.on_message(filters.photo)
async def handle_photo(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        if user_id in user_states and user_states[user_id]["step"] == "photo":
            user_states[user_id]["photo"] = message.photo.file_id
            user_states[user_id]["step"] = "name"
            await message.reply("✅ **Photo saved!** Now, send your **real name**. (or use /skip)")
    except Exception as e:
        logger.error(f"Error in handle_photo for user {user_id}: {e}")
        await message.reply("An error occurred while processing your photo. Please try again later.")

# Handle text input during profile setup
@Client.on_message(filters.text & filters.private)
async def handle_text(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        if user_id not in user_states:
            return

        step = user_states[user_id]["step"]

        if step in ["name", "location", "birthday", "bio", "edit_bio"]:
            if step == "birthday":
                if not validate_date(message.text):
                    await message.reply("⚠ **Invalid date format!** Please use `YYYY-MM-DD`. (or use /skip)")
                    return

            if step in ["bio", "edit_bio"]:
                if len(message.text) > 200:
                    await message.reply("⚠ **Bio must be 200 characters or less.** Please shorten it.")
                    return

            if step == "edit_bio":
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
    except Exception as e:
        logger.error(f"Error in handle_text for user {user_id}: {e}")
        await message.reply("An error occurred while processing your input. Please try again later.")

# Save profile data to the database
async def save_profile(user_id: int, message: Message):
    try:
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
        await message.reply("✅ **Profile saved!** Use /profile to view it.")
    except Exception as e:
        logger.error(f"Error in save_profile for user {user_id}: {e}")
        await message.reply("An error occurred while saving your profile. Please try again later.")

# Callback query for editing profile
@Client.on_callback_query(filters.regex("edit_profile"))
async def edit_profile(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    try:
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
    except Exception as e:
        logger.error(f"Error in edit_profile for user {user_id}: {e}")
        await callback_query.message.reply("An error occurred while editing your profile. Please try again later.")

# Callback query for showing bio
@Client.on_callback_query(filters.regex(r"^show_bio_(\d+)$"))
async def show_bio(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[2])

    try:
        profile = await db.get_profile(user_id)
        if profile and profile.get("bio", "Not set") != "Not set":
            await callback_query.answer(profile["bio"], show_alert=True)
        else:
            await callback_query.answer("⚠ No bio set yet!", show_alert=True)
    except Exception as e:
        logger.error(f"Error in show_bio for user {user_id}: {e}")
        await callback_query.answer("An error occurred while fetching your bio. Please try again later.", show_alert=True)
