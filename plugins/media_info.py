import subprocess
import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db
from html_telegraph_poster import TelegraphPoster

# Initialize Telegraph
telegraph = TelegraphPoster(use_api=True)
telegraph.create_api_token("MediaInfoBot")

def get_mediainfo(file_path):
    process = subprocess.Popen(
        ["mediainfo", file_path, "--Output=HTML"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"Error getting media info: {stderr.decode().strip()}")
    return stdout.decode().strip()

@Client.on_message(filters.command("mediainfo") & filters.chat(-1001883100756))
async def mediainfo_handler(client: Client, message: Message):
    if not message.reply_to_message or (not message.reply_to_message.document and not message.reply_to_message.video):
        await message.reply_text("Please reply to a document or video to retrieve its media info.")
        return

    reply = message.reply_to_message
    media = reply.document or reply.video

    processing_message = await message.reply_text("📥 Downloading your file. Please wait...")

    try:
        # Download media
        file_path = await client.download_media(media)

        # Extract media info
        media_info_html = get_mediainfo(file_path)
        media_info_html = (
            f"<strong>Elites Botz</strong><br>"
            f"<strong>MediaInfo X</strong><br>"
            f"{media_info_html}"
            f"<p>Designed By Sʜᴀᴅᴏᴡ 様</p>"
        )

        # Post media info to Telegraph
        response = telegraph.post(
            title="MediaInfo",
            author="Elites Botz",
            author_url="https://t.me/Elites_Bots",
            text=media_info_html
        )
        link = f"https://graph.org/{response['path']}"

        # Save media info to HTML file
        html_file_path = f"Media Info.html"
        with open(html_file_path, "w") as file:
            file.write(media_info_html)

        # Store media info in the database
        media_info_data = {
            'media_info': media_info_html,
            'media_id': media.file_id
        }
        await db.store_media_info_in_db(media_info_data)

        # Prepare response message and button
        message_text = (
            f"📊 MediaInfo X"
        )
        button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("📄 View on Telegraph", url=link)]]
        )

        # Send media info as a document with a button
        await message.reply_document(
            document=html_file_path,
            caption=message_text,
            reply_markup=button
        )
        await reply.delete()

    except Exception as e:
        await message.reply_text(f"⚠️ Error: {e}")

    finally:
        await processing_message.delete()
        if os.path.exists(file_path):
            os.remove(file_path)
        if os.path.exists(html_file_path):
            os.remove(html_file_path)
