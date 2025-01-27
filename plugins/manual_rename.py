from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.ffmpeg import fix_thumb, add_metadata
from helper.utils import progress_for_pyrogram, humanbytes, convert, add_prefix_suffix
from helper.database import db
from asyncio import sleep
import os, time, logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@Client.on_message(filters.private & filters.command("rename"))
async def rename_command(client, message):
    reply_message = message.reply_to_message
    user_id = message.chat.id

    # Ensure the command is used in reply to a file
    if not reply_message or not any([reply_message.document, reply_message.audio, reply_message.video]):
        return await message.reply_text("Please reply to a file (document, audio, or video) with /rename to rename it.")

    # Check if the user is in Manual Rename mode
    if not await db.get_mode(user_id):
        return await message.reply_text("You are currently in Auto Rename mode. Switch to Manual Rename mode to use this command.")

    file = reply_message.document or reply_message.audio or reply_message.video
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
        logger.warning(f"FloodWait triggered: {e}")
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
        media = file.document or file.audio or file.video

        # Add file extension if not present
        if "." not in new_name:
            extn = media.file_name.rsplit('.', 1)[-1] if "." in media.file_name else "mkv"
            new_name = f"{new_name}.{extn}"

        await reply_message.delete()

        # Provide options for output file type
        button = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
        if file.video:
            button.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.audio:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def handle_upload(bot, update):
    if not os.path.isdir("downloads"):
        os.mkdir("downloads")

    prefix = await db.get_prefix(update.message.chat.id)
    suffix = await db.get_suffix(update.message.chat.id)
    new_name = update.message.text.split(":-")[1].strip()

    try:
        new_filename = add_prefix_suffix(new_name, prefix, suffix)
    except Exception as e:
        logger.error(f"Error adding prefix/suffix: {e}")
        return await update.message.edit(f"Error: {e}")

    file_path = os.path.join("downloads", str(update.from_user.id), new_filename)
    file = update.message.reply_to_message

    ms = await update.message.edit("🚀 Trying to download... ⚡")
    try:
        path = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading... ⚡", ms, time.time())
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        return await ms.edit(str(e))

    # Handle metadata if enabled
    _bool_metadata = await db.get_meta(update.message.chat.id)
    if _bool_metadata:
        metadata_path = os.path.join("downloads", "Metadata", new_filename)
        try:
            await add_metadata(path, metadata_path, **await db.get_metadata(update.message.chat.id))
            path = metadata_path
        except Exception as e:
            logger.error(f"Metadata error: {e}")
            return await ms.edit(f"Error adding metadata: {e}")

    # Extract duration
    duration = 0
    try:
        parser = createParser(path)
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            duration = metadata.get("duration").seconds
        parser.close()
    except Exception as e:
        logger.warning(f"Metadata extraction failed: {e}")

    ph_path = None
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    caption = c_caption.format(
        filename=new_filename,
        filesize=humanbytes(file.file_size),
        duration=convert(duration)
    ) if c_caption else f"{new_filename}"

    if c_thumb:
        ph_path = await bot.download_media(c_thumb)
        ph_path = await fix_thumb(ph_path)

    await ms.edit("💠 Uploading... ⚡")
    upload_type = update.data.split("_")[1]
    try:
        send_func = {
            "document": bot.send_document,
            "video": bot.send_video,
            "audio": bot.send_audio
        }
        await send_func[upload_type](
            update.message.chat.id,
            document=path if upload_type == "document" else None,
            video=path if upload_type == "video" else None,
            audio=path if upload_type == "audio" else None,
            caption=caption,
            thumb=ph_path,
            duration=duration,
            progress=progress_for_pyrogram,
            progress_args=("💠 Uploading... ⚡", ms, time.time())
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return await ms.edit(f"Error: {e}")
    finally:
        if ph_path and os.path.exists(ph_path):
            os.remove(ph_path)
        if path and os.path.exists(path):
            os.remove(path)

    await ms.delete()
