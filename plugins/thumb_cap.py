from pyrogram import Client, filters, enums
from helper.database import db
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, InputMediaPhoto

@Client.on_message(filters.private & filters.command('caption_mode'))
async def caption_mode(client, message):
    user_id = message.from_user.id
    current_mode = await db.get_caption_preference(user_id) or "normal"  # Default to normal
    current_caption = await db.get_caption(user_id) or "None"  # Default caption

    # Create buttons with a checkmark for the current mode
    buttons = [
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'normal' else ''}Normal", callback_data="setmode_normal"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'nocaption' else ''}No Caption", callback_data="setmode_nocap"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'bold' else ''}Bold", callback_data="setmode_bold"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'italic' else ''}Italic", callback_data="setmode_italic"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'underline' else ''}Underlined", callback_data="setmode_underline"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'mono' else ''}Mono", callback_data="setmode_mono"),
        ],
        [
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'strikethrough' else ''}Strikethrough", callback_data="setmode_strikethrough"),
            InlineKeyboardButton(f"{'✅ ' if current_mode == 'spoiler' else ''}Spoiler", callback_data="setmode_spoiler"),
        ]
    ]

    # Send a photo with the initial message and buttons
    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/75H.jpg",
        caption=f"<u><b>📝 CAPTION MODE 📝</b></u>\n\n㊂ Select your preferred caption mode:\n\n<b>๏ Current Caption:</b> {current_caption}\n<b>๏ Current Mode:</b> {current_mode.capitalize()}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# Callback Query Handler to set the caption mode
@Client.on_callback_query(filters.regex(r"^setmode_(normal|mono|bold|italic|underline|nocap|strikethrough|spoiler)$"))
async def callback_query_handler(client, callback_query):
    user_id = callback_query.from_user.id
    mode = callback_query.data.split("_")[1]  # Extract mode from callback data (e.g., "setmode_normal" -> "normal")

    try:
        # Save the preferred caption mode to the database
        await db.set_caption_preference(user_id, mode)
        current_caption = await db.get_caption(user_id) or "None"  # Fetch the current caption

        # Create updated buttons
        buttons = [
            [
                InlineKeyboardButton(f"{'✅ ' if mode == 'normal' else ''}Normal", callback_data="setmode_normal"),
                InlineKeyboardButton(f"{'✅ ' if mode == 'nocaption' else ''}No Caption", callback_data="setmode_npcap"),
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if mode == 'bold' else ''}Bold", callback_data="setmode_bold"),
                InlineKeyboardButton(f"{'✅ ' if mode == 'italic' else ''}Italic", callback_data="setmode_italic"),
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if mode == 'underline' else ''}Underlined", callback_data="setmode_underline"),
                InlineKeyboardButton(f"{'✅ ' if mode == 'mono' else ''}Mono", callback_data="setmode_mono"),
            ],
            [
                InlineKeyboardButton(f"{'✅ ' if mode == 'strikethrough' else ''}Strikethrough", callback_data="setmode_strikethrough"),
                InlineKeyboardButton(f"{'✅ ' if mode == 'spoiler' else ''}Spoiler", callback_data="setmode_spoiler"),
            ]
        ]

        # Edit the message to show the updated caption mode and buttons
        await callback_query.message.edit_media(
            InputMediaPhoto(
                media="https://envs.sh/75H.jpg",
                caption=f"<u><b>📝 CAPTION MODE 📝</b></u>\n\n㊂ Select your preferred caption mode:\n\n<b>๏ Current Caption:</b> {current_caption}\n<b>๏ Current Mode:</b> {current_mode.capitalize()}",
            ),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await callback_query.answer(f"Caption mode set to: {mode.capitalize()}")
    except Exception as e:
        await callback_query.answer(f"An unexpected error occurred: {e}", show_alert=True)
        


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
