import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from config import Config

# Database setup
client = MongoClient(Config.DB_URL)
db = client["giveaway_bot"]
participants_collection = db["giveaway"]
settings_collection = db["settings"]

# Constants
ADMIN_ID = 6006418463
LOG_CHANNEL = Config.LOG_CHANNEL

# Helper functions
def get_giveaway_status():
    settings = settings_collection.find_one({"_id": "giveaway_status"})
    return settings.get("enabled", False) if settings else False

def set_giveaway_status(enabled):
    settings_collection.update_one(
        {"_id": "giveaway_status"},
        {"$set": {"enabled": enabled}},
        upsert=True
    )

def clear_participants():
    participants_collection.delete_many({})

# Update the control panel buttons
def generate_control_panel_buttons(giveaway_status):
    buttons = [
        [InlineKeyboardButton(f"{'Disable' if giveaway_status else 'Enable'} Giveaway", callback_data="toggle_giveaway")],
        [InlineKeyboardButton("🗑 Clear Data", callback_data="clear_data")]
    ]
    return InlineKeyboardMarkup(buttons)

# Commands
@Client.on_message(filters.command("giveaway"))
async def giveaway_command(client, message):
    if message.from_user.id == ADMIN_ID:
        giveaway_status = get_giveaway_status()
        total_participants = participants_collection.count_documents({})

        status_text = "🟢 Giveaway is currently enabled." if giveaway_status else "🔴 Giveaway is currently disabled."
        buttons = generate_control_panel_buttons(giveaway_status)

        await message.reply(
            f"**🛠️ <u>GIVEAWAY CONTROL PANEL</u> 🛠️**\n\n"
            f"{status_text}\n\n"
            f"**👥 Total Participants:** {total_participants}",
            reply_markup=buttons
        )
    else:
        # Message for non-admin users trying to use the command
        await message.reply("Only my master can use this command.\n\nBut as a user you can /enter in thr giveaway if its ongoing...")

@Client.on_callback_query(filters.regex("toggle_giveaway"))
async def toggle_giveaway(client, callback_query):
    if callback_query.from_user.id == ADMIN_ID:
        try:
            current_status = get_giveaway_status()
            new_status = not current_status
            set_giveaway_status(new_status)
            await callback_query.answer(f"Giveaway {'enabled' if new_status else 'disabled'}.", show_alert=True)

            # Update buttons and status text
            status_text = "🟢 Giveaway is currently enabled." if new_status else "🔴 Giveaway is currently disabled."
            buttons = generate_control_panel_buttons(new_status)
            await callback_query.message.edit_text(
                f"**🛠️ <u>GIVEAWAY CONTROL PANEL</u> 🛠️**\n\n"
                f"{status_text}\n\n"
                f"**👥 Total Participants:** {participants_collection.count_documents({})}",
                reply_markup=buttons
            )
        except Exception as e:
            await callback_query.answer("An error occurred while updating the giveaway status.", show_alert=True)
            print(f"Error toggling giveaway: {e}")
    else:
        await callback_query.answer("Nice Try Diddy.", show_alert=True)

@Client.on_callback_query(filters.regex("clear_data"))
async def clear_data(client, callback_query):
    if callback_query.from_user.id == ADMIN_ID:
        clear_participants()
        await callback_query.answer("All participants cleared.", show_alert=True)
        giveaway_status = get_giveaway_status()
        buttons = generate_control_panel_buttons(giveaway_status)
        await callback_query.message.edit_text(
            f"**🛠️ <u>GIVEAWAY CONTROL PANEL</u> 🛠️**\n\n"
            f"🟢 Giveaway is currently enabled." if giveaway_status else "🔴 Giveaway is currently disabled.\n\n"
            f"**👥 Total Participants:** 0",
            reply_markup=buttons
        )
    else:
        await callback_query.answer("Nice Try Diddy.", show_alert=True)
        
@Client.on_message(filters.command("enter") & filters.group)
async def enter_giveaway_group(client, message):
    user_id = message.from_user.id
    await message.reply(
        "ᴅᴇᴀʀ ᴜsᴇʀ, ᴋɪɴᴅʟʏ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ɪɴ ᴍʏ ᴘʀɪᴠᴀᴛᴇ ᴄʜᴀᴛ....",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🤖 Oᴘᴇɴ ɪɴ Pʀɪᴠᴀᴛᴇ", url="https://t.me/Auto_Rename_X_Bot")]
        ])
    )

@Client.on_message(filters.command("enter") & filters.private)
async def enter_giveaway(client, message):
    giveaway_status = get_giveaway_status()
    user_id = message.from_user.id

    if giveaway_status:
        if not participants_collection.find_one({"user_id": user_id}):
            participants_collection.insert_one({"user_id": user_id})
            await message.reply("🎉 You have successfully entered the giveaway!")

            # Send log message to LOG_CHANNEL
            await client.send_message(
                LOG_CHANNEL, 
                f"🎉 User [{message.from_user.first_name}](tg://user?id={user_id}) has entered the giveaway."
            )
        else:
            await message.reply("You are already in the giveaway!")
    else:
        await message.reply("There is currently no ongoing giveaway.")

@Client.on_message(filters.command("winner"))
async def select_winner(client, message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("Only my master can use this command.")
        return

    giveaway_status = get_giveaway_status()

    if not giveaway_status:
        await message.reply("The giveaway is currently disabled.")
        return

    participants = list(participants_collection.find({}))
    if participants:
        winner = random.choice(participants)
        winner_user_id = winner['user_id']

        # Fetch the winner's details
        winner_user = await client.get_users(winner_user_id)
        winner_first_name = winner_user.first_name
        winner_username = winner_user.username if winner_user.username else "None"

        # Ensure the winner is not repeated if already chosen
        participants_collection.delete_one({"user_id": winner_user_id})

        # Reply with the formatted winner message
        await message.reply(
            f"🏆 **Winner Announcement** 🏆\n\n"
            f"**👤 Name:** {winner_first_name}\n"
            f"**🔗 Username:** @{winner_username}\n"
            f"**🆔 ID:** <code>{winner_user_id}</code>\n\n"
            f"Congrats, You've won 🎉"
        )
    else:
        await message.reply("No participants found in the giveaway.")
        
