# Necessary Imports
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from helper.database import db
from helper.extraction import *

# Start sequencing command
@Client.on_message(filters.command("startsequence") & filters.private)
async def start_sequence(client, message: Message):
    user_id = message.from_user.id
    
    if not await db.is_user_authorized(user_id):
        await message.reply_text(Config.USER_REPLY)
        return
    
    if await db.is_user_sequence_mode(user_id):
        await message.reply_text("You already started a sequence. Please send files or end it with /endsequence.")
    else:
        await db.set_user_sequence_mode(user_id, True)
        await db.initialize_sequence_queue(user_id)  # Initialize the sequence queue in the database
        await message.reply_text("Sequence started! Please send the files you want to sequence.")

# End sequencing command
@Client.on_message(filters.command("endsequence") & filters.private)
async def end_sequence(client, message: Message):
    user_id = message.from_user.id

    if not await db.is_user_sequence_mode(user_id):
        return await message.reply_text("You have not started sequencing yet. Enter /startsequence to activate sequencing mode.")
    
    await db.set_user_sequence_mode(user_id, False)
    queue = await db.get_sequence_queue(user_id)  # Retrieve the user's sequence queue
    
    if not queue:
        return await message.reply_text("No files were sequenced.")

    # Sort the files based on volume, season, chapter, and episode
    queue.sort(key=lambda x: (
        x.get('volume', 0),
        x.get('season', 0),
        x.get('chapter', 0),
        x.get('episode', 0)
    ))

    # Send sorted files back to the user
    for item in queue:
        file_type = item.get('file_type', 'document')
        file_id = item['file_id']
        caption = item.get('caption', 'No name available')
        
        if file_type == 'video':
            await client.send_video(chat_id=message.chat.id, video=file_id, caption=caption)
        elif file_type == 'audio':
            await client.send_audio(chat_id=message.chat.id, audio=file_id, caption=caption)
        else:  # Default to sending as a document
            await client.send_document(chat_id=message.chat.id, document=file_id, caption=caption)

    await message.reply_text(f"Sequencing completed. Sent {len(queue)} files.")
    await db.clear_sequence_queue(user_id)
    
