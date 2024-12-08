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
import os, time, re, asyncio, pytz

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
    download_msg = await message.reply_text("Your file has been added to the queue and will be processed soon.")
    await asyncio.sleep(1)
   
async def safe_edit_message(message, text, delay=0):
    try:
        if delay:
            await asyncio.sleep(delay)  # Add a delay to avoid rate limits
        await message.edit(text)
    except FloodWait as e:
        print(f"FloodWait occurred for {e.value} seconds. Retrying...")
        await asyncio.sleep(e.value)  # Wait for the required time
        await safe_edit_message(message, text)  # Retry the edit
    except Exception as e:
        print(f"Failed to edit message: {e}")

# Replace your edits with the `safe_edit_message` function
async def task():
    await asyncio.sleep(1)  # Prevent excessive rate limiting
    await safe_edit_message(download_msg, "Processing... ⚡")
    try:
        path = await client.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started....", download_msg, time.time())
        )
    except FloodWait as e:
        await asyncio.sleep(e.value) 
        await task()
    except Exception as e:
        # Mark the file as ignored
        del renaming_operations[file_id]
        return await safe_edit_message(download_msg, str(e))
            
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
        await safe_edit_message(download_msg, "Processing.... ⚡")
        
    duration = 0
    try:
        metadata = extractMetadata(createParser(file_path))
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    except Exception as e:
        print(f"Error getting duration: {e}")
        
    try:
        upload_msg = await safe_edit_message(download_msg, "Trying To Upload...")
    except FloodWait as e:
        await asyncio.sleep(e.value)  # Wait dynamically if FloodWait error occurs
        upload_msg = await safe_edit_message(download_msg, "Trying To Upload...")  # Retry edit
                            
        ph_path = None
        c_caption = await db.get_caption(message.chat.id)
        c_thumb = await db.get_thumbnail(message.chat.id)
        caption = c_caption.format(filename=new_file_name, filesize=humanbytes(message.document.file_size), duration=convert(duration)) if c_caption else f"**{new_file_name}**"
        
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
        
    user_queue = get_user_queue(user_id)
    await user_queue.put(task)
    
    semaphore = get_user_semaphore(user_id)
    if not semaphore.locked():
        while not user_queue.empty():
            task = await user_queue.get()
            await process_task(user_id, task)
            user_queue.task_done()

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

    # Sorting: Prioritize by season, episode, volume, then chapter
    queue.sort(key=lambda x: (x['season'], x['episode'], x['volume'], x['chapter']))

    dump_channel = await db.get_dump_channel(user_id)
    if not dump_channel:
        return await message.reply_text("No dump channel found. Please connect it using /dump.")

    status_message = await message.reply_text("Starting to send files in sequence to channel...")

    # Dynamic method mapping for file types
    send_methods = {
        'document': client.send_document,
        'video': client.send_video,
        'audio': client.send_audio,
        'pdf': client.send_document
    }

    failed_files = []

    for item in queue:
        send_method = send_methods.get(item['file_type'])

        if not send_method:
            failed_files.append(f"Unsupported media type: {item['file_name']} ({item['file_type']})")
            continue

        try:
            # Retry mechanism to handle flood wait
            await send_file_with_retry(send_method, dump_channel, item)
        except Exception as e:
            failed_files.append(f"Failed to send file: {item['file_name']} (Error: {e})")

    sequence_notified[user_id] = False
    await db.clear_user_sequence_queue(user_id)
    await client.delete_messages(chat_id=message.chat.id, message_ids=status_message.id)

    if failed_files:
        await message.reply_text(f"Files sent, but some failed:\n" + "\n".join(failed_files))
    else:
        await message.reply_text(f"All files sent in sequence to channel {dump_channel}.")

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


@Client.on_message(filters.command("cleardump") & filters.private)
async def clear_sequence_dump(client, message: Message):
    user_id = message.from_user.id    
    result = await db.clear_user_sequence_queue(user_id)
    if result:
        await message.reply_text("Your sequence dump has been successfully cleared.")
    else:
        await message.reply_text("You don't have any files in your sequence dump.")
        
