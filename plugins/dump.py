from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from helper.database import db
from config import Config, Txt
from helper.extraction import extract_season, extract_episode_number, extract_chapter_number, extract_volume_number

# Global dicts to manage user settings and sequence mode
user_sequence_mode = {}
sequencing_queue = {}


@Client.on_message(filters.command("dumpsettings") & filters.private)
async def dump_settings_command(client, message: Message):
    user_id = message.from_user.id

    # Get the dump settings for the user
    dump_files_status = "Enabled" if await db.get_dump_files(user_id) else "Disabled"
    forward_mode = await db.get_forward_mode(user_id)
    channel_id = await db.get_dump_channel(user_id)

    # Prepare the response text
    reply_text = (
        "㊂ Dump Settings:\n\n"
        f"๏ Dump Files ‣ <code>{dump_files_status}</code>\n"
        f"๏ Forward Mode ‣ <code>{forward_mode}</code>\n"
        f"๏ Connected Channel ‣ <code>{channel_id}</code>"
    )

    # Inline keyboard for interacting with settings
    keyboard = [
        [
            InlineKeyboardButton("How to Set Dump", callback_data="dump_help")
        ],
        [
            InlineKeyboardButton("Dump Files", callback_data="toggle_dump_files"),
            InlineKeyboardButton(dump_files_status, callback_data="toggle_dump_files_status")
        ],
        [
            InlineKeyboardButton("Forward Mode", callback_data="toggle_forward_mode"),
            InlineKeyboardButton(forward_mode, callback_data="toggle_forward_mode_status")
        ],
        [
            InlineKeyboardButton("Back", callback_data="settings")
        ]
    ]
    # Send the image along with the settings
    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/w_X.jpg",
        caption=reply_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

@Client.on_callback_query(filters.regex("dump_settings"))
async def dump_settings(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    dump_files_status = "Enabled" if await db.get_dump_files(user_id) else "Disabled"
    forward_mode = await db.get_forward_mode(user_id)
    channel_id = await db.get_dump_channel(user_id)

    reply_text = (
        "㊂ Dump Settings:\n\n"
        f"๏ Dump Files ‣ <code>{dump_files_status}</code>\n"
        f"๏ Forward Mode ‣ <code>{forward_mode}</code>\n"
        f"๏ Connected Channel ‣ <code>{channel_id}</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("How to Set Dump", callback_data="dump_help")
        ],
        [   
            InlineKeyboardButton("Dump Files", callback_data="toggle_dump_files"),
            InlineKeyboardButton(dump_files_status, callback_data="toggle_dump_files_status")
        ],
        [
            InlineKeyboardButton("Forward Mode", callback_data="toggle_forward_mode"),
            InlineKeyboardButton(forward_mode, callback_data="toggle_forward_mode_status")
        ],
        [
            InlineKeyboardButton("Back", callback_data="settings")
        ]
    ]

    await callback_query.message.edit_text(
        text=reply_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()


# Callback to toggle Dump Files setting
@Client.on_callback_query(filters.regex("toggle_dump_files"))
async def toggle_dump_files(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    # Check if the user has set a dump channel
    dump_channel = await db.get_dump_channel(user_id)
    if not dump_channel:
        return await callback_query.message.edit_text(
            text="You must set a dump channel before enabling dump mode. Use the /dump command to set a channel.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Back", callback_data="dump_settings")]
            ])
        )

    current_dump_files = await db.get_dump_files(user_id)
    new_dump_files_status = not current_dump_files
    
    await db.set_dump_files(user_id, new_dump_files_status)

    await update_dump_message(client, callback_query)



# Callback to toggle Forward Mode setting
@Client.on_callback_query(filters.regex("toggle_forward_mode"))
async def toggle_forward_mode(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    current_forward_mode = await db.get_forward_mode(user_id)
    new_forward_mode = 'Sequence' if current_forward_mode == 'Normal' else 'Normal'
    
    await db.set_forward_mode(user_id, new_forward_mode)
    
    # Update the text and buttons on the same message
    await update_dump_message(client, callback_query)


# Function to update the dump message text and buttons
async def update_dump_message(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    
    dump_files_status = "Enabled" if await db.get_dump_files(user_id) else "Disabled"
    forward_mode = await db.get_forward_mode(user_id)
    channel_id = await db.get_dump_channel(user_id)

    reply_text = (
        "㊂ Dump Settings:\n\n"
        f"๏ Dump Files ‣ <code>{dump_files_status}</code>\n"
        f"๏ Forward Mode ‣ <code>{forward_mode}</code>\n"
        f"๏ Connected Channel ‣ <code>{channel_id}</code>"
    )

    keyboard = [
        [
            InlineKeyboardButton("How to Set Dump", callback_data="dump_help")
        ],
        [   
            InlineKeyboardButton("Dump Files", callback_data="toggle_dump_files"),
            InlineKeyboardButton(dump_files_status, callback_data="toggle_dump_files_status")
        ],
        [
            InlineKeyboardButton("Forward Mode", callback_data="toggle_forward_mode"),
            InlineKeyboardButton(forward_mode, callback_data="toggle_forward_mode_status")
        ],
        [
            InlineKeyboardButton("Back", callback_data="settings")
        ]
    ]

    await callback_query.message.edit_text(
        text=reply_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await callback_query.answer()


# Callback to show dump help
@Client.on_callback_query(filters.regex('dump_help'))
async def dump_help(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.DUMP_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="dump_settings"), InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url='https://t.me/Elites_Assistance')]
        ])            
    )
    await query.answer()


# /channel command to set the dump channel
@Client.on_message(filters.command("dump") & filters.private)
async def set_dump_channel(client, message: Message):
    user_id = message.from_user.id
    try:
        channel_id = int(message.text.split()[1])
        
        # Check if the bot can send messages to the specified channel
        try:
            await client.get_chat_member(channel_id, "self")
        except Exception as e:
            return await message.reply_text(f"Failed to access the channel: {e}")
        
        await db.set_dump_channel(user_id, channel_id)
        await message.reply_text(f"Dump Channel set to: {channel_id}")
    except (IndexError, ValueError):
        await message.reply_text("Please provide a valid channel ID.\n\nEg : <code>/dump -100123456789 </code>")


@Client.on_message(filters.command("startdump") & filters.private)
async def start_dump(client, message: Message):
    user_id = message.from_user.id
    replied = message.reply_to_message
    if not replied:
        await message.reply_text(
            "Dear user, please reply to the **text**, **image**, or **sticker** "
            "you want to set as the start message for dumping. Use the placeholders:\n\n"
            "- **{quality}**: Content quality (e.g., 1080p)\n"
            "- **{title}**: Series title\n"
            "- **{season}**: Season number\n"
            "- **{firstepisode}**: First episode\n"
            "- **{lastepisode}**: Last episode"
        )
        return
    # Check if the replied message is a sticker, image, or text
    if replied.sticker:
        await db.set_start_message(user_id, sticker_id=replied.sticker.file_id, text=replied.sticker.caption or "")
        await message.reply_text("Start message set with a sticker.")
    elif replied.photo:
        await db.set_start_message(user_id, image_id=replied.photo.file_id, text=replied.photo.caption or "")
        await message.reply_text("Start message set with an image.")
    elif replied.text:
        await db.set_start_message(user_id, text=replied.text)
        await message.reply_text(f"Start message set:\n{replied.text}")
    else:
        await message.reply_text("Invalid format. Please reply to a text, image, or sticker.")

@Client.on_message(filters.command("enddump") & filters.private)
async def end_dump(client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(
        "Please send the **start message** for each season. "
        "You have the flexibility to send the message as plain text, an image (with or without a caption), or a sticker. "
        "You can also make use of the following placeholders to dynamically modify the message:\n\n"
        "- **{quality}**: The quality of the content (e.g., 1080p)\n"
        "- **{title}**: The title of the series\n"
        "- **{season}**: The season number\n"
        "- **{firstepisode}**: The first episode number\n"
        "- **{lastepisode}**: The last episode number\n\n"
        "**Example Format**:\n"
        "✧ Season {season} : [{firstepisode} - {lastepisode}]\n"
        "✧ {quality} [English + Japanese]"
    )

    response = await client.listen(message.chat.id)

    # Determine if the response is a sticker, image, or text
    if response.sticker:
        await db.set_end_message(user_id, sticker_id=response.sticker.file_id, text=response.caption or "")
        await message.reply_text("End message set with a sticker.")
    elif response.photo:
        await db.set_end_message(user_id, image_id=response.photo.file_id, text=response.caption or "")
        await message.reply_text("End message set with an image.")
    elif response.text:
        await db.set_end_message(user_id, text=response.text)
        await message.reply_text(f"End message set:\n{response.text}")
    else:
        await message.reply_text("Invalid format. Please send a text, image, or sticker.")

@Client.on_message(filters.command("dlt_startdump") & filters.private)
async def delete_start_dump(client, message: Message):
    user_id = message.from_user.id
    await db.delete_start_message(user_id)
    await message.reply_text("Start message deleted.")

@Client.on_message(filters.command("dlt_enddump") & filters.private)
async def delete_end_dump(client, message: Message):
    user_id = message.from_user.id
    await db.delete_end_message(user_id)
    await message.reply_text("End message deleted.")

@Client.on_message(filters.command("dumptext"))
async def show_dump_text(client, message: Message):
    user_id = message.from_user.id

    # Get start and end messages from the database
    start_message = await db.get_start_message(user_id) or {"text": "No start message set."}
    end_message = await db.get_end_message(user_id) or {"text": "No end message set."}

    response_text = (
        f"**✨ <u>Start Message:</u>**\n\n"
        f"📜 **Text:** {start_message.get('text', 'N/A')}\n"
        f"🖼️ **Sticker:** {'✅ Yes' if start_message.get('sticker_id') else '❌ No'}\n"
        f"📷 **Image:** {'✅ Yes' if start_message.get('image_id') else '❌ No'}\n\n"
        f"**🌟 <u>End Message</u>:**\n\n"
        f"📜 **Text:** {end_message.get('text', 'N/A')}\n"
        f"🖼️ **Sticker:** {'✅ Yes' if end_message.get('sticker_id') else '❌ No'}\n"
        f"📷 **Image:** {'✅ Yes' if end_message.get('image_id') else '❌ No'}"
    )

    await message.reply_text(response_text)


@Client.on_message(filters.command("dumptextmode"))
async def dumptextmode(client, message: Message):
    user_id = message.from_user.id

    # Retrieve current user preference from the database
    current_preference = await db.get_user_preference(user_id)  # Assume 'db' handles DB operations

    # Define the button labels and callback data
    button_season = InlineKeyboardButton(f"Season ✅" if current_preference == 'season' else "Season", callback_data="season")
    button_quality = InlineKeyboardButton(f"Quality ✅" if current_preference == 'quality' else "Quality", callback_data="quality")
    button_both = InlineKeyboardButton(f"Both ✅" if current_preference == 'both' else "Both", callback_data="both")

    # Create the buttons layout
    buttons = InlineKeyboardMarkup([[button_season, button_quality, button_both]])

    # Send a message with the buttons
    await message.reply_text(
        "Please select your preferred mode:",
        reply_markup=buttons
    )

@Client.on_callback_query(filters.regex('^(season|quality|both)$'))
async def handle_switch_callback(client, callback_query):
    user_id = callback_query.from_user.id
    selected_mode = callback_query.data

    # Update the user's preference in the database
    await db.set_user_preference(user_id, selected_mode)

    # Retrieve the updated preference to re-render buttons
    current_preference = await db.get_user_preference(user_id)

    # Update buttons based on the selected mode
    button_season = InlineKeyboardButton(f"Season ✅" if current_preference == 'season' else "Season", callback_data="season")
    button_quality = InlineKeyboardButton(f"Quality ✅" if current_preference == 'quality' else "Quality", callback_data="quality")
    button_both = InlineKeyboardButton(f"Both ✅" if current_preference == 'both' else "Both", callback_data="both")

    # Create the updated button layout
    buttons = InlineKeyboardMarkup([[button_season, button_quality, button_both]])

    # Edit the original message with the updated buttons
    await callback_query.message.edit_text(
        "Please select your preferred mode:",
        reply_markup=buttons
    )

    # Acknowledge the callback query
    await callback_query.answer(f"Switched to {selected_mode} mode!")
