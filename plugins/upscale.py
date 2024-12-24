import os
import tempfile
import requests
from pyrogram import Client, filters
from pyrogram.types import Message

UPSCALE_API_URL = "YOUR_API_URL"  # Add your upscale API URL here
API_KEY = "YOUR_API_KEY"  # Add your API key here

@Client.on_message(filters.command("upscale") & filters.reply & filters.private)
async def upscale_image(client: Client, message: Message):
    if not message.reply_to_message or not message.reply_to_message.photo:
        await message.reply_text("Please reply to an image with the /upscale command.")
        return

    msg = await message.reply_text("Enhancing the image quality... Please wait!")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        photo_file = await message.reply_to_message.download(file_name=os.path.join(temp_dir, "original_image.jpg"))
        enhanced_file = os.path.join(temp_dir, "enhanced_image.jpg")

        try:
            # Enhance the image via API
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
