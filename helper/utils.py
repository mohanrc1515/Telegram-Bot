import math, time, re, os, pytz
import aiohttp
from datetime import datetime, timedelta
from pytz import timezone
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from pyrogram.errors import FloodWait


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
            
