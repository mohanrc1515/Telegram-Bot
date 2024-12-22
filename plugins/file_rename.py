from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message
from PIL import Image
from datetime import datetime
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import db
from helper.ffmpeg import *
from helper.extraction import *
from config import Config
from asyncio import Queue, Semaphore, create_task, gather
import os
import time
import re
import asyncio
import pytz

renaming_operations = {}
thumbnail_extraction_mode = {}
sequence_notified = {}
user_files = {}
user_task_queues = {}
user_semaphores = {}

# Function to get or create the queue for each user
def get_user_queue(user_id):
    if user_id not in user_task_queues:
        user_task_queues[user_id] = Queue()
    return user_task_queues[user_id]

# Function to get or create the semaphore for each user
def get_user_semaphore(user_id):
    if user_id not in user_semaphores:
        user_semaphores[user_id] = Semaphore(5)
    return user_semaphores[user_id]

async def process_task(user_id, task):
    semaphore = get_user_semaphore(user_id)
    async with semaphore:
        try:
            await task()
        except Exception as e:
            print(f"Error processing task for user {user_id}: {e}")
        finally:
            await asyncio.sleep(5)

async def increment_global_stats(message):
    # Determine the file size based on the message type
    file_size = 0
    if message.document:
        file_size = message.document.file_size
    elif message.video:
        file_size = message.video.file_size
    elif message.audio:
        file_size = message.audio.file_size
    elif message.photo:
        file_size = message.photo[-1].file_size if message.photo else 0

    # Update the total number of files renamed
    total_files_renamed = await db.get_total_files_renamed()
    new_total_files_renamed = total_files_renamed + 1
    await db.update_total_files_renamed(new_total_files_renamed)

    # Update the total size of renamed files
    total_renamed_size = await db.get_total_renamed_size()
    new_total_renamed_size = total_renamed_size + file_size
    await db.update_total_renamed_size(new_total_renamed_size)

async def increment_user_file_count(user_id):
    current_file_count = await db.get_file_count(user_id)
    new_file_count = current_file_count + 1
    await db.update_file_count(user_id, new_file_count)
    return new_file_count    

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_queue(client, message: Message):
    user_id = message.from_user.id

    user_queue = get_user_queue(user_id)
    while not user_queue.empty():
        await user_queue.get()
        user_queue.task_done()

    # Reset semaphore to unlock ongoing tasks
    user_semaphore = get_user_semaphore(user_id)
    while user_semaphore.locked():
        user_semaphore.release()

    # Remove user-related data from dictionaries
    if user_id in renaming_operations:
        del renaming_operations[user_id]
    if user_id in sequence_notified:
        del sequence_notified[user_id]
    if user_id in user_task_queues:
        del user_task_queues[user_id]
    if user_id in user_semaphores:
        del user_semaphores[user_id]
    if user_id in thumbnail_extraction_mode:
        del thumbnail_extraction_mode[user_id]
    if user_id in user_files:
        del user_files[user_id]
     
    if await db.is_user_sequence_mode(user_id):
        await db.set_user_sequence_mode(user_id, False)
   
    await db.clear_user_sequence_queue(user_id)
    await db.clear_sequence_queue(user_id)
    await message.reply_text("All tasks have been canceled !!")

@Client.on_message(filters.command("queue") & filters.private)
async def show_queue(client, message: Message):
    user_id = message.from_user.id
    user_queue = get_user_queue(user_id)
    queue_size = user_queue.qsize()

    if queue_size > 0:
        await message.reply_text(f"Your renaming queue contains {queue_size} files.")
    else:
        await message.reply_text("Your renaming queue is empty.")
        
@Client.on_message(filters.command("getthumb") & filters.private)
async def get_thumbnail(client, message: Message):
    user_id = message.from_user.id

    if not await db.is_user_authorized(user_id):
        await message.reply_text(Config.USER_REPLY)
        return    
        
    if thumbnail_extraction_mode.get(user_id, False):
        await message.reply_text("You are already in thumbnail extraction mode. Please send the file to extract the thumbnail.")
    else:
        thumbnail_extraction_mode[user_id] = True
        await message.reply_text("Please send the file from which you want to extract the thumbnail.")
        
# Handle file uploads and renaming
@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def handle_files(client: Client, message: Message):
    user_id = message.from_user.id
    firstname = message.from_user.first_name
    format_template = await db.get_format_template(user_id)
    media_preference = await db.get_media_preference(user_id)
    
    if not await db.is_user_authorized(user_id):
        await message.reply_text(Config.USER_REPLY)
        return
        
    if await db.is_user_sequence_mode(user_id):
        file_name = None
        if message.document:
            file_name = message.document.file_name
        elif message.video:
            file_name = message.video.file_name
        elif message.audio:
            file_name = message.audio.file_name

        if file_name:
            season = extract_season(file_name) or 0
            episode = extract_episode_number(file_name) or 0
            volume = extract_volume_number(file_name) or 0
            chapter = extract_chapter_number(file_name) or 0

            if episode or chapter:
                file_id = (
                    message.document.file_id if message.document else 
                    (message.video.file_id if message.video else message.audio.file_id)
                )
                await db.add_to_sequence_queue(user_id, {
                    'file_id': file_id,
                    'file_name': file_name,
                    'season': int(season),
                    'episode': int(episode),
                    'volume': int(volume),
                    'chapter': int(chapter),
                    'file_type': 'document' if message.document else ('video' if message.video else 'audio')
                })
                await message.reply_text("The file has been successfully received and integrated into the sequencing.")
            else:
                await message.reply_text(f"Could not extract sufficient information from '{file_name}'. File was not added to the queue.")
        else:
            await message.reply_text("File name could not be determined.")
        return
        
    if user_id in thumbnail_extraction_mode and thumbnail_extraction_mode[user_id]:
        file = message.document or message.video or message.audio
        if not file:
            await message.reply_text("Unsupported File Type")
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
            del thumbnail_extraction_mode[user_id]
        else:
            await message.reply_text("No thumbnail available for this file.")
        return
        
    if not format_template:
        return await message.reply_text("Please Set An Auto Rename Format First Using /autorename")    

    file = message.document or message.video or message.audio
    if not file:
        await message.reply_text("Unsupported File Type.", quote=True)
        return

    file_info = {
        'file_type': media_preference or "document" if message.document else media_preference or "video" if message.video else media_preference or "audio",
        'file_id': file.file_id,
        'file_name': file.file_name if file else 'Unknown'
    }

    file_id = file_info['file_id']
    file_name = file_info['file_name']
    file_type = file_info['file_type']

    print(f"Original File Name: {file_name}")

    if file_id in renaming_operations:
        elapsed_time = (datetime.now() - renaming_operations[file_id]).seconds
        if elapsed_time < 10:
            print("File is being ignored as it is currently being renamed or was renamed recently.")
            return

    renaming_operations[file_id] = datetime.now()

    def replace_placeholder(template, placeholder, value):
        return template.replace(f"{{{placeholder}}}", str(value) if value else '')

    placeholders = {
        "title": extract_title(file_name),
        "chapter": extract_chapter_number(file_name),
        "volume": extract_volume_number(file_name),
        "episode": extract_episode_number(file_name),
        "quality": extract_quality(file_name),
        "season": extract_season(file_name),
        "audio": extract_audio_language(file_name)
    }
    for placeholder, value in placeholders.items():
        format_template = replace_placeholder(format_template, placeholder, value)                     
           
    _, file_extension = os.path.splitext(file_name)
    new_file_name = f"{format_template}{file_extension}"
    file_path = f"downloads/{new_file_name}"

    working_dir = "Metadata"
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)    
    
    # Initialize the file based on media type
    file = message.document or message.video or message.audio
    if file:
        # Reply with the specified message, ensuring the reply is quoted
        download_msg = await message.reply_text(
            "Your file has been added to the queue and will be processed soon.",
            quote=True
        )
   
    async def task():
        await asyncio.sleep(2)
        await download_msg.edit("Processing... ⚡")
        try:
            path = await client.download_media(
                message=file,
                file_name=file_path,
                progress=progress_for_pyrogram,
                progress_args=("Download Started....", download_msg, time.time())
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)  # Wait dynamically based on the flood wait error
            await task()  # Retry the task after the flood wait
        except Exception as e:
            # Mark the file as ignored
            del renaming_operations[file_id]
            return await download_msg.edit(str(e))
            
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
            await asyncio.sleep(2)
            await increment_user_file_count(user_id)
            await asyncio.sleep(2)
            await increment_global_stats(message)
            await asyncio.sleep(1.5)
        
        duration = 0
        try:
            metadata = extractMetadata(createParser(file_path))
            if metadata.has("duration"):
                duration = metadata.get('duration').seconds
        except Exception as e:
            print(f"Error getting duration: {e}")
            
        try:
            upload_msg = await download_msg.edit("Trying To Upload...⚡")
        except FloodWait as e:
            await asyncio.sleep(e.value)  # Wait dynamically if FloodWait error occurs
            upload_msg = await download_msg.edit("Trying To Upload...⚡")  # Retry edit
                
        ph_path = None
        c_thumb = await db.get_thumbnail(message.chat.id)                
        c_caption = await db.get_caption(message.chat.id)
        caption = c_caption.format(filename=new_file_name, filesize=humanbytes(message.document.file_size), duration=convert(duration)) if c_caption else f"{new_file_name}"
        caption_mode = await db.get_caption_preference(message.chat.id) or "normal" 

        if c_caption:
            if caption_mode == "normal":
                caption = caption  # No special formatting
            elif caption_mode == "bold":
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
            ph_path = await client.download_media(c_thumb)
            print(f"Thumbnail downloaded successfully. Path: {ph_path}")
        elif file_type  == "video" and message.video and message.video.thumbs:
            ph_path = await client.download_media(message.video.thumbs[0].file_id)
            
        if ph_path:
            Image.open(ph_path).convert("RGB").save(ph_path)
            img = Image.open(ph_path)
            img.resize((320, 320))
            img.save(ph_path, "JPEG")
            logs_caption2 = f"{firstname}\n{user_id}\n{new_file_name}"
            
        dump_settings = {
            'dump_files': await db.get_dump_files(user_id),
            'forward_mode': await db.get_forward_mode(user_id),
            'channel': await db.get_dump_channel(user_id)
        }

        if dump_settings['dump_files']:
            if dump_settings['forward_mode'] == 'Sequence':
                if file_type == "document":
                    response = await client.send_document(
                        chat_id=-1002388905688,
                        document=metadata_path if _bool_metadata else file_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    hinata = response.document.file_id
                elif file_type == "video":
                    response = await client.send_video(
                        chat_id=-1002388905688,
                        video=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    hinata = response.video.file_id
                elif file_type == "audio":
                    response = await client.send_audio(
                        chat_id=-1002388905688,
                        audio=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    hinata = response.audio.file_id

                file_data = {
                    'file_id': hinata,
                    'file_name': new_file_name,
                    'file_type': file_type,
                    'file_path': file_path,
                    'thumb_path': ph_path,
                    'caption': caption,
                    'file_size': message.document.file_size if message.document else None,
                    'duration': message.video.duration if message.video else None,
                    'season': extract_season(new_file_name) or 0,
                    'episode': extract_episode_number(new_file_name) or 0,
                    'quality': extract_quality(new_file_name) or 'Unknown',
                    'volume': extract_volume_number(new_file_name) or 0,
                    'chapter': extract_chapter_number(new_file_name) or 0
                }
                # Pass the consolidated file_data to the database function
                await db.add_to_sequence_queue(user_id, file_data)
                
                if user_id not in sequence_notified or not sequence_notified[user_id]:
                    await message.reply_text("Once you're done renaming all files, use /sequencedump to send them to your dump channel....")
                    sequence_notified[user_id] = True

                await upload_msg.delete()
                
            else:
                if file_type == "document":
                    await client.send_document(
                        chat_id=dump_settings['channel'],
                        document=metadata_path if _bool_metadata else file_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    
                elif file_type == "video":
                    await client.send_video(
                        chat_id=dump_settings['channel'],
                        video=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    
                elif file_type == "audio":
                    await client.send_audio(
                        chat_id=dump_settings['channel'],
                        audio=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    
                await asyncio.sleep(0.5)
                await upload_msg.edit("File Successfully Dumped")
                await asyncio.sleep(5)
                await upload_msg.delete()
                
        else:
            try:
                if file_type == "document":
                    await client.send_document(
                        chat_id=message.chat.id,
                        document=metadata_path if _bool_metadata else file_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    
                elif file_type == "video":
                    await client.send_video(
                        chat_id=message.chat.id,
                        video=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    
                elif file_type == "audio":
                    await client.send_audio(
                        chat_id=message.chat.id,
                        audio=metadata_path if _bool_metadata else file_path,
                        duration=duration,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )                    
                
            except Exception as e:
                await message.reply_text(f"Upload failed: {e}")
            finally:
                await upload_msg.delete()
                if os.path.exists(file_path):
                    os.remove(file_path)
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
        del renaming_operations[file_id]
        
    # Add the task to the user's queue
    user_queue = get_user_queue(user_id)
    await user_queue.put(task)
    
    # Process tasks from the user's queue
    semaphore = get_user_semaphore(user_id)
    if not semaphore.locked():
        while not user_queue.empty():
            task = await user_queue.get()
            await process_task(user_id, task)
            user_queue.task_done()
    
# Define the priority for each quality
quality_priority = {
    "480p": 1,
    "720p": 2,
    "1080p": 3,
    "2160p": 4,
    "4k": 5,
    "8k": 6
}



async def send_custom_message(client, dump_channel, message_data, current_item, first_item=None, last_item=None):
    # Replace placeholders in the message text
    message_text = message_data.get('text', '').replace("{quality}", current_item['quality'])
    message_text = message_text.replace("{title}", extract_title(current_item['file_name']))
    message_text = message_text.replace("{season}", str(current_item.get('season', '')))
    message_text = message_text.replace("{episode}", str(current_item.get('episode', '')))

    # Replace placeholders for first and last episodes
    if first_item:
        message_text = message_text.replace("{firstepisode}", str(first_item.get('episode', '')))
    if last_item:
        message_text = message_text.replace("{lastepisode}", str(last_item.get('episode', '')))

    # Retrieve optional sticker or image IDs
    sticker_id = message_data.get('sticker_id')
    image_id = message_data.get('image_id')

    # Send the appropriate type of message
    try:
        if sticker_id:
            await client.send_sticker(dump_channel, sticker_id)
        elif image_id:
            await client.send_photo(dump_channel, image_id, caption=message_text)
        else:
            await client.send_message(dump_channel, message_text)
    except Exception as e:
        print(f"Failed to send message: {e}")

            
async def send_file(client, dump_channel, file):
    try:
        if file["file_type"] == "document":
            await client.send_document(
                chat_id=dump_channel,
                document=file["file_id"],
                caption=file.get("caption"),
                thumb=file.get("thumb_path"),
            )
        elif file["file_type"] == "video":
            await client.send_video(
                chat_id=dump_channel,
                video=file["file_id"],
                caption=file.get("caption"),
                duration=file.get("duration"),
                thumb=file.get("thumb_path"),
            )
        elif file["file_type"] == "audio":
            await client.send_audio(
                chat_id=dump_channel,
                audio=file["file_id"],
                caption=file.get("caption"),
                duration=file.get("duration"),
                thumb=file.get("thumb_path"),
            )
    except FloodWait as e:
        print(f"Flood wait of {e.value} seconds for file {file['file_name']}")
        await asyncio.sleep(e.value)
        await send_file(client, dump_channel, file)
    except Exception as e:
        print(f"Failed to send {file['file_name']}: {e}")


@Client.on_message(filters.command("sequencedump") & filters.private)
async def sequencedump_command(client, message):
    user_id = message.from_user.id

    # Fetch user's sequence queue and preferences
    queue = await db.get_user_sequence_queue(user_id)
    message_type = await db.get_user_preference(user_id)
    dump_channel = await db.get_dump_channel(user_id)

    if not queue:
        await message.reply_text("Your sequence queue is empty.")
        return

    status_message = await message.reply_text("Processing and sending your sequence. Please wait...")

    # Sort queue
    queue.sort(
        key=lambda x: (
            quality_priority.get(x["quality"], float("inf")),
            x.get("season", 0),
            x.get("episode", 0),
            x.get("volume", 0),
            x.get("chapter", 0),
        )
    )

    first_item = queue[0]
    last_item = queue[-1]

    start_message = await db.get_start_message(user_id)
    end_message = await db.get_end_message(user_id)

    failed_files = []

    try:
        if message_type == "season":
            previous_season = None

            for index, item in enumerate(queue):
                current_season = item["season"]

                if previous_season is not None and previous_season != current_season:
                    if end_message:
                        await send_custom_message(client, dump_channel, end_message, queue[index - 1], queue[0], queue[index - 1])

                if previous_season is None or previous_season != current_season:
                    if start_message:
                        await send_custom_message(client, dump_channel, start_message, item, queue[0], queue[index - 1])

                previous_season = current_season

                try:
                    await send_file(client, dump_channel, item)
                except Exception as e:
                    failed_files.append(f"Failed to send file: {item['file_name']} (Error: {e})")

            if end_message:
                await send_custom_message(client, dump_channel, end_message, last_item, first_item, last_item)

        elif message_type == "quality":
            quality_groups = {}
            for item in queue:
                quality = item["quality"]
                if quality not in quality_groups:
                    quality_groups[quality] = []
                quality_groups[quality].append(item)

            for quality in sorted(quality_groups.keys(), key=lambda q: quality_priority.get(q, float("inf"))):
                files = quality_groups[quality]

                if start_message:
                    await send_custom_message(client, dump_channel, start_message, files[0], files[0], files[-1])

                for file in files:
                    try:
                        await send_file(client, dump_channel, file)
                    except Exception as e:
                        failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                if end_message:
                    await send_custom_message(client, dump_channel, end_message, files[-1], files[0], files[-1])

        elif message_type == "episodebatch":
            episodes = {}
            for item in queue:
                key = (item["season"], item["episode"])
                if key not in episodes:
                    episodes[key] = []
                episodes[key].append(item)

            for (season, episode), files in sorted(episodes.items()):
                files.sort(key=lambda x: quality_priority.get(x["quality"], float("inf")))

                if start_message:
                    await send_custom_message(client, dump_channel, start_message, files[0], files[0], files[-1])

                for file in files:
                    try:
                        await send_file(client, dump_channel, file)
                    except Exception as e:
                        failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                if end_message:
                    await send_custom_message(client, dump_channel, end_message, files[-1], files[0], files[-1])

        elif message_type == "custombatch":
            batch_size = await db.get_user_dumpbatch(user_id)
            if not batch_size:
                return await message.reply_text("Batch size not set. Use /setbatch number to set batch size.")

            for i in range(0, len(queue), batch_size):
                batch = queue[i : i + batch_size]

                if start_message:
                    await send_custom_message(client, dump_channel, start_message, batch[0], batch[0], batch[-1])

                for file in batch:
                    try:
                        await send_file(client, dump_channel, file)
                    except Exception as e:
                        failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                if end_message:
                    await send_custom_message(client, dump_channel, end_message, batch[-1], batch[0], batch[-1])

        elif message_type == "both":
            previous_season = None
            quality_groups = {}

            # Group files by season first, then by quality
            for item in queue:
                season = item["season"]
                quality = item["quality"]

                if season not in quality_groups:
                    quality_groups[season] = {}

                if quality not in quality_groups[season]:
                    quality_groups[season][quality] = []

                quality_groups[season][quality].append(item)

            # Iterate through each season and its quality groups
            for season, quality_files in sorted(quality_groups.items()):
                previous_quality = None

                # Iterate through each quality group for the current season
                for quality, files in sorted(quality_files.items(), key=lambda x: quality_priority.get(x[0], float("inf"))):
                    if start_message:
                        await send_custom_message(client, dump_channel, start_message, files[0], files[0], files[-1])

                    for file in files:
                        try:
                            await send_file(client, dump_channel, file)
                        except Exception as e:
                            failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                    if end_message:
                        await send_custom_message(client, dump_channel, end_message, files[-1], files[0], files[-1])

                # After sending all qualities for a season, move to the next season
                previous_season = season
        
    finally:
        sequence_notified[user_id] = False
        await db.clear_user_sequence_queue(user_id)
        await status_message.delete()

        if failed_files:
            await message.reply_text(f"Files sent, but some failed:\n" + "\n".join(failed_files))
        else:
            await message.reply_text(f"All files sent in sequence to channel {dump_channel}.")            
                
