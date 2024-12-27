import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/ai-selfie-generator"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("selfie"))
async def generate_ai_selfie(client: Client, message: Message):
    # Check if the command is replied to an image
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("⚠️ Please reply to an image with **/selfie** and add a text prompt to generate your AI portrait.")
        return

    # Get the optional text prompt
    text_prompt = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "AI Selfie"

    # Notify the user that the process is starting
    processing_message = await message.reply_text("🎨 Creating your personalized AI portrait, please wait...")

    # Download the image
    image_path = await client.download_media(message.reply_to_message.photo.file_id)
    if not image_path:
        await processing_message.edit_text("❌ Failed to download the image. Please try again.")
        return

    selfie_path = None  # Initialize variable

    try:
        # Send the image and text prompt to the API
        with open(image_path, "rb") as image_file:
            response = requests.post(
                API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file},
                data={"text": text_prompt}
            )

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to generate the AI portrait. Please try again later.")
            return

        # Download the generated AI portrait
        selfie_url = result["output_url"]
        selfie_path = "ai_selfie.jpg"
        selfie_data = requests.get(selfie_url).content
        with open(selfie_path, "wb") as file:
            file.write(selfie_data)

        # Send the AI-generated selfie to the user
        await processing_message.delete()
        await message.reply_photo(selfie_path, caption="🤳 Here is your stunning AI-generated selfie!")
        await message.reply_document(selfie_path, caption="📂 AI Selfie in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files
        if os.path.exists(image_path):
            os.remove(image_path)
        if selfie_path and os.path.exists(selfie_path):
            os.remove(selfie_path)
