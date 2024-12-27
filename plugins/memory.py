from pyrogram import Client, filters
import psutil
from asyncio import sleep
from config import Config

# /memory command to show current memory status
@Client.on_message(filters.command("memory") & filters.private)
async def show_memory(client, message):
    memory = psutil.virtual_memory()
    total = memory.total / (1024 ** 3)  # Convert to GB
    used = memory.used / (1024 ** 3)  # Convert to GB
    free = memory.available / (1024 ** 3)  # Convert to GB
    percent = memory.percent

    response = (
        f"**💾 Memory Status**\n"
        f"**Total Memory:** {total:.2f} GB\n"
        f"**Used Memory:** {used:.2f} GB ({percent}%)\n"
        f"**Available Memory:** {free:.2f} GB\n"
    )
    await message.reply_text(response)
