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
sequencing_queue = {}
user_sequence_mode = {}
sequence_notified = {}
thumbnail_extraction_mode = {}
user_files = {}
file_count = {}
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
        user_semaphores[user_id] = Semaphore(4)
    return user_semaphores[user_id]

async def process_task(user_id, task):
    semaphore = get_user_semaphore(user_id)
    async with semaphore:
        await task()
        await asyncio.sleep(5)

async def send_file_with_retry(send_method, dump_channel, item):
    try:
        # Attempt to send the file
        await send_method(dump_channel, **{
            item['file_type']: item['file_id'],
            'caption': item['file_name']
        })
    except FloodWait as e:
        # If FloodWait occurs, wait for the specified time and retry
        print(f"Flood wait of {e.value} seconds for file {item['file_name']}")
        await asyncio.sleep(e.value)
        await send_file_with_retry(send_method, dump_channel, item)

async def send_custom_message(client, dump_channel, message_data, current_item, first_item=None, last_item=None):
    # Replace placeholders in the message text
    message_text = message_data.get('text', '').replace("{quality}", current_item['quality'])
    message_text = message_text.replace("{title}", extract_title(current_item['file_name']))
    message_text = message_text.replace("{season}", str(current_item.get('season', '')))
    message_text = message_text.replace("{episode}", str(current_item.get('episode', '')))
    
    
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
        
async def notify_progress(message, total, completed):
    """
    Notify the user about the current progress.
    """
    if completed % 10 == 0 or completed == total:
        await message.edit(f"Processing files: {completed}/{total} completed...")
        

# Start sequencing command
@Client.on_message(filters.command("startsequence") & filters.private)
async def start_sequence(client, message: Message):
    user_id = message.from_user.id   
    if not await db.is_user_authorized(user_id):
        await message.reply_text(Config.USER_REPLY)
        return    
        
    if user_sequence_mode.get(user_id, False):
        await message.reply_text("You already started a sequence. Please send files or end it with /endsequence.")
    else:
        sequencing_queue[user_id] = []
        user_sequence_mode[user_id] = True
        await message.reply_text("Sequence started! Please send the files you want to sequence.")
        
@Client.on_message(filters.command("endsequence") & filters.private)
async def end_sequence(client, message):
    user_id = message.from_user.id
    # Check if sequencing is active for the user
    if user_id not in user_sequence_mode or not user_sequence_mode[user_id]:
        return await message.reply_text("You have not started sequencing yet. Enter /startsequence to activate sequencing mode.")  

    # Disable sequencing mode
    user_sequence_mode[user_id] = False
    queue = sequencing_queue.pop(user_id, [])
    
    if not queue:
        return await message.reply_text("No files were sequenced.")
    # Sort the files based on volume, season, chapter, and episode
    queue.sort(key=lambda x: (
        x.get('volume', 0),    # Prioritize by volume
        x.get('season', 0),    # Then by season
        x.get('chapter', 0),   # Then by chapter
        x.get('episode', 0)    # Finally by episode
    ))
    # Send sorted files back to user
    for item in queue:
        file_type = item.get('file_type', 'document')
        file_id = item['file_id']
        caption = item.get('file_name', 'No name available')
        if file_type == 'video':
            await client.send_video(
                chat_id=message.chat.id,
                video=file_id,
                caption=caption
            )
        elif file_type == 'audio':
            await client.send_audio(
                chat_id=message.chat.id,
                audio=file_id,
                caption=caption
            )
        else:  # Default to sending as a document
            await client.send_document(
                chat_id=message.chat.id,
                document=file_id,
                caption=caption
            )
    await message.reply_text(f"Sequencing completed. Sent {len(queue)} files.")

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

    if user_id in user_sequence_mode and user_sequence_mode[user_id]:
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
                sequencing_queue[user_id].append({
                    'file_id': message.document.file_id if message.document else (message.video.file_id if message.video else message.audio.file_id),
                    'file_name': file_name,
                    'season': int(season),
                    'episode': int(episode),
                    'volume': int(volume),
                    'chapter': int(chapter)
                })
                await message.reply_text("The file has been successfully received and integrated into the sequencing.")
            else:
                await message.reply_text(f"Could not extract sufficient information from '{file_name}'. File was not added to the queue.")
        else:
            await message.reply_text("File name could not be determined.")
        return

    if not format_template:
        return await message.reply_text("Please Set An Auto Rename Format First Using /autorename")    
        
    # Initialize user_files and file_count if not present
    if user_id not in user_files:
        user_files[user_id] = []
    if user_id not in file_count:
        file_count[user_id] = await db.get_file_count(user_id)  # Fetch from DB

    # Update file count
    file_count[user_id] += 1
    await db.update_file_count(user_id, file_count[user_id])
    
    user_files[user_id].append(message)
    
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
        await asyncio.sleep(1)
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
            await download_msg.edit("Processing....  ⚡")
            
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
        c_caption = await db.get_caption(message.chat.id)
        c_thumb = await db.get_thumbnail(message.chat.id)        
        caption = c_caption.format(filename=new_file_name, filesize=humanbytes(message.document.file_size), duration=convert(duration)) if c_caption else f"**{new_file_name}**"
        
        # Initialize user-specific data if not present
        await asyncio.sleep(1)
        if user_id not in user_files:
            user_files[user_id] = []  # List for storing user-specific files/messages
        if user_id not in file_count:
            file_count[user_id] = await db.get_file_count(user_id)  # Fetch user's file count from DB

    # Fetch and initialize global counters
        if "global_stats" not in globals():
            global_stats = {
                "total_files_renamed": await db.get_total_files_renamed(),
                "total_renamed_size": await db.get_total_renamed_size()
            }
 
        await asyncio.sleep(1)
        # Increment user-specific file count
        file_count[user_id] += 1
        await db.update_file_count(user_id, file_count[user_id])

         # Extract file size based on file type
        file_size = 0
        if message.document:
            file_size = message.document.file_size
        elif message.video:
            file_size = message.video.file_size
        elif message.audio:
            file_size = message.audio.file_size
        elif message.photo:
            # Telegram photos provide a list of sizes, use the largest one
            file_size = message.photo[-1].file_size if message.photo else 0
        else:
            file_size = 0  # Default to 0 if no file size is found

        await asyncio.sleep(1)
        # Increment global counters
        global_stats["total_files_renamed"] += 1
        await db.update_total_files_renamed(global_stats["total_files_renamed"])

        global_stats["total_renamed_size"] += file_size
        await db.update_total_renamed_size(global_stats["total_renamed_size"])

        # Append the current file/message to the user's file list
        user_files[user_id].append(message)       
        
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
            await client.send_document(Config.FILES_CHANNEL, document=file_path, caption=logs_caption2)
            
        dump_settings = {
            'dump_files': await db.get_dump_files(user_id),
            'forward_mode': await db.get_forward_mode(user_id),
            'channel': await db.get_dump_channel(user_id)
        }

        if dump_settings['dump_files']:
            if dump_settings['forward_mode'] == 'Sequence':
                # Upload the file first and get the response
                if file_type == "document":
                    response = await client.send_document(
                        chat_id=-1002388905688,
                        document=metadata_path if _bool_metadata else file_path,
                        thumb=ph_path,
                        caption=caption,
                        progress=progress_for_pyrogram,
                        progress_args=("Uploading...", upload_msg, time.time())
                    )
                    hinata = response.document.file_id  # Get the file ID
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
                    hinata = response.video.file_id  # Get the file ID
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

                # Add the file to the sequence queue
                await db.add_to_sequence_queue(user_id, {
                    'file_id': hinata,
                    'file_name': new_file_name,
                    'thumb_path': ph_path,
                    'caption': caption,
                    'file_type': file_type,
                    'file_path': file_path
                })

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
                    
                # Delete the progress message after upload
                await sleep(0.5)
                await upload_msg.edit("File Successfully Dumped")
                await asyncio.sleep(5)
                await upload_msg.delete()
                
        else:
            # Regular upload to the user
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
                # Clean up: delete progress message after uploading
                await upload_msg.delete()
                if os.path.exists(file_path):
                    os.remove(file_path)
                if ph_path and os.path.exists(ph_path):
                    os.remove(ph_path)
        # Remove the file_id from renaming_operations to allow further processing
        del renaming_operations[file_id]
        #del user_files[user_id]
        
    # Add the task to the user's queue
    user_queue = get_user_queue(user_id)
    await user_queue.put(task)
    
    # Process tasks from the user's queue
    semaphore = get_user_semaphore(user_id)
    if not semaphore.locked():
        # If the semaphore is not locked, process tasks from the queue
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

@Client.on_message(filters.command("sequencedump") & filters.private)
async def sequence_dump(client, message: Message):
    user_id = message.from_user.id
    queue = await db.get_user_sequence_queue(user_id)

    if not queue:
        return await message.reply_text("No files found in your sequence queue.")

    # Extract metadata and sort the queue
    for item in queue:
        file_name = item['file_name']
        item['season'] = int(extract_season(file_name) or 0)
        item['episode'] = int(extract_episode_number(file_name) or 0)
        item['chapter'] = int(extract_chapter_number(file_name) or 0)
        item['volume'] = int(extract_volume_number(file_name) or 0)
        item['quality'] = extract_quality(file_name) or '0'

    # Sorting by season, episode, volume, chapter, then quality
    queue.sort(key=lambda x: (
        quality_priority.get(x['quality'], float('inf')),
        x['season'],
        x['episode'],
        x['volume'],
        x['chapter']
    ))

    dump_channel = await db.get_dump_channel(user_id)
    if not dump_channel:
        return await message.reply_text("No dump channel found. Please connect it using /dump.")

    status_message = await message.reply_text("Starting to send files in sequence to channel...")
    send_methods = {
        'document': client.send_document,
        'video': client.send_video,
        'audio': client.send_audio,
        'pdf': client.send_document
    }

    failed_files = []
    previous_season = None
    previous_quality = None

    # Get user preference (season or quality or both) from the DB
    message_type = await db.get_user_preference(user_id)  # Retrieve from DB

    for index, item in enumerate(queue):
        current_season = item['season']
        current_quality = item['quality']
        send_method = send_methods.get(item['file_type'])

        # Handle season or quality changes based on user preference
        if message_type == 'season':
            if previous_season is not None and previous_season != current_season:
                end_msg = await db.get_end_message(user_id)
                if end_msg:
                    await send_custom_message(client, dump_channel, end_msg, item, queue[0], queue[index - 1])

            if previous_season is None or previous_season != current_season:
                start_msg = await db.get_start_message(user_id)
                if start_msg:
                    await send_custom_message(client, dump_channel, start_msg, item, queue[0])

            previous_season = current_season

        elif message_type == 'quality':
                # Group files by quality
                quality_groups = {}
                for item in queue:
                    quality = item['quality']
                    if quality not in quality_groups:
                        quality_groups[quality] = []
                    quality_groups[quality].append(item)

                # Send files by quality priority
                for quality in sorted(quality_groups.keys(), key=lambda q: quality_priority.get(q, float('inf'))):
                    files = quality_groups[quality]

                    # Send start message for the quality group
                    start_msg = await db.get_start_message(user_id)
                    if start_msg:
                        await send_custom_message(client, dump_channel, start_msg, files[0])

                    for file in files:
                        send_method = send_methods.get(file['file_type'])
                        if not send_method:
                            failed_files.append(f"Unsupported media type: {file['file_name']} ({file['file_type']})")
                            continue

                        try:
                            await send_file_with_retry(send_method, dump_channel, file)
                        except Exception as e:
                            failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                    # Send end message for the quality group
                    end_msg = await db.get_end_message(user_id)
                    if end_msg:
                        await send_custom_message(client, dump_channel, end_msg, files[-1])

            # Send final end message if needed
            if previous_quality is not None:
                end_msg = await db.get_end_message(user_id)
                if end_msg:
                    await send_custom_message(client, dump_channel, end_msg, queue[-1], queue[0], queue[-1])

        elif message_type == 'both':
            # Handle both season and quality changes
            if (previous_season is not None and previous_season != current_season) or \
               (previous_quality is not None and previous_quality != current_quality):
                end_msg = await db.get_end_message(user_id)
                if end_msg:
                    await send_custom_message(client, dump_channel, end_msg, item, queue[0], queue[index - 1])

            if previous_season is None or previous_season != current_season or previous_quality is None or previous_quality != current_quality:
                start_msg = await db.get_start_message(user_id)
                if start_msg:
                    await send_custom_message(client, dump_channel, start_msg, item, queue[0])

            previous_season = current_season
            previous_quality = current_quality
            
        elif message_type == 'episodebatch':
            # Group files by episode
            episodes = {}  # Ensure `episodes` is initialized here
            for item in queue:
                key = (item['season'], item['episode'])  # Grouping by season and episode
                if key not in episodes:
                    episodes[key] = []
                episodes[key].append(item)

            for (season, episode), files in sorted(episodes.items()):
                # Sort the files of the same episode by quality
                files.sort(key=lambda x: quality_priority.get(x['quality'], float('inf')))

                # Send start message for this episode group
                start_msg = await db.get_start_message(user_id)
                if start_msg:
                    await send_custom_message(client, dump_channel, start_msg, files[0])

                # Send all files for the current episode
                for file in files:
                    send_method = send_methods.get(file['file_type'])
                    if not send_method:
                        failed_files.append(f"Unsupported media type: {file['file_name']} ({file['file_type']})")
                        continue

                    try:
                        await send_file_with_retry(send_method, dump_channel, file)
                    except Exception as e:
                        failed_files.append(f"Failed to send file: {file['file_name']} (Error: {e})")

                # Send end message for this episode group
                end_msg = await db.get_end_message(user_id)
                if end_msg:
                    await send_custom_message(client, dump_channel, end_msg, files[-1])
            
            episodes[user_id] = False  # This should be safe now, as `episode` is a dictionary
    
        # Send the file
        if not send_method:
            failed_files.append(f"Unsupported media type: {item['file_name']} ({item['file_type']})")
            continue

        try:
            await send_file_with_retry(send_method, dump_channel, item)
        except Exception as e:
            failed_files.append(f"Failed to send file: {item['file_name']} (Error: {e})")

    # Send final end message if needed
    if previous_season is not None or previous_quality is not None:
        end_msg = await db.get_end_message(user_id)
        if end_msg:
            await send_custom_message(client, dump_channel, end_msg, queue[-1], queue[0], queue[-1])

    sequence_notified[user_id] = False
    await db.clear_user_sequence_queue(user_id)
    await status_message.delete()

    if failed_files:
        await message.reply_text(f"Files sent, but some failed:\n" + "\n".join(failed_files))
    else:
        await message.reply_text(f"All files sent in sequence to channel {dump_channel}.")


@Client.on_message(filters.command("cleardump") & filters.private)
async def clear_sequence_dump(client, message: Message):
    user_id = message.from_user.id

    user_queue = await db.get_user_sequence_queue(user_id)
    if user_queue:
        sequence_notified[user_id] = False
        await db.clear_user_sequence_queue(user_id)
        await message.reply_text("Your sequence dump has been successfully cleared.")
    else:
        await message.reply_text("You don't have any files in your sequence dump.")

