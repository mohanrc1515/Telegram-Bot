from pyrogram import Client, filters, enums
from helper.database import db

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
	
