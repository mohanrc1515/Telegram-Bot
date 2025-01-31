import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db
from config import Config, Txt


# 📌 Command: /start
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)  

    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('Uᴩᴅᴀᴛᴇꜱ', url='https://t.me/AutoRenameUpdates'),
        InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Elites_Assistance')
    ]])

    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=button)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=button, disable_web_page_preview=True)




@Client.on_message(filters.private & filters.command("start"))
async def check_command(client, message):
    try:
        # Your check command logic
        await message.reply("Check command executed successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")
