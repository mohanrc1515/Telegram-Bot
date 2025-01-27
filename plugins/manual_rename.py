from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.enums import MessageMediaType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.ffmpeg import fix_thumb, add_metadata
from helper.utils import progress_for_pyrogram, humanbytes, convert, add_prefix_suffix
from helper.database import db
from asyncio import sleep
import os, time, logging
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_statistics(user_id, file_size):
    # Update user-specific file count
    current_user_count = await db.get_file_count(user_id)
    new_user_count = current_user_count + 1
    await db.update_file_count(user_id, new_user_count)

    # Update global file count and size
    current_global_count = await db.get_total_files_renamed()
    current_global_size = await db.get_total_renamed_size()

    new_global_count = current_global_count + 1
    new_global_size = current_global_size + file_size

    await db.update_total_files_renamed(new_global_count)
    await db.update_total_renamed_size(new_global_size)

    # Log the updated stats
    print(f"User {user_id}: Files Processed = {new_user_count}")
    print(f"Global Stats: Total Files = {new_global_count}, Total Size = {humanbytes(new_global_size)}")
    

@Client.on_message(filters.private & filters.command("rename"))
async def rename_command(client, message):
    reply_message = message.reply_to_message
    user_id = message.chat.id

    # Ensure the command is used in reply to a file
    if not reply_message or not any([reply_message.document, reply_message.audio, reply_message.video]):
        return await message.reply_text("Please reply to a file (document, audio, or video) with /rename to rename it.")

    # Check if the user is in Manual Rename mode
    if not await db.get_mode(user_id):
        return await message.reply_text("You are currently in Auto Rename mode. Switch to Manual Rename mode to use this command by hitting /mode.")

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
        _bool_metadata = await db.get_meta(message.chat.id)
        if _bool_metadata:
            # Retrieve metadata title, author, subtitle, audio, video, and artist from the database
            elites_data = await db.get_metadata(message.chat.id)
                
            sub_title = elites_data.get("title")
            sub_author = elites_data.get("author")
            sub_subtitle = elites_data.get("subtitle")
            sub_audio = elites_data.get("audio")
            sub_video = elites_data.get("video")
            sub_artist = elites_data.get("artist")

            metadata_path = f"Metadata/{new_file_name}"
            await add_metadata(path, metadata_path, sub_title, sub_author, sub_subtitle, sub_audio, sub_video, sub_artist, download_msg)

        else:
            await asyncio.sleep(1.5)
            await download_msg.edit("Processing....  ⚡")
        
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
    user_id = int(update.message.chat.id) 
    media = getattr(file, file.media.value)
    c_caption = await db.get_caption(update.message.chat.id)
    c_thumb = await db.get_thumbnail(update.message.chat.id)

    if c_caption:
         try:
             caption = c_caption.format(filename=new_filename, filesize=humanbytes(media.file_size), duration=convert(duration))
         except Exception as e:
             return await ms.edit(text=f"Your Caption Error Except Keyword Argument: ({e})")             
    else:
         caption = f"**{new_filename}**"
 
    if (media.thumbs or c_thumb):
         if c_thumb:
             ph_path = await bot.download_media(c_thumb)
             width, height, ph_path = await fix_thumb(ph_path)
         else:
             try:
                 ph_path_ = await take_screen_shot(file_path, os.path.dirname(os.path.abspath(file_path)), random.randint(0, duration - 1))
                 width, height, ph_path = await fix_thumb(ph_path_)
             except Exception as e:
                 ph_path = None
                 print(e)  
 
    await ms.edit("💠 Try To Upload...  ⚡")
    file_size = file.file_size if file else 0
    await update_statistics(message.chat.id, file_size)       
    type = update.data.split("_")[1]
    try:
        if type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=metadata_path if _bool_metadata else file_path,
                thumb=ph_path, 
                caption=caption, 
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time()))

        elif type == "video": 
            await bot.send_video(
                update.message.chat.id,
                video=metadata_path if _bool_metadata else file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time()))

        elif type == "audio": 
            await bot.send_audio(
                update.message.chat.id,
                audio=metadata_path if _bool_metadata else file_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time()))


    except Exception as e:          
        os.remove(file_path)
        if ph_path:
            os.remove(ph_path)
        return await ms.edit(f"**Error :** `{e}`")    
 
    await ms.delete() 
    if ph_path:
        os.remove(ph_path)
    if file_path:
        os.remove(file_path)
