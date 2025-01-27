from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from helper.database import db
from config import Config, Txt
import asyncio

@Client.on_message(filters.private & filters.command(["tutorial"]))
async def tutorial(client, message):
    await message.reply_text(
        text=Txt.FILE_NAME_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Aᴅᴍɪɴ", url="https://t.me/ElitesCrewBot"),
             InlineKeyboardButton("Dᴇᴍᴏ", url="https://t.me/Elites_Assistance")]
        ])
    )

@Client.on_message(filters.private & filters.command(["premium"]))
async def premium(client, message):
    user_id = message.from_user.id
    await message.reply_text(
        text=Txt.PREMIUM_TXT.format(message.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Activate Premium ⚡", url="https://t.me/Elites_Assistance")]
        ])
    )

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id
    format_template = await db.get_format_template(user_id) or "None set"

    def send_usage_message(format_template):
        return (
            "Please add a new file name after /autorename command.\n\n"
            "You can use the following variables in your format template:\n"
            "• {title} - for anime name\n"
            "• {season} - for anime season number\n"
            "• {episode} - for anime episode number\n"
            "• {audio} - for anime language\n"
            "• {quality} - for video resolution\n"
            "• {volume} - for manga volume number\n"
            "• {chapter} - for manga chapter number\n\n"
            "<b>Example 1:</b> <code>/autorename S{season} E{episode} - {title} [{audio}] [{quality}] @Anime_Elites</code>\n\n"
            "<b>Example 2:</b> <code>/autorename Vol{volume} Ch{chapter} - {title} @Manga_Elites</code>\n\n"
            f"<b>Your current format:</b> <code>{format_template}</code>"
        )

    try:
        command_parts = message.text.split(None, 1)  # Split by whitespace after command
        if len(command_parts) < 2:
            await message.reply_text(send_usage_message(format_template))
            return
        
        format_template = command_parts[1].strip()
        if not format_template or len(format_template) < 3:
            await message.reply_text("The template is too short. Please provide a more detailed format.")
            return

        # Save the new format template to the database
        await db.set_format_template(user_id, format_template)

        await message.reply_text(
            f"Your autorename template has been saved!!\n\nYour template : <code>{format_template}</code>..."
        )
    except FloodWait as e:
        await asyncio.sleep(e.x)
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")
        # Consider logging the error if needed
        print(f"Error in auto_rename_command: {e}")


@Client.on_message(filters.private & filters.command("setmediatype"))
async def mode_command(client, message):
    user_id = message.from_user.id

    try:
        # Retrieve the current media preference from the database
        media_preference = await db.get_media_preference(user_id)

        # Determine the state of the buttons
        document_button_text = "Document ✅" if media_preference == "document" else "Document"
        video_button_text = "Video ✅" if media_preference == "video" else "Video"
        audio_button_text = "Audio ✅" if media_preference == "audio" else "Audio"

        # Create the inline keyboard with buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(document_button_text, callback_data="setmedia_document")],
            [InlineKeyboardButton(video_button_text, callback_data="setmedia_video")],
            [InlineKeyboardButton(audio_button_text, callback_data="setmedia_audio")]
        ])

        await message.reply_text("Choose your preferred media type:", reply_markup=keyboard)
    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")

@Client.on_callback_query(filters.regex(r"^setmedia_(document|video|audio)$"))
async def callback_query_handler(client, callback_query):
    user_id = callback_query.from_user.id
    media_type = callback_query.data.split("_")[1]

    try:
        # Save the preferred media type to the database
        await db.set_media_preference(user_id, media_type)

        # Update the button text
        document_button_text = "Document ✅" if media_type == "document" else "Document"
        video_button_text = "Video ✅" if media_type == "video" else "Video"
        audio_button_text = "Audio ✅" if media_type == "audio" else "Audio"

        # Create the updated inline keyboard with buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(document_button_text, callback_data="setmedia_document")],
            [InlineKeyboardButton(video_button_text, callback_data="setmedia_video")],
            [InlineKeyboardButton(audio_button_text, callback_data="setmedia_audio")]
        ])

        await callback_query.message.edit_text("Choose your preferred media type:", reply_markup=keyboard)
        await callback_query.answer(f"Media preference set to: {media_type.capitalize()}")
    except Exception as e:
        await callback_query.message.edit_text(f"An unexpected error occurred: {e}")


from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters

@Client.on_message(filters.command("mode") & filters.private)
async def set_mode(client, message):
    user_id = message.from_user.id

    # Fetch the current mode from the database
    current_mode = await db.get_mode(user_id)
    if not current_mode:
        current_mode = "Auto Rename"  # Default mode is Auto Rename

    # Prepare the inline buttons with indicators
    manual_rename_btn = "✅ Manual Renaming" if current_mode == "Manual Rename" else "Manual Renaming"
    auto_rename_btn = "✅ Auto Renaming" if current_mode == "Auto Rename" else "Auto Renaming"

    buttons = [
        [
            InlineKeyboardButton(manual_rename_btn, callback_data="set_mode_manual"),
            InlineKeyboardButton(auto_rename_btn, callback_data="set_mode_auto"),
        ]
    ]

    # Send the message with buttons
    await message.reply_text(
        "Select your preferred mode:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_callback_query(filters.regex("set_mode_"))
async def handle_mode_selection(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data

    # Determine the selected mode
    if data == "set_mode_manual":
        new_mode = "Manual Rename"
    elif data == "set_mode_auto":
        new_mode = "Auto Rename"
    else:
        await callback_query.answer("Invalid selection.", show_alert=True)
        return

    # Update the mode in the database
    await db.set_user_attr(user_id, "mode", new_mode)

    # Prepare the updated buttons
    manual_rename_btn = "✅ Manual Renaming" if new_mode == "Manual Rename" else "Manual Renaming"
    auto_rename_btn = "✅ Auto Renaming" if new_mode == "Auto Rename" else "Auto Renaming"

    buttons = [
        [
            InlineKeyboardButton(manual_rename_btn, callback_data="set_mode_manual"),
            InlineKeyboardButton(auto_rename_btn, callback_data="set_mode_auto"),
        ]
    ]

    # Edit the original message with updated buttons
    await callback_query.message.edit_text(
        "Select your preferred mode:",
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    # Notify the user of the updated mode
    await callback_query.answer(f"Mode updated to {new_mode}.", show_alert=True)
