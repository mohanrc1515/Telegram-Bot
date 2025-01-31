import os
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.database import db
from config import Config, Txt


# 📌 Command: /start
@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await db.add_user(client, message)  

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('Hᴇʟᴘ', callback_data="help_menu"),
         InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Elites_Assistance')]
    ])

    if Config.START_PIC:
        await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(user.mention), reply_markup=buttons)       
    else:
        await message.reply_text(text=Txt.START_TXT.format(user.mention), reply_markup=buttons, disable_web_page_preview=True)


# 📌 Callback Handler for Help Menu
@Client.on_callback_query(filters.regex("help_menu"))
async def help_menu(client, query: CallbackQuery):
    help_text = (
        "🤖 **Available Commands:**\n"
        "• /set_profile - Set up your profile\n"
        "• /profile - View your profile\n"
        "• /user <user_id/username> - View someone else's profile\n"
        "• /editbio - Edit your bio\n"
        "• /del_profile - Delete your profile\n"
        "• /cancel - Cancel profile setup\n"
        "• /nofap - Check your NoFap status\n"
        "• /fapped - Restart your NoFap timer\n"
    )

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('🔙 Bᴀᴄᴋ', callback_data="back_to_start")]
    ])

    await query.message.edit_text(text=help_text, reply_markup=buttons, disable_web_page_preview=True)


# 📌 Callback Handler for Back Button
@Client.on_callback_query(filters.regex("back_to_start"))
async def back_to_start(client, query: CallbackQuery):
    user = query.from_user

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton('Hᴇʟᴘ', callback_data="help_menu"),
         InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Elites_Assistance')]
    ])

    if Config.START_PIC:
        await query.message.edit_caption(caption=Txt.START_TXT.format(user.mention), reply_markup=buttons)
    else:
        await query.message.edit_text(text=Txt.START_TXT.format(user.mention), reply_markup=buttons, disable_web_page_preview=True)
