import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/ai-headshots"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("headshot"))
async def generate_headshot(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/headshot** to generate a professional AI headshot.")
        return

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🎭 Generating a professional AI headshot, please wait...")

    # Download the image
    image_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not image_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    headshot_path = None  # Initialize variable

    try:
        # Send the image to the API
        with open(image_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file}
            )

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to generate the AI headshot. Please try again later.")
            return

        # Download the generated headshot
        headshot_url = result["output_url"]
        headshot_path = "ai_headshot.jpg"
        headshot_data = requests.get(headshot_url).content
        with open(headshot_path, "wb") as file:
            file.write(headshot_data)

        # Send the AI-generated headshot to the user
        await processing_message.delete()
        await message.reply_photo(headshot_path, caption="📸 Here is your AI-generated professional headshot!")
      #  await message.reply_document(headshot_path, caption="📂 AI Headshot in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(image_path):
            os.remove(image_path)
        if headshot_path and os.path.exists(headshot_path):
            os.remove(headshot_path)
