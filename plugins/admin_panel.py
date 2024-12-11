from config import Config, Txt
from helper.database import db
import psutil
from helper.utils import get_size
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import os, sys, time, asyncio, logging, datetime

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
    # Calculate stats
    total_users = await db.total_users_count()
    size = await db.get_db_size()
    free = 536870912 - size
    size = get_size(size)
    free = get_size(free)
    uptime = time.strftime("%Hh%Mm%Ss", time.gmtime(time.time() - bot.uptime))
    start_t = time.time()
   
    
    # Calculate time taken to get stats
    st = await message.reply_text('**🔍 Fetching the details...**')
    end_t = time.time()
    time_taken_s = (end_t - start_t) * 1000

    # Prepare stats message
    stats_message = (
        f"**-- Bot Status --**\n\n"
        f"**⌚️ Uptime:** __{uptime}__\n"
        f"**🐌 Ping:** `{time_taken_s:.3f} ms`\n"
        f"**👥 Total Users:** `{total_users}`\n"
        f"**📦 Storage Used:** `{size}`\n"
        f"**📂 Storage Free:** `{free}`"
    )
    
    # Send stats with image
    await bot.send_photo(
        chat_id=message.chat.id,
        photo="https://envs.sh/w_f.jpg",
        caption=stats_message
    )
    await st.delete()
    
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
        if not done % 20:
           await sts_msg.edit(f"Broadcast In Progress: \n\nTotal Users {total_users} \nCompleted : {done} / {total_users}\nSuccess : {success}\nFailed : {failed}")
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts_msg.edit(f"Bʀᴏᴀᴅᴄᴀꜱᴛ Cᴏᴍᴩʟᴇᴛᴇᴅ: \nCᴏᴍᴩʟᴇᴛᴇᴅ Iɴ `{completed_in}`.\n\nTotal Users {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nFailed: {failed}")
           
async def send_msg(user_id, message):
    try:
        await message.copy(chat_id=int(user_id))
        return 200
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return send_msg(user_id, message)
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
        
