import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/colorizer"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("colorize"))
async def colorize_image(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/colorize** to add color to it.")
        return

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🎨 Adding color to your image, please wait...")

    # Download the image
    download_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not download_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    colorized_image_path = None  # Initialize variable

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
            await processing_message.edit_text("❌ Failed to colorize the image. Please try again later.")
            return

        # Download the colorized image
        colorized_image_url = result["output_url"]
        colorized_image_path = "colorized_image.jpg"
        image_data = requests.get(colorized_image_url).content
        with open(colorized_image_path, "wb") as file:
            file.write(image_data)

        # Send the colorized image to the user
        await processing_message.delete()
        await message.reply_photo(colorized_image_path, caption="Here is your colorized image!")
      #  await message.reply_document(colorized_image_path, caption="📂 Colorized image in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(download_path):
            os.remove(download_path)
        if colorized_image_path and os.path.exists(colorized_image_path):
            os.remove(colorized_image_path)
          
