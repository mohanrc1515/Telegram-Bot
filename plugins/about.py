import time
import os
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters
from helper.database import db
from helper.utils import humanbytes

@Client.on_message(filters.command(["about"]))
async def aboutcm(client, message):
    total_files_renamed = await db.get_total_files_renamed()
    total_renamed_size = await db.get_total_renamed_size()

    await message.reply_photo(
        photo="https://envs.sh/C5Q.jpg",
        caption=(
            f"<b><u>AUTO RENAME BOT</b></u>\n\n"
            f"👑 Owner: {message.from_user.mention}\n"
            f"🧑🏻‍💻 Developer: [Sʜᴀᴅᴏᴡ 様](https://t.me/ElitesCrewBot)\n"
            f"🗂️ Database: [Mongo Db](https://www.mongodb.com/)\n"
            f"📡 Server: [Heroku](https://www.heroku.com/)\n"
            f"🗣️ Language: [Python](https://www.python.org/)\n"
            f"📢 Updates Channel: [Elites Botz](https://t.me/Elites_Bots)\n"
            f"👥 Support Group: [Elites Assistance](https://t.me/Elites_Assistance)\n"
            f"🤖 GitHub: [Click Here](https://github.com/Orewa-Kaizen)\n\n"
            f"📂 Total Files Renamed: {total_files_renamed}\n"
            f"🗃 Total Renamed Size: {humanbytes(int(total_renamed_size))}"
        ),
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("✗ Close ✗", callback_data="close")]
            ]
        )
    )

@Client.on_callback_query(filters.regex('about'))
async def about_callback(client, callback_query):
    total_files_renamed = await db.get_total_files_renamed()
    total_renamed_size = await db.get_total_renamed_size()
    
    text = (
        f"<b><u>AUTO RENAME BOT</b></u>\n\n"
        f"👑 Owner: {callback_query.from_user.mention}\n"
        f"🧑🏻‍💻 Developer: [Sʜᴀᴅᴏᴡ 様](https://t.me/ElitesCrewBot)\n"
        f"🗂️ Database: [Mongo Db](https://www.mongodb.com/)\n"
        f"📡 Server: [Heroku](https://www.heroku.com/)\n"
        f"🗣️ Language: [Python](https://www.python.org/)\n"
        f"📢 Updates Channel: [Elites Botz](https://t.me/Elites_Bots)\n"
        f"👥 Support Group: [Elites Assistance](https://t.me/Elites_Assistance)\n"
        f"🤖 GitHub: [Click Here](https://github.com/Orewa-Kaizen)\n\n"
        f"📂 Total Files Renamed: {total_files_renamed}\n"
        f"🗃 Total Renamed Size: {humanbytes(int(total_renamed_size))}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("✗ Bᴀᴄᴋ ✗", callback_data="start")],
        ]
    )

    await callback_query.message.edit_text(text=text, reply_markup=keyboard)
    await callback_query.answer()

@Client.on_callback_query(filters.regex('close'))
async def close_callback(client, callback_query):
    # Delete the post triggered by the command
    try:
        await callback_query.message.delete()  # Delete the post created by the bot
        if callback_query.message.reply_to_message:  # Check if there's a reply to message (original command)
            await callback_query.message.reply_to_message.delete()  # Delete the message that triggered the post
    except Exception as e:
        await callback_query.answer(text=f"Error: {e}", show_alert=True)
    else:
        await callback_query.answer(text="Successfully Closed", show_alert=True)
        


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
        
