from config import Config, Txt
from helper.database import db
import psutil, time, os, sys
from helper.utils import get_size
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import logging, datetime, asyncio

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ADMIN_USER_ID = Config.ADMIN

# Flag to indicate if the bot is restarting
is_restarting = False

@Client.on_message(filters.private & filters.command("restart") & filters.user(ADMIN_USER_ID))
async def restart_bot(b: Client, m: Message):
    global is_restarting
    if not is_restarting:
        is_restarting = True
        msg = await m.reply_text("**🔄 Restarting.....**")
        b.stop()
        await asyncio.sleep(4)
        await msg.edit_text("**✅ Successfully restarted**")
        os.execl(sys.executable, sys.executable, *sys.argv)

@Client.on_message(filters.command(["stats", "status"]) & filters.user(Config.ADMIN))
async def get_stats(bot: Client, message: Message):
    try:
        # Calculate database stats
        total_users = await db.total_users_count()
        size = await db.get_db_size()
        free = 536870912 - size  # Assuming a 512MB limit
        size = get_size(size)
        free = get_size(free)
        
        # Uptime and ping calculation
        uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - bot.uptime))
        start_t = time.time()
        st = await message.reply_text('**🔍 Fetching the details...**')
        end_t = time.time()
        time_taken_s = (end_t - start_t) * 1000

        # System RAM and memory details
        ram_info = psutil.virtual_memory()
        total_ram = get_size(ram_info.total)
        used_ram = get_size(ram_info.used)
        free_ram = get_size(ram_info.available)
        ram_percentage = ram_info.percent

        # Renaming RAM (if relevant)
        renaming_process = psutil.Process(os.getpid())
        renaming_ram = get_size(renaming_process.memory_info().rss)  # Resident Set Size (RAM used by the bot)

        # Prepare stats message
        stats_message = (
            f"**-- Bot Status --**\n\n"
            f"**⌚️ Uptime:** __{uptime}__\n"
            f"**🐌 Ping:** `{time_taken_s:.3f} ms`\n"
            f"**👥 Total Users:** `{total_users}`\n"
            f"**📦 Storage Used:** `{size}`\n"
            f"**📂 Storage Free:** `{free}`\n\n"
            f"**-- System RAM Stats --**\n\n"
            f"**💾 Total RAM:** `{total_ram}`\n"
            f"**📊 Used RAM:** `{used_ram}` ({ram_percentage}%)\n"
            f"**📂 Free RAM:** `{free_ram}`\n"
            f"**⚙️ Renaming RAM Usage:** `{renaming_ram}`\n"
        )

        # Send stats with image
        await bot.send_photo(
            chat_id=message.chat.id,
            photo="https://envs.sh/w_f.jpg",  # Ensure this is a valid image URL
            caption=stats_message
        )
        await st.delete()

    except Exception as e:
        logger.error(f"Error in /stats: {e}")
        await message.reply_text(f"**❌ Failed to fetch stats:** `{e}`")
 
@Client.on_message(filters.command("broadcast") & filters.user(Config.ADMIN) & filters.reply)
async def broadcast_handler(bot: Client, m: Message):
    await bot.send_message(Config.LOG_CHANNEL, f"{m.from_user.mention} or {m.from_user.id} Started The Broadcast......")
    all_users = await db.get_all_users()
    broadcast_msg = m.reply_to_message
    sts_msg = await m.reply_text("Broadcast Started..!") 
    done = 0
    failed = 0
    success = 0
    start_time = time.time()
    total_users = await db.total_users_count()

    async for user in all_users:
        sts = await send_msg(user['_id'], broadcast_msg)
        if sts == 200:
            success += 1
        else:
            failed += 1
        if sts == 400:
            await db.delete_user(user['_id'])
        done += 1
        if done % 20 == 0:
            await sts_msg.edit(
                f"Broadcast In Progress: \n\n"
                f"Total Users {total_users} \n"
                f"Completed : {done} / {total_users}\n"
                f"Success : {success}\n"
                f"Failed : {failed}"
            )

    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    broadcast_summary = (
        f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \n"
        f"Completed in `{completed_in}`.\n\n"
        f"Total Users {total_users}\n"
        f"Completed: {done} / {total_users}\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )
    
    # Add buttons for Edit/Delete
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Edit Message", callback_data=f"edit_broadcast:{broadcast_msg.id}")],
            [InlineKeyboardButton("Delete Message", callback_data=f"delete_broadcast:{broadcast_msg.id}")]
        ]
    )
    await sts_msg.edit(broadcast_summary, reply_markup=buttons)

async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        logger.info(f"Flood wait for {e.value} seconds while sending message to {user_id}")
        await asyncio.sleep(e.value)
        return await send_msg(user_id, message)
    except InputUserDeactivated:
        logger.info(f"{user_id} : Deactivated")
        return 400
    except UserIsBlocked:
        logger.info(f"{user_id} : Blocked The Bot")
        return 400
    except PeerIdInvalid:
        logger.info(f"{user_id} : User ID Invalid")
        return 400
    except Exception as e:
        logger.error(f"{user_id} : {e}")
        return 500

@Client.on_callback_query(filters.regex(r"^edit_broadcast:(\d+)$"))
async def edit_broadcast(bot: Client, callback_query: CallbackQuery):
    message_id = int(callback_query.data.split(":")[1])
    await callback_query.message.reply(
        f"Please send the updated message for broadcast ID: {message_id}",
        quote=True
    )

@Client.on_callback_query(filters.regex(r"^delete_broadcast:(\d+)$"))
async def delete_broadcast(bot: Client, callback_query: CallbackQuery):
    message_id = int(callback_query.data.split(":")[1])
    try:
        await bot.delete_messages(chat_id=callback_query.message.chat.id, message_ids=message_id)
        await callback_query.answer("Broadcasted message deleted successfully.", show_alert=True)
    except Exception as e:
        await callback_query.answer(f"Error: {e}", show_alert=True)
