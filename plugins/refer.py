import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors import UserNotParticipant
from datetime import datetime, timedelta
from config import Config, Txt
from helper.database import db
from helper.utils import *
import pytz

# Settings and Constants
ADMIN = 6006418463
REFERRAL_POINTS_THRESHOLD = 100
AUTH_DURATION = "1 month"

@Client.on_message(filters.private & filters.command("refer"))
async def refer_user(client: Client, message: Message):
    user_id = message.from_user.id
    referral_link = f"https://t.me/{client.me.username}?start=referral_{user_id}"

    # Fetch current referral points
    referral_points = await db.get_referral_points(user_id)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('Share Link', url=f'https://telegram.me/share/url?url={referral_link}'),
             InlineKeyboardButton(f"⌛ {referral_points}", callback_data=f"show_referral_points:{user_id}")],
            [InlineKeyboardButton('📘 Referral Help 📘', callback_data='refer_help')]
        ]
    )

    caption = (f"Invite your friends to use this bot and earn referral points!\n\n"
               f"**Your Referral Link:**👇\n"
               f"<code>{referral_link}</code>\n\n"
               f"For every successful referral, you will earn {Config.POINTS_PER_REFERRAL} points. "
               f"Once you reach {REFERRAL_POINTS_THRESHOLD} points, hit /claim and you will be authorized for {AUTH_DURATION}!")

    await client.send_photo(
        chat_id=message.chat.id,
        photo="https://graph.org/file/e9ddc7a10979c19875a7b.jpg",
        caption=caption,
        reply_markup=keyboard
    )

@Client.on_callback_query(filters.regex(r"show_referral_points:(\d+)"))
async def show_referral_points(client, callback_query):
    user_id = int(callback_query.matches[0].group(1))
    referral_points = await db.get_referral_points(user_id)
    await callback_query.answer(f"You have {referral_points} referral points.", show_alert=True)

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    if message.text.startswith("/start referral_"):
        referrer_id = int(message.text.split("_")[1])
        user_id = message.from_user.id
        if referrer_id == user_id:
            await message.reply("You cannot refer yourself.")
            return

        if await db.is_user_exist(user_id):
            await message.reply("You are already registered.")
            return

        # Add both the referrer and the new user to the database
        await db.add_user(client, message)
        await db.store_referral(user_id, referrer_id)
        await db.add_referral(referrer_id, user_id)  # Save the invitee info
        referrer_user = await client.get_users(referrer_id)

        # Notify the new user
        await message.reply(f"You have been referred by {referrer_user.first_name}.")

        # Notify the referrer
        await client.send_message(
            chat_id=referrer_id,
            text=f"{message.from_user.first_name} has started the bot using your referral link."
        )

        # Log the referral event
        await client.send_message(
            chat_id=Config.REFER_CHANNEL,
            text=(
                f"📥 **Referral Event**\n"
                f"👤 **Referred User:** {message.from_user.first_name} (ID: {message.from_user.id})\n"
                f"🔗 **Referred By:** {referrer_user.first_name} (ID: {referrer_id})"
            )
        )
    else:
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(client, message)

        # Define the new inline keyboard
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("Help & Commands", callback_data='commands')],
            [
                InlineKeyboardButton('Updates', url='https://t.me/Elites_Bots'),
                InlineKeyboardButton('Support', url='https://t.me/Elites_Assistance')
            ],
            [
                InlineKeyboardButton('About', callback_data='about'),
                InlineKeyboardButton('Premium', callback_data='premium')
            ]
        ])

        # Respond to the user
        if Config.START_PIC:
            await message.reply_photo(Config.START_PIC, caption=Txt.START_TXT.format(message.from_user.mention), reply_markup=button)
        else:
            await message.reply_text(text=Txt.START_TXT.format(message.from_user.mention), reply_markup=button, disable_web_page_preview=True)

@Client.on_message(filters.command("claim") & filters.private)
async def claim_referral(client: Client, message: Message):
    user_id = message.from_user.id

    try:
        if await db.is_user_authorized(user_id):  # Colon added here
            await message.reply("You are already authorized. Claim after your current authorization expires.")
            return

        referral_points = await db.get_referral_points(user_id)

        if referral_points < REFERRAL_POINTS_THRESHOLD:
            await message.reply("Not enough referral points. You need at least 100 points to claim authorization.")
            return

        remaining_points = referral_points - REFERRAL_POINTS_THRESHOLD
        await db.update_referral_points(user_id, remaining_points)

        auth_duration = parse_duration(AUTH_DURATION)
        expiration_date = datetime.now() + auth_duration if auth_duration else datetime.now() + timedelta(days=30)

        await db.authorize_user(user_id, expiration_date)

        await message.reply(f"Congratulations! You have been authorized for {AUTH_DURATION}. Your remaining referral points: {remaining_points}.")

        await client.send_message(
            chat_id=Config.LOG_CHANNEL,
            text=f"{user_mention(message.from_user)} has claimed authorization for {AUTH_DURATION}. Remaining referral points: {remaining_points}."
        )
    except Exception as e:
        await message.reply("An error occurred while processing your claim. Please try again later.")
        print(f"Error in claim_referral: {e}")

@Client.on_message(filters.command("referred_by") & filters.private)
async def referred_by(client: Client, message: Message):
    # Check if a user ID was provided
    if len(message.command) < 2:
        await message.reply("Please provide a user ID.")
        return

    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply("Invalid user ID. Please provide a valid number.")
        return

    try:
        # Fetch user details for the provided ID
        searched_user = await client.get_users(user_id)
        searched_user_mention = searched_user.mention
        
        # Fetch the referrer ID from the database
        referrer_id = await db.get_referrer(user_id)

        if referrer_id:
            # Fetch details of the referrer
            referrer_user = await client.get_users(referrer_id)
            referrer_mention = referrer_user.mention

            # Prepare the response with user and referrer information
            response = (
                f"👤 **User Info**\n"
                f"🔹 **ID:** {searched_user.id}\n"
                f"🔹 **Mention:** {searched_user_mention}\n\n"
                "🔗 **Referral Info**\n"
                f"🔹 **Referrer ID:** {referrer_user.id}\n"
                f"🔹 **Referrer Mention:** {referrer_mention}"
            )
        else:
            response = f"No referrer found for user {searched_user_mention}."

        # Send the response to the user
        await message.reply(response)

    except Exception as e:
        await message.reply(f"An error occurred while fetching referral info: {e}")
        print(f"Error in referred_by: {e}")

@Client.on_callback_query(filters.regex("refer_help"))
async def refer_help_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id  # Extract the user ID here
    # Inline keyboard with the back button to go back to /refer
    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_refer:{user_id}")]
        ]
    )
    
    await callback_query.message.edit_text(
        text=Txt.REFER_TXT,
        reply_markup=keyboard
    )


@Client.on_callback_query(filters.regex(r"back_to_refer:(\d+)"))
async def back_to_refer(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.matches[0].group(1))
    
    referral_link = f"https://t.me/{client.me.username}?start=referral_{user_id}"

    # Fetch current referral points
    referral_points = await db.get_referral_points(user_id)

    keyboard = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton('Share Link', url=f'https://telegram.me/share/url?url={referral_link}'),
             InlineKeyboardButton(f"⌛ {referral_points}", callback_data=f"show_referral_points:{user_id}")],
            [InlineKeyboardButton('📘 Referral Help 📘', callback_data='refer_help')]
        ]
    )

    caption = (f"Invite your friends to use this bot and earn referral points!\n\n"
               f"**Your Referral Link:**👇\n"
               f"<code>{referral_link}</code>\n\n"
               f"For every successful referral, you will earn {Config.POINTS_PER_REFERRAL} points. "
               f"Once you reach {REFERRAL_POINTS_THRESHOLD} points, hit /claim and you will be authorized for {AUTH_DURATION}!")

    await callback_query.message.edit_text(caption, reply_markup=keyboard)
