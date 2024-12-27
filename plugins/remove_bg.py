import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/background-remover"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("remove_bg") & filters.reply)
async def remove_background(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/remove_bg** to remove its background.")
        return

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🔄 Removing the background, please wait...")

    # Download the image
    download_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not download_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    try:
        # Send the image to the API
        with open(download_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file}
            )

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to remove the background. Please try again later.")
            return

        # Download the image with background removed
        bg_removed_url = result["output_url"]
        bg_removed_path = "background_removed_image.png"
        image_data = requests.get(bg_removed_url).content
        with open(bg_removed_path, "wb") as file:
            file.write(image_data)

        # Send the processed image to the user
        await processing_message.delete()
        await message.reply_photo(bg_removed_path, caption="✨ Here is your image with the background removed!")
        await message.reply_document(bg_removed_path, caption="📂 Background removed image in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(download_path):
            os.remove(download_path)
        if os.path.exists(bg_removed_path):
            os.remove(bg_removed_path)
