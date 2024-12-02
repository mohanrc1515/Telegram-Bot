from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from config import Config
from helper.utils import format_timestamp
from datetime import datetime
from helper.database import db  # Assuming your Database class is in `database.py`

DEFAULT_THUMBNAIL_URL = "https://graph.org/file/304a4a1c70aa0c520e956.jpg"

@Client.on_message(filters.command("user") & filters.user(Config.ADMIN))
async def get_user_details(client, message):
    args = message.text.split(" ", 1)
    if len(args) != 2:
        await message.reply("Please provide a user ID or username.")
        return

    user_identifier = args[1]

    try:
        if user_identifier.isdigit():
            user_id = int(user_identifier)
            user = await client.get_users(user_id)
        else:
            user = await client.get_users(user_identifier)
            user_id = user.id if user else None

        if not user_id or not user:
            await message.reply("Invalid user ID or username.")
            return

        user_db = await db.user_col.find_one({"_id": user_id})

        if not user_db:
            await message.reply("User not found in the database.")
            return

        # Fetching all necessary data
        dump_enabled = "Enabled" if user_db.get('dump_enabled', False) else "Disabled"
        forward_mode = user_db.get('forward_mode', 'N/A')
        auto_rename_pattern = await db.get_format_template(user_id) or 'N/A'
        user_caption = await db.get_caption(user_id) or 'N/A'
        file_count = await db.get_file_count(user_id)
        referral_count = await db.get_referral_count(user_id) or 0 # Total referrals
        referrer_id = await db.get_referrer(user_id)
        if referrer_id:
            referrer_user = await client.get_users(referrer_id)
            referrer_mention = referrer_user.mention
        else:
            referrer_mention = "N/A"
        
        thumbnail_file_id = await db.get_thumbnail(user_id) or DEFAULT_THUMBNAIL_URL

        # Construct user details with mention
        user_details = (
            f"**User Details [`{user_id}`]**\n\n"
            f"👤 **User**: [{user.first_name}](tg://user?id={user_id})\n"  # Added user mention
            f"🔗 **Referred By**: {referrer_mention}\n"
            f"⭐️ **Referral Points**: {user_db.get('referral_points', 0)}\n"
            f"🔢 **Total Referrals**: {referral_count}\n"
            f"📂 **Total Renamed**: {file_count} Files\n"
            f"🗃 **Metadata**: {'Enabled' if user_db.get('metadata', False) else 'Disabled'}\n"
            f"🗂️ **Dump mode**: {dump_enabled}\n"
            f"📤 **Forward Mode**: `{forward_mode}`\n"
            f"📝 **Caption**: {user_caption}\n"
            f"🔄 **Auto Rename Setup**: `{auto_rename_pattern}`"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📄 Metadata Details", callback_data=f"metadata_{user_id}")],
                [InlineKeyboardButton("🔑 Authorization Details", callback_data=f"auth_{user_id}")]
            ]
        )

        if thumbnail_file_id:
            await message.reply_photo(thumbnail_file_id, caption=user_details, reply_markup=keyboard)
        else:
            await message.reply(user_details, reply_markup=keyboard)

    except Exception as e:
        await message.reply(f"An error occurred: {e}")

@Client.on_callback_query(filters.regex(r"metadata_\d+"))
async def show_metadata_details(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])

    try:
        metadata = await db.get_metadata(user_id)

        if not metadata:
            await callback_query.message.edit("No metadata found for this user.")
            return

        metadata_details = (
            f"**Metadata Details**\n\n"
            f"🎬 **Title**: {metadata.get('title', 'N/A')}\n"
            f"✍️ **Author**: {metadata.get('author', 'N/A')}\n"
            f"🎨 **Artist**: {metadata.get('artist', 'N/A')}\n"
            f"📜 **Subtitle**: {metadata.get('subtitle', 'N/A')}\n"
            f"🎵 **Audio**: {metadata.get('audio', 'N/A')}\n"
            f"📹 **Video**: {metadata.get('video', 'N/A')}"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 Back", callback_data=f"back_{user_id}")],
                [InlineKeyboardButton("🔑 Authorization Details", callback_data=f"auth_{user_id}")]
            ]
        )

        await callback_query.message.edit(metadata_details, reply_markup=keyboard)

    except Exception as e:
        await callback_query.message.edit(f"An error occurred: {e}")

@Client.on_callback_query(filters.regex(r"auth_\d+"))
async def show_authorization_details(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])

    try:
        # Check if the user is authorized
        authorized = await db.is_user_authorized(user_id)
        if authorized:
            # Fetch authorization details
            expiry_time = await db.get_authorization_expiry(user_id)
            duration_td = expiry_time - datetime.utcnow()
            user_details = await client.get_users(user_id)

            check_message = (f"**Authorization Details:**\n\n"
                             f"**👤 User Mention:** {user_details.mention}\n\n"
                             f"**⏳ Auth Duration:** `{str(duration_td)}`\n"
                             f"**🎗️ Auth Start:** `{format_timestamp(expiry_time - duration_td)}`\n"
                             f"**🏷️ Auth Expiry:** `{format_timestamp(expiry_time)}`")
        else:
            check_message = f"❌ User with ID `{user_id}` is not authorized."

        # Buttons to go back to the metadata or user details
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔙 Back", callback_data=f"back_{user_id}")],
                [InlineKeyboardButton("📄 Metadata Details", callback_data=f"metadata_{user_id}")]
            ]
        )

        # Check if the user has a thumbnail
        thumbnail_file_id = await db.get_thumbnail(user_id)

        if thumbnail_file_id:
            await callback_query.message.edit_media(
                media=InputMediaPhoto(thumbnail_file_id, caption=check_message),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.edit(
                text=check_message,
                reply_markup=keyboard
            )

    except Exception as e:
        await callback_query.message.edit(f"An error occurred: {e}")

@Client.on_callback_query(filters.regex(r"back_\d+"))
async def go_back(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])

    try:
        user_db = await db.user_col.find_one({"_id": user_id})

        if not user_db:
            await callback_query.message.edit("User not found in the database.")
            return

        # Fetch user details
        user = await client.get_users(user_id)

        dump_enabled = "Enabled" if user_db.get('dump_enabled', False) else "Disabled"
        forward_mode = user_db.get('forward_mode', 'N/A')
        auto_rename_pattern = await db.get_format_template(user_id) or 'N/A'
        user_caption = await db.get_caption(user_id) or 'N/A'
        referral_count = await db.get_referral_count(user_id) or 0
        file_count = await db.get_file_count(user_id)
        referrer_id = await db.get_referrer(user_id)
        if referrer_id:
            referrer_user = await client.get_users(referrer_id)
            referrer_mention = referrer_user.mention
        else:
            referrer_mention = "N/A"
        
        thumbnail_file_id = await db.get_thumbnail(user_id) or DEFAULT_THUMBNAIL_URL

        # Construct user details with mention
        user_details = (
            f"**User Details [`{user_id}`]**\n\n"
            f"👤 **User**: [{user.first_name}](tg://user?id={user_id})\n"  # Added user mention
            f"🔗 **Referred By**: {referrer_mention}\n"
            f"⭐️ **Referral Points**: {user_db.get('referral_points', 0)}\n"
            f"🔢 **Total Referrals**: {referral_count}\n"
            f"📂 **Total Renamed**: {file_count} Files\n"
            f"🗃 **Metadata**: {'Enabled' if user_db.get('metadata', False) else 'Disabled'}\n"
            f"🗂️ **Dump mode**: {dump_enabled}\n"
            f"📤 **Forward Mode**: `{forward_mode}`\n"
            f"📝 **Caption**: {user_caption}\n"
            f"🔄 **Auto Rename Setup**: `{auto_rename_pattern}`"
        )
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📄 Metadata Details", callback_data=f"metadata_{user_id}")],
                [InlineKeyboardButton("🔑 Authorization Details", callback_data=f"auth_{user_id}")]
            ]
        )

        if thumbnail_file_id:
            await callback_query.message.edit_media(
                media=InputMediaPhoto(thumbnail_file_id, caption=user_details),
                reply_markup=keyboard
            )
        else:
            await callback_query.message.edit(
                text=user_details,
                reply_markup=keyboard
            )

    except Exception as e:
        await callback_query.message.edit(f"An error occurred: {e}")
