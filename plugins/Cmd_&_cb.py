from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from helper.database import db
from config import Config, Txt

@Client.on_message(filters.private & filters.command(["admin_cmd"]))
async def admin_commands(client, message):
    commands = [
        "/auth - Authorize a user",
        "/unauth - Unauthorize a user",
        "/auth_users - List all authorized users",
        "/giveaway - Start a giveaway",
        "/winner - Select a winner for the giveaway",
        "/coupan - Generate free auth coupons",
        "/stats - Show bot usage statistics",
        "/broadcast - Send a message to all users"
        "/restart - Restart the bot",
    ]

    # Send the list of commands with additional buttons for your channel and group
    await message.reply_text(
        "**<u>Admin Commands**</u>\n\n" + "\n".join(commands),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Channel", url="https://t.me/Elites_Bots"),
             InlineKeyboardButton("Group", url="https://t.me/Elites_Assistance")],
        ])
    )    

@Client.on_callback_query(filters.regex('start'))
async def start_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.START_TXT.format(query.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Hᴇʟᴘ & Cᴏᴍᴍᴀɴᴅs", callback_data='commands')
        ],[
            InlineKeyboardButton('Uᴩᴅᴀᴛᴇꜱ', url='https://t.me/Elites_Bots'),
            InlineKeyboardButton('Sᴜᴩᴩᴏʀᴛ', url='https://t.me/Elites_Assistance')
        ],[
            InlineKeyboardButton('Aʙᴏᴜᴛ', callback_data='about'),
            InlineKeyboardButton('Pʀᴇᴍɪᴜᴍ', callback_data='premium')
        ]])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('commands'))
async def commands_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.COMMANDS_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Cᴏɴғɪɢᴜʀᴇ Bᴏᴛ Sᴇᴛᴛɪɴɢꜱ", callback_data='settings')
        ],[
            InlineKeyboardButton('Aᴜᴛᴏʀᴇɴᴀᴍᴇ', callback_data='file_names'),
            InlineKeyboardButton('Sᴇǫᴜᴇɴᴄɪɴɢ', callback_data='sequence')
        ],[
            InlineKeyboardButton('Fᴇᴀᴛᴜʀᴇꜱ & Gᴜɪᴅᴀɴᴄᴇ', callback_data='features')
        ],[
            InlineKeyboardButton('Cʟᴏꜱᴇ', callback_data='close'),
            InlineKeyboardButton('Hᴏᴍᴇ', callback_data='start')
        ]])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('premium'))
async def premium_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.PREMIUM_TXT.format(query.from_user.mention),
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton('Uᴘɢʀᴀᴅᴇ Nᴏᴡ', url='https://t.me/Shadow_Kunn'),
                InlineKeyboardButton('Fʀᴇᴇ Bᴏᴛ', url='https://t.me/Auto_Renamer_X_Bot')
            ],
            [
                InlineKeyboardButton("Cʟᴏꜱᴇ", callback_data="close"),
                InlineKeyboardButton("Hᴏᴍᴇ", callback_data="start")
            ]
        ])
    )
    await query.answer()


@Client.on_callback_query(filters.regex('sequence'))
async def sequence_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.SEQUENCE_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url='https://t.me/Elites_Assistance'),
             InlineKeyboardButton("Bᴀᴄᴋ", callback_data="commands")]
        ])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('caption'))
async def caption_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.CAPTION_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="settings")]
        ])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('file_names'))
async def file_names_callback(client, query: CallbackQuery):
    user_id = query.from_user.id
    await query.message.edit_text(
        text=Txt.FILE_NAME_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Bᴀᴄᴋ", callback_data="commands")]
        ])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('thumbnail'))
async def thumbnail_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.THUMB_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="settings")]
        ])
    )
    await query.answer()

@Client.on_callback_query(filters.regex('duhelp'))
async def duhelp(client, query: CallbackQuery):
    await query.message.edit_text(
        text=Txt.DUMP_TXT,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Back", callback_data="commands"), InlineKeyboardButton("Sᴜᴩᴩᴏʀᴛ", url='https://t.me/Elites_Assistance')]
        ])            
    )
    await query.answer()

@Client.on_callback_query(filters.regex('close'))
async def close_callback(client, query: CallbackQuery):
    try:
        await query.message.delete()
        if query.message.reply_to_message:
            await query.message.reply_to_message.delete()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await query.message.continue_propagation()
    await query.answer()
    
@Client.on_message(filters.private & filters.command(["dumptext"]))
async def customdumptext_cmd(client, message):
    # Send the image first
    await message.reply_photo(
        photo="https://envs.sh/ltZ.jpg",
        caption=Txt.DUMPMESSAGE_TXT,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Cᴏɴғɪɢᴜʀᴇ Dᴜᴍᴘ Sᴇᴛᴛɪɴɢꜱ", callback_data='dump_settings')
            ],
            [
                InlineKeyboardButton('Cʟᴏꜱᴇ', callback_data='close')
            ]
        ])
    )
