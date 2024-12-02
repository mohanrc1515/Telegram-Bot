import time
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from pymongo import MongoClient
from config import Config

# Database setup
client = MongoClient(Config.DB_URL)
db = client["star_bot"]
stars_collection = db["stars"]

@Client.on_message(filters.private & filters.command(["about"]))
async def aboutcm(client, message):
    # Retrieve star count
    star_count = stars_collection.count_documents({})

    await message.reply_photo(
        photo="https://envs.sh/w_f.jpg",
        caption=(
            f"<b><u>AUTO RENAME BOT</b></u>\n\n"
            f"👑 Owner: {message.from_user.mention}\n"
            f"🧑🏻‍💻 Developer: [Zᴇɴɪᴛꜱᴜ 様](https://t.me/ElitesCrewBot)\n"
            f"🗂️ Database: [Mongo Db](https://www.mongodb.com/)\n"
            f"📡 Server: [Heroku](https://www.heroku.com/)\n"
            f"🗣️ Language: [Python](https://www.python.org/)\n"
            f"📢 Updates Channel: [Elites Botz](https://t.me/Elites_Bots)\n"
            f"👥 Support Group: [Elites Assistance](https://t.me/Elites_Assistance)\n"
            f"🤖 GitHub: [Click Here](https://github.com/ElitesBotz)\n\n"
            f"⭐ Star Count: {star_count}\n"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Oᴡɴᴇʀ", url="https://t.me/ElitesCrewBot"),
                 InlineKeyboardButton("⭐ Star", callback_data="vote")]
            ]
        )
    )

@Client.on_callback_query(filters.regex('about'))
async def about_callback(client, callback_query):
    star_count = stars_collection.count_documents({})
    text = (
        f"<b><u>AUTO RENAME BOT</b></u>\n\n"
        f"👑 Owner: {callback_query.from_user.mention}\n"
        f"🧑🏻‍💻 Developer: [Zᴇɴɪᴛꜱᴜ 様](https://t.me/ElitesCrewBot)\n"
        f"🗂️ Database: [Mongo Db](https://www.mongodb.com/)\n"
        f"📡 Server: [Heroku](https://www.heroku.com/)\n"
        f"🗣️ Language: [Python](https://www.python.org/)\n"
        f"📢 Updates Channel: [Elites Botz](https://t.me/Elites_Bots)\n"
        f"👥 Support Group: [Elites Assistance](https://t.me/Elites_Assistance)\n"
        f"🤖 GitHub: [Click Here](https://github.com/ElitesBotz)\n\n"
        f"⭐ Star Count: {star_count}\n"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="start"),
             InlineKeyboardButton("⭐ Sᴛᴀʀ", callback_data="vote")],
        ]
    )

    await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex('vote'))
async def vote_callback(client, callback_query):
    user_id = callback_query.from_user.id
    user = callback_query.from_user

    try:
        # Check if the user has already starred
        user_starred = stars_collection.find_one({"user_id": user_id})
        if user_starred:
            await callback_query.answer(text="You have already given the bot a star.", show_alert=True)
        else:
            # Add user to the star collection
            stars_collection.insert_one({"user_id": user_id})
            star_count = stars_collection.count_documents({})

            # Log user information to the log channel
            log_message = (
                f"🌟 New Star 🌟 #premium_autorename\n\n"
                f"👤 User: {user.mention}\n"
                f"🆔 User ID: {user_id}\n"
                f"✉️ Username: {user.username}\n"
                f"📊 Total Stars: {star_count}"
            )
            
            try:
                await client.send_message(Config.LOG_CHANNEL, log_message)
            except Exception as e:
                print(f"Error sending log message: {e}")

            await callback_query.answer(text=f"You have successfully starred the bot. Total stars: {star_count}", show_alert=True)
    except Exception as e:
        await callback_query.answer(text=f"An error occurred: {e}", show_alert=True)
        
