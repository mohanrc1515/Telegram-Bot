from pyrogram import Client, filters
from datetime import datetime
from helper.database import db
from config import Config

# Command: /nofap
@Client.on_message(filters.command("nofap"))
async def nofap_command(client, message):
    user_id = message.from_user.id

    # Get the last fap time from the database
    last_fap_time = await db.get_last_fap_time(user_id)

    if not last_fap_time:
        await message.reply("When was your last time? (Please provide the date and time in format: YYYY-MM-DD HH:MM)")
        return

    # Calculate the time difference
    current_time = datetime.now()
    time_difference = current_time - last_fap_time

    days = time_difference.days
    hours, remainder = divmod(time_difference.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    await message.reply(f"You haven't fapped for **{days} days, {hours} hours, and {minutes} minutes**. Stay strong! 💪")

# Command: /fapped
@Client.on_message(filters.command("fapped"))
async def fapped_command(client, message):
    user_id = message.from_user.id

    # Save the current time as the last fap time in the database
    await db.set_last_fap_time(user_id, datetime.now())

    await message.reply("Your timer has been reset. Stay strong next time! 💪")

# Handle text messages that are not commands
@Client.on_message(filters.text & ~filters.command(["nofap", "fapped"]))
async def handle_text_messages(client, message):
    user_id = message.from_user.id

    # Check if the user has already set a last fap time
    last_fap_time = await db.get_last_fap_time(user_id)

    if not last_fap_time:
        try:
            # Parse the date input
            date_str = message.text.strip()
            last_fap_time = datetime.strptime(date_str, "%Y-%m-%d %H:%M")

            # Save the last fap time in the database
            await db.set_last_fap_time(user_id, last_fap_time)

            await message.reply("Your last fap time has been recorded. Use /nofap to check your progress!")
        except ValueError:
            await message.reply("Invalid date format. Please use the format: YYYY-MM-DD HH:MM")
