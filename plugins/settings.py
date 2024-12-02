from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from config import Config
from helper.database import db

SETTINGS_IMAGE_URL = "https://graph.org/file/e2f0c171342350a168f25.jpg"

@Client.on_message(filters.command("settings"))
async def settings_command(client: Client, message: Message):
    user_id = message.from_user.id
    user_settings = await get_user_settings(user_id)
    caption = generate_settings_caption(user_settings)

    buttons = create_settings_buttons(user_settings)

    await message.reply_photo(
        SETTINGS_IMAGE_URL,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


def generate_settings_caption(settings):
    metadata_status = "Enabled" if settings['metadata'] else "Disabled"
    dump_status = "Enabled" if settings['dump_files'] else "Disabled"
    dump_channel = settings['dump_channel'] if settings['dump_channel'] else "Not Set"
    thumbnail_status = "Set" if settings['thumbnail_set'] else "Not Set"
    media_preference = settings['media_preference'].capitalize()
    caption_status = "Set" if settings['caption_set'] else "Not Set" 

    return (
        f"🛠️ <u>**Your Current Settings**</u> 🛠️\n\n"
        f"📁 Metadata: `{metadata_status}`\n"
        f"📤 Dump Files: `{dump_status}`\n"
        f"📺 Dump Channel: `{dump_channel}`\n"
        f"🖼️ Thumbnail: `{thumbnail_status}`\n"
        f"📩 Media Preference: `{media_preference}`\n"
        f"📝 Caption: `{caption_status}`"
    )


def create_settings_buttons(settings):
    buttons = [
        [
            InlineKeyboardButton(f"Media Preference - {settings['media_preference'].capitalize()}", callback_data="toggle_media_preference")                      
        ],
        [
            InlineKeyboardButton("Dump", callback_data="dump_settings"),
            InlineKeyboardButton("Metadata", callback_data="metadata_settings")
        ],
        [
            InlineKeyboardButton("Thumbnail", callback_data="thumbnail"),
            InlineKeyboardButton("Caption", callback_data="caption")
        ],
        [
            InlineKeyboardButton("Back", callback_data="commands")
        ]
    ]
    return buttons


async def get_user_settings(user_id):
    dump_files = await db.get_dump_files(user_id)
    dump_channel = await db.get_dump_channel(user_id)
    metadata_enabled = await db.get_meta(user_id)
    thumbnail_set = await db.get_thumbnail(user_id) is not None
    caption_set = await db.get_caption(user_id) is not None
    media_preference = await db.get_media_preference(user_id) or "document"  # Default to 'document' if not set
    
    return {
        "dump_files": dump_files,
        "dump_channel": dump_channel,
        "metadata": metadata_enabled,
        "thumbnail_set": thumbnail_set,
        "media_preference": media_preference,
        "caption_set": caption_set
    }


@Client.on_callback_query(filters.regex("^toggle_"))
async def on_callback_query(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data

    if data == "toggle_media_preference":
        await toggle_media_preference(user_id, callback_query)

    # Update the settings message with the new values
    updated_settings = await get_user_settings(user_id)
    updated_caption = generate_settings_caption(updated_settings)
    updated_buttons = create_settings_buttons(updated_settings)

    await callback_query.edit_message_caption(
        caption=updated_caption,
        reply_markup=InlineKeyboardMarkup(updated_buttons)
    )


@Client.on_callback_query(filters.regex("^settings$"))
async def settings_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    user_settings = await get_user_settings(user_id)
    caption = generate_settings_caption(user_settings)

    buttons = create_settings_buttons(user_settings)

    await callback_query.message.edit_caption(
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


async def toggle_media_preference(user_id, callback_query: CallbackQuery):
    current_preference = await db.get_media_preference(user_id) or "document"
    preferences = ["document", "video", "audio"]
    new_preference = preferences[(preferences.index(current_preference) + 1) % len(preferences)]
    await db.set_media_preference(user_id, new_preference)
    await callback_query.answer(f"Your media preference has changed to {new_preference}.", show_alert=True)
    
