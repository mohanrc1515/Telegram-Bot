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
    await message.reply_text(
        "Please send the **start message** for each season. "
        "You can send text, an image (with or without caption), or a sticker. "
        "Placeholders like {quality}, {title}, {season} and {firstepisode} can be used."
    )

    response = await client.listen(message.chat.id)

    # Determine if the response is a sticker, image, or text
    if response.sticker:
        await db.set_start_message(user_id, sticker_id=response.sticker.file_id, text=response.caption or "")
        await message.reply_text("Start message set with a sticker.")
    elif response.photo:
        await db.set_start_message(user_id, image_id=response.photo.file_id, text=response.caption or "")
        await message.reply_text("Start message set with an image.")
    elif response.text:
        await db.set_start_message(user_id, text=response.text)
        await message.reply_text(f"Start message set:\n{response.text}")
    else:
        await message.reply_text("Invalid format. Please send a text, image, or sticker.")

@Client.on_message(filters.command("enddump") & filters.private)
async def end_dump(client, message: Message):
    user_id = message.from_user.id
    await message.reply_text(
        "Please send the **end message** for each season. "
        "You can send text, an image (with or without caption), or a sticker. "
        "Placeholders like {quality}, {title}, {firstepisode}, {season} and {lastepisode} can be used."
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

@Client.on_message(filters.command("dumptext") & filters.private)
async def show_dump_text(client, message: Message):
    user_id = message.from_user.id

    # Get start and end messages from the database
    start_message = await db.get_start_message(user_id) or {"text": "No start message set."}
    end_message = await db.get_end_message(user_id) or {"text": "No end message set."}

    response_text = (
        f"**✨ Start Message:**\n\n"
        f"📜 **Text:** {start_message.get('text', 'N/A')}\n"
        f"🖼️ **Sticker:** {'✅ Yes' if start_message.get('sticker_id') else '❌ No'}\n"
        f"📷 **Image:** {'✅ Yes' if start_message.get('image_id') else '❌ No'}\n\n"
        f"**🌟 End Message:**\n\n"
        f"📜 **Text:** {end_message.get('text', 'N/A')}\n"
        f"🖼️ **Sticker:** {'✅ Yes' if end_message.get('sticker_id') else '❌ No'}\n"
        f"📷 **Image:** {'✅ Yes' if end_message.get('image_id') else '❌ No'}"
    )

    await message.reply_text(response_text)


@Client.on_message(filters.command("dumptextset") & filters.private)
async def dump_text_set(client, message: Message):
    user_id = message.from_user.id
    # Get the current trigger from the database to display the selected one
    current_trigger = await db.get_user_dumptext_trigger(user_id)
    
    # Define buttons with a check mark (✅) if the option is selected
    buttons = [
        [InlineKeyboardButton(
            "Season ✅" if current_trigger == "season" else "Season", callback_data="set_dumptext_season")],
        [InlineKeyboardButton(
            "Quality ✅" if current_trigger == "quality" else "Quality", callback_data="set_dumptext_quality")]
    ]
    
    # Prompt user to select the trigger type
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text(
        "Please select the trigger for the dump text:",
        reply_markup=reply_markup
    )


@Client.on_callback_query(filters.regex(r"set_dumptext_(season|quality)"))
async def set_dumptext_trigger(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    trigger_type = callback_query.data.split("_")[-1]  # Extract season or quality
    
    # Save user's choice in the database
    await db.set_user_dumptext_trigger(user_id, trigger_type)
    
    # Edit the message to reflect the updated choice with ✅ on the selected option
    current_trigger = await db.get_user_dumptext_trigger(user_id)
    
    buttons = [
        [InlineKeyboardButton(
            "Season ✅" if current_trigger == "season" else "Season", callback_data="set_dumptext_season")],
        [InlineKeyboardButton(
            "Quality ✅" if current_trigger == "quality" else "Quality", callback_data="set_dumptext_quality")]
    ]
    
    await callback_query.answer(f"Dump text will now trigger on {trigger_type.capitalize()} change.")
    await callback_query.message.edit_text(
        f"Dump text trigger set to **{trigger_type.capitalize()}**.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_message(filters.command("switch") & filters.private)
async def switch_message_type(client, message: Message):
    user_id = message.from_user.id

    # Retrieve current user preference from the database
    current_preference = await db.get_user_preference(user_id)  # Assume 'db' handles DB operations

    # Determine the new preference and the text for the buttons
    if current_preference == 'season':
        new_preference = 'quality'
        button_season = InlineKeyboardButton(f"Season", callback_data="season")
        button_quality = InlineKeyboardButton(f"Quality ✅", callback_data="quality")
    else:
        new_preference = 'season'
        button_season = InlineKeyboardButton(f"Season ✅", callback_data="season")
        button_quality = InlineKeyboardButton(f"Quality", callback_data="quality")

    # Create the buttons and send a message with them
    buttons = InlineKeyboardMarkup([[button_season, button_quality]])

    # Update user preference in the database
    await db.set_user_preference(user_id, new_preference)

    # Notify the user and show the buttons
    await message.reply_text(
        f"Switched to {new_preference} mode. You can now choose the mode below:",
        reply_markup=buttons
    )


