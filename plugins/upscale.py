import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/torch-srgan"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("upscale") & filters.reply)
async def upscale_image(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("Please reply to an image with /upscale.")
        return

    # Download the replied image
    download_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not download_path:
        await message.reply_text("Failed to download the image.")
        return

    try:
        # Send image to DeepAI API
        with open(download_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file}
            )

        # Parse the response
        result = response.json()
        if "output_url" not in result:
            await message.reply_text("Failed to upscale the image.")
            return

        # Download the enhanced image
        enhanced_image_url = result["output_url"]
        enhanced_image_path = "enhanced_image.jpg"
        image_data = requests.get(enhanced_image_url).content
        with open(enhanced_image_path, "wb") as file:
            file.write(image_data)

        # Send the enhanced image back to the user
        await message.reply_photo(enhanced_image_path, caption="Here is your enhanced image!")
        await message.reply_document(enhanced_image_path, caption="Enhanced image in file format.")

    except Exception as e:
        await message.reply_text(f"An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(download_path):
            os.remove(download_path)
        if os.path.exists(enhanced_image_path):
            os.remove(enhanced_image_path)
