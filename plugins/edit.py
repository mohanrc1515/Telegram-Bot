import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/image-editor"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("edit"))
async def edit_image(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/edit** to edit it using AI.")
        return

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🔄 Editing your image, please wait...")

    # Download the image
    image_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not image_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    try:
        # Send the image to the API with additional text prompt if needed
        with open(image_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file, "text": ("", "")}  # Add text here if necessary
            )

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to edit the image. Please try again later.")
            return

        # Download the edited image
        edited_url = result["output_url"]
        edited_path = "edited_image.jpg"
        edited_data = requests.get(edited_url).content
        with open(edited_path, "wb") as file:
            file.write(edited_data)

        # Send the edited image to the user
        await processing_message.delete()
        await message.reply_photo(edited_path, caption="✨ Here is your edited image!")
        await message.reply_document(edited_path, caption="📂 Edited image in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(image_path):
            os.remove(image_path)
        if os.path.exists(edited_path):
            os.remove(edited_path)
