from pyrogram import Client, filters, enums
from helper.database import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message

# Listen for the /captionmode command to send the initial selection buttons
@Client.on_message(filters.private & filters.command('captionmode'))
async def caption_mode(client, message):
    user_id = message.from_user.id
    current_mode = await db.get_caption_preference(user_id) or "normal"  # Default to normal

    # Create buttons with a checkmark for the current mode
    buttons = [
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'normal' else ''}Normal", callback_data="setmode_normal"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'mono' else ''}Mono", callback_data="setmode_mono"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'bold' else ''}Bold", callback_data="setmode_bold"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'italic' else ''}Italic", callback_data="setmode_italic"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'underline' else ''}Underlined", callback_data="setmode_underline"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'quote' else ''}Quote", callback_data="setmode_quote"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'strikethrough' else ''}Strikethrough", callback_data="setmode_strikethrough"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'spoiler' else ''}Spoiler", callback_data="setmode_spoiler"),
        ]
    ]

    # Send the initial message with buttons
    await message.reply_text(
        "Select your preferred caption mode:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# Callback Query Handler to set the caption mode
@Client.on_callback_query(filters.regex(r"^setmode_(normal|mono|bold|italic|underline|quote|strikethrough|spoiler)$"))
async def callback_query_handler(client, callback_query):
    user_id = callback_query.from_user.id
    mode = callback_query.data.split("_")[1]  # Extract mode from callback data (e.g., "setmode_normal" -> "normal")

    try:
        # Save the preferred caption mode to the database
        await db.set_caption_preference(user_id, mode)

        # Update the button texts to reflect the new preference
        normal_button_text = "Normal ✅" if mode == "normal" else "Normal"
        mono_button_text = "Mono ✅" if mode == "mono" else "Mono"
        bold_button_text = "Bold ✅" if mode == "bold" else "Bold"
        italic_button_text = "Italic ✅" if mode == "italic" else "Italic"
        underline_button_text = "Underlined ✅" if mode == "underline" else "Underlined"
        quote_button_text = "Quote ✅" if mode == "quote" else "Quote"
        strikethrough_button_text = "Strikethrough ✅" if mode == "strikethrough" else "Strikethrough"
        spoiler_button_text = "Spoiler ✅" if mode == "spoiler" else "Spoiler"

        # Create the updated inline keyboard with buttons
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(normal_button_text, callback_data="setmode_normal")],
            [InlineKeyboardButton(mono_button_text, callback_data="setmode_mono")],
            [InlineKeyboardButton(bold_button_text, callback_data="setmode_bold")],
            [InlineKeyboardButton(italic_button_text, callback_data="setmode_italic")],
            [InlineKeyboardButton(underline_button_text, callback_data="setmode_underline")],
            [InlineKeyboardButton(quote_button_text, callback_data="setmode_quote")],
            [InlineKeyboardButton(strikethrough_button_text, callback_data="setmode_strikethrough")],
            [InlineKeyboardButton(spoiler_button_text, callback_data="setmode_spoiler")]
        ])

        # Update the message text with the new button selection
        await callback_query.message.edit_text("Choose your preferred caption mode:", reply_markup=keyboard)
        await callback_query.answer(f"Caption mode set to: {mode.capitalize()}")
    except Exception as e:
        await callback_query.message.edit_text(f"An unexpected error occurred: {e}")


@Client.on_message(filters.private & filters.command('set_caption'))
async def add_caption(client, message):
    if len(message.command) == 1:
       return await message.reply_text("**Give The Caption\n\nExample :- `/set_caption 📕Name ➠ : {filename} \n\n🔗 Size ➠ : {filesize} \n\n⏰ Duration ➠ : {duration}`**")
    caption = message.text.split(" ", 1)[1]
    await db.set_caption(message.from_user.id, caption=caption)
    await message.reply_text("**Your Caption Successfully Added ✅**")
   
@Client.on_message(filters.private & filters.command('del_caption'))
async def delete_caption(client, message):
    caption = await db.get_caption(message.from_user.id)  
    if not caption:
       return await message.reply_text("**You Don't Have Any Caption ❌**")
    await db.set_caption(message.from_user.id, caption=None)
    await message.reply_text("**Your Caption Successfully Deleted 🗑️**")
                                       
@Client.on_message(filters.private & filters.command(['see_caption', 'view_caption']))
async def see_caption(client, message):
    caption = await db.get_caption(message.from_user.id)  
    if caption:
       await message.reply_text(f"**Your Caption :**\n\n`{caption}`")
    else:
       await message.reply_text("**You Don't Have Any Caption ❌**")


@Client.on_message(filters.private & filters.command(['view_thumb', 'viewthumb']))
async def viewthumb(client, message):    
    thumb = await db.get_thumbnail(message.from_user.id)
    if thumb:
       await client.send_photo(chat_id=message.chat.id, photo=thumb)
    else:
        await message.reply_text("**You Don't Have Any Thumbnail ❌**") 
		
@Client.on_message(filters.private & filters.command(['del_thumb', 'delthumb']))
async def removethumb(client, message):
    await db.set_thumbnail(message.from_user.id, file_id=None)
    await message.reply_text("**Thumbnail Deleted Successfully 🗑️**")
	
@Client.on_message(filters.private & filters.photo)
async def addthumbs(client, message):
    mkn = await message.reply_text("Please Wait ...")
    await db.set_thumbnail(message.from_user.id, file_id=message.photo.file_id)                
    await mkn.edit("**Thumbnail Saved Successfully ✅️**")

@Client.on_message(filters.command("getthumb") & filters.private)
async def get_thumbnail(client, message: Message):
    user_id = message.from_user.id

    # Check if user is authorized
    if not await db.is_user_authorized(user_id):
        await message.reply_text(Config.USER_REPLY)
        return

    # Check if thumbnail extraction is ongoing
    if await db.is_thumbnail_extraction_mode(user_id):
        file = message.document or message.video or message.audio
        if not file:
            await message.reply_text("Unsupported file type. Please send a video or document.")
            return

        thumb_id = None
        if message.video and message.video.thumbs:
            thumb_id = message.video.thumbs[0].file_id
        elif message.document and message.document.thumbs:
            thumb_id = message.document.thumbs[0].file_id

        if thumb_id:
            thumb_path = await client.download_media(thumb_id)
            try:
                await client.send_photo(message.chat.id, thumb_path, caption="Here is the thumbnail you requested.")
            finally:
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            await db.set_thumbnail_extraction_mode(user_id, False)  # Disable thumbnail extraction mode
        else:
            await message.reply_text("No thumbnail available for this file.")
        return

    # Enable thumbnail extraction mode
    await db.set_thumbnail_extraction_mode(user_id, True)
    await message.reply_text("You are now in thumbnail extraction mode. Please send the file to extract the thumbnail.")
	
