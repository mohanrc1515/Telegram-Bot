import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://deep-image.ai/rest_api/process_result"
API_KEY = "8a924950-c826-11ef-a1c6-c3999b4db0de"

@Client.on_message(filters.command("upscale"))
async def upscale_image(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with the **/upscale** command to enhance it.")
        return

    # Notify the user that processing has started
    processing_message = await message.reply_text("🔄 Processing your image, please wait...")

    # Initialize variables for cleanup
    download_path = None
    enhanced_image_path = None

    try:
        # Download the image
        download_path = await client.download_media(message.reply_to_message.photo.file_id)
        if not download_path:
            await processing_message.edit_text("❌ Failed to download the image. Please try again.")
            return

        # Send the image to the API
        with open(download_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file}
            )

        # Check if the response was successful
        if response.status_code != 200:
            await processing_message.edit_text("❌ Error with API request. Please try again later.")
            return

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to upscale the image. Please try again later.")
            return

        # Download the enhanced image
        enhanced_image_url = result["output_url"]
        enhanced_image_path = "enhanced_image.jpg"
        image_data = requests.get(enhanced_image_url).content
        with open(enhanced_image_path, "wb") as file:
            file.write(image_data)

        # Send the enhanced image
        await processing_message.delete()
        await message.reply_photo(enhanced_image_path, caption="Here is your enhanced image!")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if download_path and os.path.exists(download_path):
            os.remove(download_path)
        if enhanced_image_path and os.path.exists(enhanced_image_path):
            os.remove(enhanced_image_path)
