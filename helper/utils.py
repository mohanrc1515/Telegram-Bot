import math, time, re, os, pytz
import aiohttp
from datetime import datetime, timedelta
from helper.database import db
from pytz import timezone
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from pyrogram.errors import FloodWait

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    percentage = current * 100 / total
    speed = current / diff if diff > 0 else 0
    elapsed_time = round(diff) * 1000
    time_to_completion = round((total - current) / speed) * 1000 if speed > 0 else 0
    estimated_total_time = elapsed_time + time_to_completion

    elapsed_time = TimeFormatter(milliseconds=elapsed_time)
    estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

    progress = "{0}{1}".format(
        ''.join(["■" for _ in range(math.floor(percentage / 5))]),
        ''.join(["□" for _ in range(20 - math.floor(percentage / 5))])
    )
    tmp = progress + Txt.PROGRESS_BAR.format(
        round(percentage, 2),
        humanbytes(current),
        humanbytes(total),
        humanbytes(speed),
        estimated_total_time if estimated_total_time != '' else "0 s"
    )

    # Keep track of the last edit time
    if not hasattr(progress_for_pyrogram, "last_edit"):
        progress_for_pyrogram.last_edit = 0

    # Only update every 5% or at completion
    if percentage == 100 or time.time() - progress_for_pyrogram.last_edit >= 5:
        try:
            await message.edit(text=f"{ud_type}\n\n{tmp}")
            progress_for_pyrogram.last_edit = time.time()
        except FloodWait as e:
            print(f"Flood wait for {e.value} seconds")
            await asyncio.sleep(e.value)
            await message.edit(text=f"{ud_type}\n\n{tmp}")
        except Exception as e:
            print(f"Error editing message: {e}")



def humanbytes(size):
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    Dic_powerN = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size >= power and n < len(Dic_powerN) - 1:
        size /= power
        n += 1
    return f"{round(size, 2)} {Dic_powerN[n]}B"

def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])
     

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    components = []
    if days: components.append(f"{days}ᴅ")
    if hours: components.append(f"{hours}ʜ")
    if minutes: components.append(f"{minutes}ᴍ")
    if seconds: components.append(f"{seconds}ꜱ")
    return ', '.join(components)


def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%d:%02d:%02d" % (hour, minutes, seconds)

def user_mention(user):
    return f"[{user.first_name}](tg://user?id={user.id})"

def format_timestamp(dt=None):
    india_tz = pytz.timezone('Asia/Kolkata')
    if dt:
        return dt.astimezone(india_tz).strftime('%H:%M:%S %d-%m-%Y')
    return datetime.now(india_tz).strftime('%H:%M:%S %d-%m-%Y')

def parse_duration(duration_str):
    units = {
        "sec": "seconds",
        "min": "minutes",
        "hour": "hours",
        "day": "days",
        "week": "weeks",
        "month": "months",
        "year": "years"
    }

    try:
        value, unit = duration_str.split()
        value = int(value)

        if unit not in units:
            return None

        if units[unit] == "months":
            return timedelta(days=value * 30)
        elif units[unit] == "years":
            return timedelta(days=value * 365)
        else:
            return timedelta(**{units[unit]: value})
    except (ValueError, KeyError):
        return None

async def send_log(bot, user):
    if Config.NEW_USER_LOG is not None:
        curr = datetime.now(timezone("Asia/Kolkata"))
        date = curr.strftime('%d %B, %Y')
        time = curr.strftime('%I:%M:%S %p')
        try:
            await bot.send_message(
                Config.NEW_USER_LOG,
                f"**--Nᴇᴡ Uꜱᴇʀ Sᴛᴀʀᴛᴇᴅ Tʜᴇ Bᴏᴛ--**\n\nUꜱᴇʀ: {user_mention(user)}\nIᴅ: `{user.id}`\nUɴ: @{user.username}\n\nDᴀᴛᴇ: {date}\nTɪᴍᴇ: {time}\n\nBy: {bot.mention}\n\n#Premium_AR"
            )
        except Exception as e:
            print(f"Error sending log message: {e}")
            

def add_prefix_suffix(input_string, prefix='', suffix=''):
    pattern = r'(?P<filename>.*?)(\.\w+)?$'
    match = re.search(pattern, input_string)
    if match:
        filename = match.group('filename')
        extension = match.group(2) or ''
        if prefix == None:
            if suffix == None:
                return f"{filename}{extension}"
            return f"{filename} {suffix}{extension}"
        elif suffix == None:
            if prefix == None:
               return f"{filename}{extension}"
            return f"{prefix}{filename}{extension}"
        else:
            return f"{prefix}{filename} {suffix}{extension}"


    else:
        return input_string

async def update_statistics(user_id, file_size):
    # Update user-specific file count
    current_user_count = await db.get_file_count(user_id)
    new_user_count = current_user_count + 1
    await db.update_file_count(user_id, new_user_count)

    # Update global file count and size
    current_global_count = await db.get_total_files_renamed()
    current_global_size = await db.get_total_renamed_size()

    new_global_count = current_global_count + 1
    new_global_size = current_global_size + file_size

    await db.update_total_files_renamed(new_global_count)
    await db.update_total_renamed_size(new_global_size)

    # Log the updated stats
    print(f"User {user_id}: Files Processed = {new_user_count}")
    print(f"Global Stats: Total Files = {new_global_count}, Total Size = {humanbytes(new_global_size)}")
    
