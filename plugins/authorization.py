from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from helper.database import db
from datetime import datetime, timedelta
from config import Config, Txt
from helper.utils import *
import pytz
import random
import string

ADMIN = 6006418463

def generate_coupons(prefix, num_coupons, length=8):
    coupons = []
    for _ in range(num_coupons):
        code = prefix + ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        coupons.append(code)
    return coupons

@Client.on_message(filters.command("auth") & (filters.private | filters.group))
async def auth_user(client: Client, message: Message):
    if message.from_user.id != ADMIN:
        await message.reply_text(f"{user_mention(message.from_user)}, you cannot use this command; it's only for my master.")
        return
    
    try:
        user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
        duration = " ".join(message.command[2:])
        duration_td = parse_duration(duration)
        if not duration_td:
            await message.reply_text("Master! Please provide a valid duration (e.g., '1 day', '2 weeks').")
            return
    except (IndexError, ValueError):
        await message.reply_text("Master! Please reply to a user or provide a valid user ID and duration to authorize.")
        return

    expiry_time = datetime.now() + duration_td

    if await db.is_user_authorized(user_id):
        await message.reply_text(f"User with ID {user_id} is already authorized.")
    else:
        await db.authorize_user(user_id, expiry_time)
        timestamp = format_timestamp()
        expiry_str = format_timestamp(expiry_time)

        user_details = await client.get_users(user_id)
        auth_message = (f"✅ You have been authorized!\n\n"
                        f"**User:** {user_mention(user_details)}\n"
                        f"**Authorization Duration:** `{duration}`\n"
                        f"**Authorization Start:** `{timestamp}`\n"
                        f"**Authorization Expiry:** `{expiry_str}`")
        await client.send_message(user_id, auth_message)
        
        await message.reply_text(f"User with ID {user_id} has been authorized successfully for {duration}.")

        # Send log message to the log channel
        log_message = (f"User Authorized ✅...\n\n"
                       f"**User:** {user_mention(user_details)} `{user_details.id}`\n"
                       f"**Username:** @{user_details.username}\n"
                       f"**Authorized by:** {user_mention(message.from_user)} `{message.from_user.id}`\n"
                       f"**Chat:** {'Group' if message.chat.type in ['group', 'supergroup'] else 'Private'}\n"
                       f"**Chat ID:** `{message.chat.id}`\n\n"
                       f"**Authorization Duration:** `{duration}`\n"
                       f"**Authorization Start:** `{timestamp}`\n"
                       f"**Authorization Expiry:** `{expiry_str}`")
        await client.send_message(Config.LOG_CHANNEL, log_message)

@Client.on_message(filters.command("unauth") & (filters.private | filters.group))
async def unauth_user(client: Client, message: Message):
    if message.from_user.id != ADMIN:
        await message.reply_text(f"{user_mention(message.from_user)}, you cannot use this command; it's only for my master.")
        return
    
    try:
        user_id = message.reply_to_message.from_user.id if message.reply_to_message else int(message.command[1])
    except (IndexError, ValueError):
        await message.reply_text("Master! Please reply to a user or provide a valid user ID to unauthorize.")
        return

    if await db.is_user_authorized(user_id):
        await db.unauthorize_user(user_id)
        timestamp = format_timestamp()

        user_details = await client.get_users(user_id)
        unauth_message = (f"⚠️ You have been unauthorized.\n\n"
                          f"**User:** {user_mention(user_details)}\n\n"
                          f"**Unauthorized Time:** `{timestamp}`")
        await client.send_message(user_id, unauth_message)

        await message.reply_text(f"User with ID {user_id} has been unauthorized.")

        # Send log message to the log channel
        log_message = (f"User Unauthorized ⚠️...\n\n"
                       f"**User:** {user_mention(user_details)} `{user_details.id}`\n"              
                       f"**Unauthorized by:** {user_mention(message.from_user)} `{message.from_user.id}`\n"
                       f"**Chat:** {'Group' if message.chat.type in ['group', 'supergroup'] else 'Private'}\n"
                       f"**Chat ID:** `{message.chat.id}`\n\n"
                       f"**Unauthorized Time:** `{timestamp}`")
        await client.send_message(Config.LOG_CHANNEL, log_message)
    else:
        await message.reply_text(f"{user_mention(message.from_user)}, user with ID {user_id} is not authorized.")

@Client.on_message(filters.command("auth_users") & (filters.private | filters.group))
async def list_auth_users(client: Client, message: Message):
    if message.from_user.id != ADMIN:
        await message.reply_text(f"{user_mention(message.from_user)}, you cannot use this command; it's only for my master.")
        return

    # Fetch all authorized users from the database
    authorized_users_cursor = await db.get_all_authorized_users()
    authorized_users = await authorized_users_cursor.to_list(length=None)
    
    if not authorized_users:
        await message.reply_text("No users are currently authorized.")
        return

    user_list = ""
    for user in authorized_users:
        try:
            user_details = await client.get_users(user["_id"])
            duration_td = user["expiry_time"] - datetime.utcnow()
            user_list += (f"{user_mention(user_details)} `{user['_id']}`\n"
                          f"**Authorization Duration:** `{str(duration_td)}`\n"
                          f"**Expiry Date:** `{format_timestamp(user['expiry_time'])}`\n\n")
        except Exception:
            user_list += f"User with ID `{user['_id']}` not found.\n"

    await message.reply_text(f"**Authorized Users:**\n\n{user_list}")


@Client.on_message(filters.command("myplan") & filters.private)
async def myplan(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check if the user is authorized
    if await db.is_user_authorized(user_id):
        expiry_time = await db.get_authorization_expiry(user_id)
        duration_td = expiry_time - datetime.utcnow()
        start_time = expiry_time - duration_td

        # Prepare the plan information message
        myplan_message = (
            f"**💳 <u>Authorization Details</u> 💳**\n\n"
            f"👤 **User:** {user_mention(message.from_user)}\n"
            f"🕒 **Auth Duration:** `{str(duration_td)}`\n"
            f"📅 **Auth Start:** `{format_timestamp(start_time)}`\n"
            f"⏳ **Auth Expiry:** `{format_timestamp(expiry_time)}`\n\n"
            f"✨ __Enjoy your premium features and benefits!__"
        )

        # Close button
        close_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("✗ Close ✗", callback_data="close")]
        ])

        # Send default image with premium details
        await client.send_photo(
            chat_id=user_id,
            photo="https://envs.sh/7S2.jpg",
            caption=myplan_message,
            reply_markup=close_button
        )
    
    # If user is not authorized
    else:
        # Button with a callback to 'premium'
        buy_premium_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("💎 Buy Premium", callback_data="premium")]
        ])
        
        # Prepare the unauthorized message
        unauthorized_message = (
            f"**Hello {user_mention(message.from_user)} !!!**\n\n"
            f"⚠️ __You are currently not an authorized user.__\n\n"
            f"💼 **Unlock Premium Features:**\n"
            f"✨ Better Speed\n"
            f"✨ Extended support\n"
            f"✨ Unlimited Renaming\n\n"
            f"Click the button below to buy premium!"
        )
        
        # Send message with the "Buy Premium" button
        await message.reply_text(unauthorized_message, reply_markup=buy_premium_button)

@Client.on_message(filters.command("coupan") & (filters.private | filters.group))
async def generate_coupons_command(client: Client, message: Message):
    if message.from_user.id != ADMIN:
        await message.reply_text(f"{user_mention(message.from_user)}, you cannot use this command; it's only for my master.")
        return

    await message.reply_text("Please provide the duration for the coupons.")

    response = await client.listen(message.chat.id, timeout=60)  # Adjust timeout as needed
    duration = response.text.strip()
    duration_td = parse_duration(duration)
    
    if not duration_td:
        await message.reply_text("Invalid duration provided. Please use a valid duration format (e.g., '30 days', '1 hour').")
        return

    await message.reply_text("Please provide the total number of coupons you want to generate.")

    response = await client.listen(message.chat.id, timeout=60)  # Adjust timeout as needed
    try:
        num_coupons = int(response.text.strip())
        if num_coupons <= 0:
            raise ValueError
    except ValueError:
        await message.reply_text("Invalid number of coupons. Please enter a positive integer.")
        return

    coupons = generate_coupons("ELITES-", num_coupons)
    expiry_time = datetime.now() + duration_td

    for coupon in coupons:
        await db.save_coupon(coupon, duration, expiry_time)

    coupon_list = "\n".join(f"<code>{coupon}</code>" for coupon in coupons)
    await message.reply_text(f"Generated {num_coupons} coupons:\n\n{coupon_list}")

    log_message = (f"Coupons Generated 🎟️...\n\n"
                   f"**Generated by:** {user_mention(message.from_user)} `{message.from_user.id}`\n"
                   f"**Duration:** `{duration}`\n"
                   f"**Coupons:**\n{coupon_list}\n\n"
                   f"**Generated Time:** `{format_timestamp()}`")
    await client.send_message(Config.LOG_CHANNEL, log_message)
       

@Client.on_message(filters.command("redeem") & (filters.private | filters.group))
async def redeem_coupon_command(client: Client, message: Message):
    coupon_code = message.command[1] if len(message.command) > 1 else None
    
    if not coupon_code:
        await message.reply_text("Please provide a valid coupon code to redeem.")
        return
    
    coupon_data = await db.get_coupon(coupon_code)
    if not coupon_data or coupon_data["redeemed"]:
        await message.reply_text("Invalid or already redeemed coupon code.")
        return

    user_id = message.from_user.id
    duration_td = parse_duration(coupon_data["duration"])
    expiry_time = datetime.now() + duration_td

    if await db.is_user_authorized(user_id):
        await message.reply_text("You are already authorized.")
        return

    await db.authorize_user(user_id, expiry_time)
    await db.redeem_coupon(coupon_code, user_id)

    timestamp = format_timestamp()
    expiry_str = format_timestamp(expiry_time)
    
    auth_message = (f"🎉 Congratulations! You have been authorized!\n\n"
                    f"**User:** {user_mention(message.from_user)}\n"
                    f"**Authorization Duration:** `{coupon_data['duration']}`\n"
                    f"**Authorization Start:** `{timestamp}`\n"
                    f"**Authorization Expiry:** `{expiry_str}`")
    await message.reply_text(auth_message)
    
    log_message = (f"Coupon Redeemed 🎟️...\n\n"
                   f"**User:** {user_mention(message.from_user)} `{user_id}`\n"
                   f"**Coupon Code:** `{coupon_code}`\n"
                   f"**Duration:** `{coupon_data['duration']}`\n"
                   f"**Redemption Time:** `{timestamp}`\n"
                   f"**Authorization Expiry:** `{expiry_str}`")
    await client.send_message(Config.LOG_CHANNEL, log_message)
    
