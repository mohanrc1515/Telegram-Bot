import psutil
from asyncio import sleep
from config import Config

# Monitor memory usage and notify in log channel
async def monitor_memory(client):
    log_channel = Config.LOG_CHANNEL  # Replace with your log channel ID
    notified_50 = False
    notified_80 = False

    while True:
        memory = psutil.virtual_memory()
        usage_percent = memory.percent

        if usage_percent >= 80 and not notified_80:
            await client.send_message(log_channel, "⚠️ **Memory Alert**: 80% memory used.")
            notified_80 = True
        elif usage_percent >= 50 and not notified_50:
            await client.send_message(log_channel, "⚠️ **Memory Alert**: 50% memory used.")
            notified_50 = True
        elif usage_percent < 50:  # Reset notifications if memory drops below 50%
            notified_50 = False
            notified_80 = False

        await sleep(60)  # Check every 60 seconds


# Start memory monitoring
async def start_monitoring(client):
    asyncio.create_task(monitor_memory(client))


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


# Add memory monitoring to bot initialization
@Client.on_start
async def on_start(client):
    print("Bot started.")
    await start_monitoring(client)
