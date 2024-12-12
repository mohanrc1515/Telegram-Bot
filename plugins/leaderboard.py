from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
from pytz import timezone
from helper.utils import user_mention
import asyncio
from helper.database import db

# Command Leaderboard
@Client.on_message(filters.command("leaderboard"))
async def leaderboard_command(client, message):
    user_id = message.from_user.id
    user_count = await db.get_file_count(user_id)
    await send_leaderboard(client, message.chat.id, include_user_count=True, user_count=user_count)

# Scheduled Leaderboard
async def send_leaderboard(client, chat_id, include_user_count=False, user_count=None):
    try:
        top_users = await db.get_top_users_by_file_count(10)
        leaderboard_message = "🏆 **Leaderboard: Top Renamers** 🏆\n\n"

        if not top_users:
            leaderboard_message += "No users have renamed files yet.\n\n"
        else:
            for rank, user in enumerate(top_users, start=1):
                user_id = user['_id']
                file_count = user.get('file_count', 0)

                try:
                    user_details = await client.get_users(user_id)
                    first_name = user_details.first_name if user_details else "Unknown"
                except Exception:
                    first_name = "Unknown"

                # Avoid notifying users by excluding the `tg://user?id` mention link
                leaderboard_message += f"**{rank}.** {first_name} — **{file_count} files**\n"

        if include_user_count:
            leaderboard_message += f"\n✨ Your Total Files: **{user_count}**\n\n"

        leaderboard_message += "Thank You All ! 🚀\n\n"

        support_button = InlineKeyboardButton("Updates Channel", url="https://t.me/Elites_Bots")
        keyboard = InlineKeyboardMarkup([[support_button]])

        await client.send_message(chat_id, leaderboard_message, reply_markup=keyboard)

    except Exception as e:
        await client.send_message(chat_id, f"An error occurred while generating the leaderboard: {str(e)}")

# Schedule Leaderboard at 23:59 daily
async def schedule_leaderboard(client):
    kolkata_tz = timezone("Asia/Kolkata")
    while True:
        now = datetime.now(kolkata_tz)
        target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)

        if now > target_time:
            target_time += timedelta(days=1)

        await asyncio.sleep((target_time - now).total_seconds())
        # Scheduled leaderboard for the main channel/group without user-specific data
        await send_leaderboard(client, chat_id=-1001883100756, include_user_count=False)

# Start the scheduler on bot startup
@Client.on_start
async def start_scheduler(client):
    asyncio.create_task(schedule_leaderboard(client))


@Client.on_message(filters.command("top_referrals"))
async def top_referrals(client, message):
    try:
        current_user_id = message.from_user.id
        top_referrers = await db.get_top_referrers(limit=10)
        referral_count = await db.get_referral_count(current_user_id)

        if not top_referrers:
            await message.reply("No referrers found.")
            return

        top_referrers_message = "🎉 **Top Referrers** 🎉\n\n"
        for rank, referrer in enumerate(top_referrers, start=1):
            referrer_id = referrer.get("_id")
            referrer_count = referrer.get("referral_count", 0)

            if referrer_id:
                try:
                    # Fetch user details to get the first name
                    user_details = await client.get_users(referrer_id)
                    first_name = user_details.first_name if user_details else "Unknown"
                except Exception as e:
                    first_name = "Unknown"
                    print(f"Error fetching user details: {e}")

                user_mention_text = f"[{first_name}](tg://user?id={referrer_id})"  # Create mention link with first name
                top_referrers_message += f"{rank}. {user_mention_text} - {referrer_count} referrals\n"

        # Add thank you message
        top_referrers_message += f"\nYour Referral Count: {referral_count}"

        support_button = InlineKeyboardButton("Support Group", url="https://t.me/Elites_Assistance")
        keyboard = InlineKeyboardMarkup([[support_button]])

        await message.reply(top_referrers_message, reply_markup=keyboard)
    except Exception as e:
        print(f"Error: {e}")
        await message.reply("An error occurred while fetching the top referrers.")
        
