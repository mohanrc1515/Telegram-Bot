from pyrogram import Client, filters, enums
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import db
from pyromod.exceptions import ListenerTimeout
from config import Txt
import asyncio

handler_dict = {}
default_values = {
    "title": "By @Elites_Bots",
    "author": "@Elites_Bots",
    "artist": "@Elites_Bots",
    "subtitle": "@Elites_Bots",
    "audio": "@Elites_Bots",
    "video": "Encoded By @Elites_Bots"
}

@Client.on_message(filters.command("metadata") & filters.private)
async def metadata_command(client: Client, message: Message):
    user_data = await db.get_meta(message.from_user.id)
    meta_status = "Enabled" if user_data else "Disabled"
    
    # Define the metadata settings text
    text = f"<b>Your Metadata Settings:</b>\n\n<b>Metadata Status:</b> {meta_status}"
    
    # Create buttons
    buttons = [
        [InlineKeyboardButton("Metadata", callback_data="toggle_metadata"),
         InlineKeyboardButton(f"{meta_status}", callback_data="toggle_meta")],
        [InlineKeyboardButton("Set Metadata", callback_data="set_metadata"),
         InlineKeyboardButton("View Metadata", callback_data="view_metadata")],
        [InlineKeyboardButton("Back", callback_data="settings")]
    ]
    
    # Define the reply markup
    reply_markup = InlineKeyboardMarkup(buttons)
    
    # Send the image with the metadata text and buttons
    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/w_m.jpg",
        caption=text,
        reply_markup=reply_markup
    )
    

@Client.on_callback_query(filters.regex(r'^metadata_settings'))
async def handle_metadata_settings_callback(bot: Client, callback_query):
    user_data = await db.get_meta(callback_query.from_user.id)
    meta_status = "Enabled" if user_data else "Disabled"

    text = f"<b>Your Metadata Settings:</b>\n\n<b>Metadata Status:</b> {meta_status}"

    buttons = [
        [InlineKeyboardButton("Metadata", callback_data="toggle_metadata"),
         InlineKeyboardButton(f"{meta_status}", callback_data="toggle_meta")],
        [InlineKeyboardButton("Set Metadata", callback_data="set_metadata"),
         InlineKeyboardButton("View Metadata", callback_data="view_metadata")],
        [InlineKeyboardButton("Back", callback_data="settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await callback_query.message.edit(text=text, reply_markup=reply_markup)
    await callback_query.answer()  # Acknowledge the callback

@Client.on_callback_query(filters.regex('.*?(toggle_meta|set_meta|update_var_|empty_var_|edit_var_|reset_var_|view_metadata|set_metadata|home_meta).*?'))
async def query_metadata(bot: Client, query: CallbackQuery):

    data = query.data
    user_id = query.from_user.id

    if data.startswith('toggle_meta'):
        meta_mode = await db.get_meta(user_id)
        meta_mode = not meta_mode
        await db.set_meta(user_id, meta_mode)
        reply_markup, text = await toggle_mode_buttons(user_id)
        await query.message.edit_text(text=text, reply_markup=reply_markup)
    
    elif data.startswith('toggle_metadata'):
        meta_mode = await db.get_meta(user_id)
        meta_mode = not meta_mode
        await db.set_meta(user_id, meta_mode)
        reply_markup, text = await toggle_mode_buttons(user_id)
        await query.message.edit_text(text=text, reply_markup=reply_markup)
    
    elif data == "view_metadata":
        metadata = await db.get_metadata(user_id)

        # Use an empty string if any metadata field is not set
        sub_title = metadata.get("title", "")
        sub_author = metadata.get("author", "")
        sub_subtitle = metadata.get("subtitle", "")
        sub_audio = metadata.get("audio", "")
        sub_video = metadata.get("video", "")
        sub_artist = metadata.get("artist", "")

        # Display metadata settings
        metadata_text = (
            f"<b>㊂ Metadata Settings :</b>\n\n"
            f"<b>Title:</b> <code>{sub_title}</code>\n"
            f"<b>Author:</b> <code>{sub_author}</code>\n"
            f"<b>Subtitle:</b> <code>{sub_subtitle}</code>\n"
            f"<b>Audio:</b> <code>{sub_audio}</code>\n"
            f"<b>Video:</b> <code>{sub_video}</code>\n"
            f"<b>Artist:</b> <code>{sub_artist}</code>\n"
        )

        buttons = [
            [InlineKeyboardButton("Back", callback_data="metadata_settings"),
             InlineKeyboardButton("Close", callback_data="close")]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=metadata_text,
            reply_markup=reply_markup
        )

    
    elif data == "set_metadata":
        handler_dict.pop(user_id, None)
        await show_metadata_buttons(query.message, page=1)

    elif data.startswith("update_var_"):
        variable_name = data[len("update_var_"):]
        await handle_update_var(bot, query, variable_name)

    elif data.startswith("empty_var_"):
        variable_name = data[len("empty_var_"):]    
        handler_dict.pop(user_id, None)   
        await db.update_metadata(user_id, variable_name, "")   
        await query.answer(f"The value for {variable_name.capitalize()} has been cleared ✅", show_alert=True)
        await handle_update_var(bot, query, variable_name)
      
    elif data.startswith("edit_var_"):
        variable_name = data[len("edit_var_"):]
        await handle_edit_var(bot, query, variable_name)

    elif data.startswith("reset_var_"):
        variable_name = data[len("reset_var_"):]
        handler_dict.pop(user_id, None)
        default_value = default_values.get(variable_name)
        await db.update_metadata(user_id, variable_name, default_value)
        await query.answer(f"The Value For {variable_name} Has Been Reset To Its Default Value ✅", show_alert=True)
        await handle_update_var(bot, query, variable_name)


async def toggle_mode_buttons(user_id):
    user_data = await db.get_meta(user_id)
    meta_status = "Enabled" if user_data else "Disabled"

    text = f"<b>Your Metadata Settings:</b>\n\n<b>Metadata Status:</b> {meta_status}"

    buttons = [
        [InlineKeyboardButton("Metadata", callback_data="toggle_metadata"),
         InlineKeyboardButton(f"{meta_status}", callback_data="toggle_meta")],
        [InlineKeyboardButton("Set Metadata", callback_data="set_metadata"),
         InlineKeyboardButton("View Metadata", callback_data="view_metadata")],
        [InlineKeyboardButton("Back", callback_data="settings")]
    ]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    return reply_markup, text  # Return both reply_markup and text for editing

async def show_metadata_buttons(message, page):
    variable_names = [
        "Title", "Author", "Artist", "Audio", "Video", "Subtitle"
    ]
    user_id = message.from_user.id
    handler_dict[user_id] = False
    buttons_per_row = 3
    rows = 2
    buttons_per_page = buttons_per_row * rows
    total_pages = (len(variable_names) + buttons_per_page - 1) // buttons_per_page

    start = (page - 1) * buttons_per_page
    end = min(start + buttons_per_page, len(variable_names))
    buttons_list = variable_names[start:end]

    buttons = [
        [InlineKeyboardButton(variable, callback_data=f"update_var_{variable.lower()}") for variable in buttons_list[i:i + buttons_per_row]]
        for i in range(0, len(buttons_list), buttons_per_row)
    ]

    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton("Previous", callback_data=f"pagination_{page - 1}"))
    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton("Next", callback_data=f"pagination_{page + 1}"))

    buttons.append(navigation_buttons)
    buttons.append([InlineKeyboardButton("Back", callback_data="metadata_settings"), InlineKeyboardButton("Close", callback_data="close")])

    text = f"<b>Custom Metadata | Page: {page}/{total_pages}</b>\n\n"
    await message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


def get_edit_var_text(variable_name):
    descriptions = {
        "title": "Descriptive title of the media.",
        "author": "Creator or owner of the media.",
        "artist": "Associated artist (e.g., musician, illustrator).",
        "audio": "Title or description of audio content.",
        "video": "Description of video content.",
        "subtitle": "Title of subtitle content."
    }
    return descriptions.get(variable_name, "No Description Available.")


async def handle_update_var(client, query, variable_name):
    edit_text = get_edit_var_text(variable_name)
    text = f"<b>Variable : {variable_name.capitalize()}</b>\n\nDescription : {edit_text}"

    user_id = query.from_user.id
    handler_dict[user_id] = False
    config_value = await db.get_metadata(user_id)
    current_value = config_value.get(variable_name) if config_value else None
    if current_value:
        text += f"\n\n<b>Current Value :</b> <code>{current_value}</code>\n\n"

    buttons = [
        [InlineKeyboardButton("Edit", callback_data=f"edit_var_{variable_name}"),
         InlineKeyboardButton("Reset", callback_data=f"reset_var_{variable_name}"),
         InlineKeyboardButton("Empty", callback_data=f"empty_var_{variable_name}")],  # New "Empty" button
        [InlineKeyboardButton("Back", callback_data="set_metadata"),
         InlineKeyboardButton("Close", callback_data="close")],
    ]

    # Check if the new content is different from the existing content
    if query.message.text != text:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await query.answer("No changes detected. Message not modified.", show_alert=True)
    

async def handle_edit_var(client, query, variable_name):
    user_id = query.from_user.id
    handler_dict[user_id] = True

    edit_text = get_edit_var_text(variable_name)
    text = f"<b>Variable: {variable_name.capitalize()}</b>\n\nDescription: {edit_text}"

    config_value = await db.get_metadata(user_id)
    current_value = config_value.get(variable_name) if config_value else None
    if current_value:
        text += f"\n\n<b>Current Value :</b> {current_value}\n\n"

    text += "Please Enter The New Value Within 60 Seconds."

    buttons = [
        [InlineKeyboardButton("Stop Edit", callback_data=f"update_var_{variable_name}"),
         InlineKeyboardButton("Reset", callback_data=f"reset_var_{variable_name}")],
        [InlineKeyboardButton("Home", callback_data="set_metadata"),
         InlineKeyboardButton("Close", callback_data="close")]
    ]

    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

    try:
        new_message = await asyncio.wait_for(client.listen(user_id), timeout=60)

        if new_message and handler_dict.get(user_id) is True:
            if new_message.text:
                new_value = new_message.text
                if new_value.startswith("/"):
                    await new_message.delete()
                else:
                    await db.update_metadata(user_id, variable_name, new_value)
                    await new_message.delete()
                    await handle_update_var(client, query, variable_name)
            else:
                await query.answer(text="Please Provide Text Input. Media Files Are Not Accepted ❌", show_alert=True)
                await handle_update_var(client, query, variable_name)
        elif new_message:
            await new_message.delete()

    except asyncio.TimeoutError:
        await handle_update_var(client, query, variable_name)
    finally:
        handler_dict[user_id] = False
    
