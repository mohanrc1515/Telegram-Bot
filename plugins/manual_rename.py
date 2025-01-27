from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.ffmpeg import fix_thumb, add_metadata
from helper.utils import progress_for_pyrogram, humanbytes, convert, add_prefix_suffix
from helper.database import db
from asyncio import sleep
import os, time

@Client.on_message(filters.private & filters.command("rename"))
async def rename_command(client, message):
    reply_message = message.reply_to_message
    user_id = message.chat.id

    # Ensure the command is used in reply to a file
    if not reply_message or not (reply_message.document or reply_message.audio or reply_message.video):
        return await message.reply_text("Please reply to a file (document, audio, or video) with /rename to rename it.")

    # Check if the user is in Manual Rename mode
    if not await db.get_mode(user_id):
        return await message.reply_text("You are currently in Auto Rename mode. Switch to Manual Rename mode to use this command.")

    file = getattr(reply_message, reply_message.media.value)
    filename = file.file_name

    if file.file_size > 2000 * 1024 * 1024:  # 2GB limit
        return await message.reply_text("Sorry, this bot doesn't support renaming files larger than 2GB.")

    try:
        await message.reply_text(
            text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=reply_message.id,
            reply_markup=ForceReply(True)
        )
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=reply_message.id,
            reply_markup=ForceReply(True)
        )


@Client.on_message(filters.private & filters.reply)
async def handle_rename_reply(client, message):
    reply_message = message.reply_to_message
    user_id = message.chat.id

    # Check if reply is to a ForceReply message
    if reply_message.reply_markup and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()

        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)

        # Add file extension if not present
        if "." not in new_name:
            extn = media.file_name.rsplit('.', 1)[-1] if "." in media.file_name else "mkv"
            new_name = f"{new_name}.{extn}"

        await reply_message.delete()

        # Provide options for output file type
        button = [[InlineKeyboardButton("📁 Document",callback_data = "upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data = "upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data = "upload_audio")])
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )

  

@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):    
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
        
    prefix = await db.get_prefix(update.message.chat.id)
    suffix = await db.get_suffix(update.message.chat.id)
    new_name = update.message.text.split(":-")[1].strip()

    try:
        new_filename = add_prefix_suffix(new_name, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Error: {e}")

    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("🚀 Try To Download...  ⚡")    
    try:
        path = await bot.download_media(
            message=file, 
            file_name=file_path, 
            progress=progress_for_pyrogram,
            progress_args=("🚀 Try To Downloading...  ⚡", ms, time.time())
        )
        
        # Add the line to update statistics after the download is completed
        file_size = file.file_size if file else 0
        await update_statistics(message.chat.id, file_size)
    
    except Exception as e:
        return await ms.edit(e)      
    
    _bool_metadata = await db.get_meta(update.message.chat.id)
    if _bool_metadata:
        elites_data = await db.get_metadata(update.message.chat.id)
        metadata_path = f"Metadata/{new_filename}"
        try:
            await add_metadata(
                path, metadata_path,
                elites_data.get("title"), elites_data.get("author"),
                elites_data.get("subtitle"), elites_data.get("audio"),
                elites_data.get("video"), elites_data.get("artist")
            )
        except Exception as e:
            return await ms.edit(f"Error adding metadata: {e}")

    duration = 0
    try:
        parser = createParser(file_path)
        metadata = extractMetadata(parser)
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        parser.close()   
    except:
        pass
        
    ph_path = None
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    file_size = getattr(file, "file_size", None)
    caption = c_caption.format(
        filename=new_filename,
        filesize=humanbytes(file_size) if file_size else "Unknown",
        duration=convert(duration) if duration else "N/A"
    ) if c_caption else f"{new_filename}"

    caption_mode = await db.get_caption_preference(update.message.chat.id) or "normal"
    if caption_mode == "bold":
        caption = f"**{caption}**"
    elif caption_mode == "italic":
        caption = f"__{caption}__"
    elif caption_mode == "underline":
        caption = f"<u>{caption}</u>"
    elif caption_mode == "strikethrough":
        caption = f"~~{caption}~~"
    elif caption_mode == "nocaption":
        caption = f"```{caption}```"
    elif caption_mode == "mono":
        caption = f"`{caption}`"
    elif caption_mode == "spoiler":
        caption = f"||{caption}||"

    if c_thumb:
        ph_path = await bot.download_media(c_thumb)
        ph_path = await fix_thumb(ph_path)

    await ms.edit("💠 Uploading... ⚡")
    type = update.data.split("_")[1]
    try:
        send_func = {
            "document": bot.send_document,
            "video": bot.send_video,
            "audio": bot.send_audio
        }
        await send_func[type](
            update.message.chat.id,
            document=metadata_path if _bool_metadata else file_path,
            caption=caption,
            thumb=ph_path,
            duration=duration,
            progress=progress_for_pyrogram,
            progress_args=("💠 Uploading... ⚡", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"Error: {e}")
    finally:
        if ph_path:
            os.remove(ph_path)
        if file_path:
            os.remove(file_path)

    await ms.delete()
