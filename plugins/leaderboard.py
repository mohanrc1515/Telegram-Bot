from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from helper.database import db
from helper.utils import user_mention

@Client.on_message(filters.command("leaderboard"))
async def leaderboard_command(client, message):
    top_users = await db.get_top_users_by_file_count(10)  # Get top 10 users by file count
    user_id = message.from_user.id
    user_count = await db.get_file_count(user_id)  # Fetch total file count for the current user
      
    if not top_users:
        await message.reply("No users have renamed files yet.")
        return

    leaderboard_message = "<u>🏆 **Our Top Renamers** 🏆</u>\n\n"
    for rank, user in enumerate(top_users, start=1):
        user_id = user['_id']
        file_count = user.get('file_count', 0)
        
        # Fetch user details to get the first name
        user_details = await client.get_users(user_id)
        first_name = user_details.first_name if user_details else "Unknown"
        
        user_mention = f"[{first_name}](tg://user?id={user_id})"  # Create mention link with first name
        leaderboard_message += f"{rank}. {user_mention} - {file_count} files\n"
    
    # Add thank you message
    leaderboard_message += f"\n⚡ Your File Count: {user_count}\n\nThanks for using the bot! 🚀"

    support_button = InlineKeyboardButton("Bots Channel", url="https://t.me/Elites_Bots")
    keyboard = InlineKeyboardMarkup([[support_button]])

    await message.reply(leaderboard_message, reply_markup=keyboard)
   
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
        await message.reply("An error occurred while fetching the top referrers.") you 
