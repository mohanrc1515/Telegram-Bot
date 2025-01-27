from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from helper.ffmpeg import fix_thumb, add_metadata, take_screen_shot
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import db
from asyncio import sleep
from PIL import Image
import os, time, re, random, asyncio


@@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    user_id = message.chat.id
    
    # Check if the user is in Manual Rename mode
    user_mode = await db.get_mode(user_id)  # Assume this returns the user's mode
    if user_mode != "Manual Rename":
        return await message.reply_text("You are not in Manual Rename mode. Change your mode to Manual Rename to use this feature.")
    
    file = getattr(message, message.media.value)
    filename = file.file_name  
    if file.file_size > 2000 * 1024 * 1024:
        return await message.reply_text("Sorry, this bot doesn't support uploading files larger than 2GB.")
    
    try:
        await message.reply_text(
            text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
        await sleep(30)  # Wait for the user to reply
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**Please Enter New Filename**\n\n**Old File Name** :- `{filename}`",
            reply_to_message_id=message.id,
            reply_markup=ForceReply(True)
        )
    except Exception as e:
        print(f"Error in rename_start: {e}")
        return


@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    user_id = message.chat.id

    # Check if the user is in Manual Rename mode
    user_mode = await db.get_mode(user_id)
    if user_mode != "Manual Rename":
        return

    # Check if reply is to a ForceReply message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)

        # Add file extension if not present
        if "." not in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn

        await reply_message.delete()

        # Provide options for output file type
        button = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])
        
        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


@Client.on_callback_query(filters.regex("upload"))
async def doc(bot, update):    
    # Creating Directory for Metadata
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")
        
    # Extracting necessary information    
    prefix = await db.get_prefix(update.message.chat.id)
    suffix = await db.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1]

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(f"Something Went Wrong Can't Able To Set Prefix Or Suffix 🥺 \n\n**Contact My Creator :** @Elites_Assistance\n\n**Error :** `{e}`")
    
    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("🚀 Try To Download...  ⚡")    
    try:
     	path = await bot.download_media(message=file, file_name=file_path, progress=progress_for_pyrogram,progress_args=("🚀 Try To Downloading...  ⚡", ms, time.time()))                    
    except Exception as e:
     	return await ms.edit(e)
    

    # Metadata Adding Code
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
        
        
        
