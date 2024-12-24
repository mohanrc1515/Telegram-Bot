from pyrogram import Client, filters
from pyrogram.types import Message
import requests
import os

# Path for storing temporary files
TEMP_PATH = "downloads/"

# Replace with your API key from the chosen service
API_KEY = "your_api_key_here"
UPSCALE_API_URL = "https://api.deepai.org/api/super-resolution"  # Example API URL

@Client.on_message(filters.command("upscale") & filters.private)
async def upscale_handler(client: Client, message: Message):
    await message.reply_text(
        "Send me an image, and I'll enhance its quality!"
    )

@Client.on_message(filters.photo & filters.private)
async def process_image(client: Client, message: Message):
    if not message.photo:
        return

    msg = await message.reply_text("Enhancing the image quality... Please wait!")
    
    # Download the photo
    photo_file = await message.download(file_name=f"{TEMP_PATH}original_image.jpg")
    
    try:
        # Enhance the image via API
        enhanced_file = f"{TEMP_PATH}enhanced_image.jpg"
        if upscale_with_api(photo_file, enhanced_file):
            # Send the enhanced image
            await message.reply_photo(
                enhanced_file, caption="Here's your enhanced image!"
            )
            
            await message.reply_document(
                enhanced_file, caption="Here's your enhanced image as a document!"
            )
        else:
            await message.reply_text("Failed to enhance the image. Please try again later.")
    except Exception as e:
        await message.reply_text(f"Error: {e}")
    finally:
        # Cleanup
        if os.path.exists(photo_file):
            os.remove(photo_file)
        if os.path.exists(enhanced_file):
            os.remove(enhanced_file)
    
    await msg.delete()


def upscale_with_api(input_path: str, output_path: str) -> bool:
    """
    Enhance the image using an external API and save the result.
    """
    try:
        with open(input_path, "rb") as image_file:
            response = requests.post(
                UPSCALE_API_URL,
                headers={"api-key": API_KEY},
                files={"image": image_file}
            )
        response_data = response.json()

        if response.status_code == 200 and "output_url" in response_data:
            # Download the enhanced image
            output_image = requests.get(response_data["output_url"])
            with open(output_path, "wb") as out_file:
                out_file.write(output_image.content)
            return True
        else:
            print(f"API Error: {response_data}")
            return False
    except Exception as e:
        print(f"Error in API request: {e}")
        return False
