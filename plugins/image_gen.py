import requests
from pyrogram import Client, filters
from pyrogram.types import Message
import os

# DeepAI API details
API_URL = "https://api.deepai.org/api/text2img"
API_KEY = "618a0be5-1f50-4a2d-876b-ed3f10f479f7"

@Client.on_message(filters.command("gen"))
async def generate_image(client: Client, message: Message):
    # Check if a description is provided
    if len(message.command) < 2:
        await message.reply_text("⚠️ Please provide a description for the image. Example:\n`/gen a futuristic city at night`")
        return

    # Combine the text description from the command
    description = " ".join(message.command[1:])

    # Notify the user that the generation process has started
    processing_message = await message.reply_text(f"🔄 Generating an image for: **{description}**\nPlease wait...")

    generated_image_path = None  # Ensure the variable is initialized here

    try:
        # Send the description to the API
        response = requests.post(
            API_URL,
            headers={"api-key": API_KEY},
            data={"text": description}
        )

        result = response.json()
        if "output_url" not in result:
            await processing_message.edit_text("❌ Failed to generate the image. Please try again later.")
            return

        # Download the generated image
        generated_image_url = result["output_url"]
        generated_image_path = "generated_image.jpg"
        image_data = requests.get(generated_image_url).content
        with open(generated_image_path, "wb") as file:
            file.write(image_data)

        # Send the generated image to the user
        await processing_message.delete()
        await message.reply_photo(generated_image_path, caption=f"✨ Here is your generated image for:\n**{description}**")
        await message.reply_document(generated_image_path, caption="📂 Generated image in file format.")

    except Exception as e:
        await processing_message.edit_text(f"❌ An error occurred: {e}")

    finally:
        # Clean up temporary files if the path is defined
        if generated_image_path and os.path.exists(generated_image_path):
            os.remove(generated_image_path)
