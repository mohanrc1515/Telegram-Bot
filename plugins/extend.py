import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/zoom-out"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("extend") & filters.reply)
async def extend_image(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/extend** to uncrop or expand it.")
        return

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🔄 Expanding your image, please wait...")

    # Download the image
    download_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not download_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    expanded_image_path = None  # Initialize variable

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
            await processing_message.edit_text("❌ Failed to expand the image. Please try again later.")
            return

        # Download the expanded image
        expanded_image_url = result["output_url"]
        expanded_image_path = "expanded_image.jpg"
        image_data = requests.get(expanded_image_url).content
        with open(expanded_image_path, "wb") as file:
            file.write(image_data)

        # Send the expanded image to the user
        await processing_message.delete()
        await message.reply_photo(expanded_image_path, caption="✨ Here is your expanded image!")
        await message.reply_document(expanded_image_path, caption="📂 Expanded image in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(download_path):
            os.remove(download_path)
        if expanded_image_path and os.path.exists(expanded_image_path):
            os.remove(expanded_image_path)
            
