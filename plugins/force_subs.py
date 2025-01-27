import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant
from config import Config

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS


async def not_subscribed(_, __, message):
    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await message._client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except UserNotParticipant:
            return True
    return False


@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    not_joined_channels = []
    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)

    buttons = [
        [
            InlineKeyboardButton(
                text=f"📢 Join {channel.capitalize()} 📢", url=f"https://t.me/{channel}"
            )
        ]
        for channel in not_joined_channels
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="⚡ Verify ⚡", callback_data="check_subscription"
            )
        ]
    )

    text = "**Sorry, you're not joined to all required channels 😐. Please join the update channels to continue**"
    await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    not_joined_channels = []

    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(channel, user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)

    if not not_joined_channels:
        await callback_query.message.edit_text(
            "**You have joined all the required channels. Thank you!  /start now**"
        )
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"📢 Join {channel.capitalize()} 📢",
                    url=f"https://t.me/{channel}",
                )
            ]
            for channel in not_joined_channels
        ]
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⚡ Verify ⚡", callback_data="check_subscription"
                )
            ]
        )

        text = "**You haven't joined all the required channels. Please join them to continue. **"
        await callback_query.message.edit_text(
            text=text, reply_markup=InlineKeyboardMarkup(buttons)
        )
        



"""
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid
from config import Config
from helper.database import db
import logging

logger = logging.getLogger(__name__)

async def check_subscription(client, user_id, channel):
    try:
        member = await client.get_chat_member(channel, user_id)
        if member.status in [enums.ChatMemberStatus.MEMBER, enums.ChatMemberStatus.RESTRICTED, enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]:
            return True
    except UserNotParticipant:
        pass
    except PeerIdInvalid:
        logger.error(f"Channel {channel} is invalid or bot is not an admin.")
    except Exception as e:
        logger.exception(e)
    return False

async def get_join_request_link(client, channel_id):
    try:
        invite_link = await client.create_chat_invite_link(int(channel_id), creates_join_request=True)
        return invite_link.invite_link
    except ChatAdminRequired:
        logger.error(f"Bot must be an admin in the channel {channel_id}.")
        return None

async def not_subscribed(_, client, message):
    # Add user to the database or perform other necessary actions
    await db.add_user(client, message)  # Assuming you have an `add_user` function

    # If there's no forced subscription or required channels, skip the check
    if not Config.FORCE_SUB and not Config.REQ_CHANNEL:
        return False
    
    try:
        # Check if the user is subscribed to the FORCE_SUB channel
        force_user = await client.get_chat_member(Config.FORCE_SUB, message.from_user.id)
        if force_user.status == enums.ChatMemberStatus.BANNED:
            return True  # Banned from force channel, considered unsubscribed
        
        # Check if the user is subscribed to the REQ_CHANNEL
        req_user = await client.get_chat_member(Config.REQ_CHANNEL, message.from_user.id)
        if req_user.status == enums.ChatMemberStatus.BANNED:
            return True  # Banned from required channel, considered unsubscribed

        # If subscribed to both channels, return False
        return False

    except UserNotParticipant:
        # User is not a participant in either the force or required channel
        return True

    except Exception as e:
        # Log any other exceptions that occur
        logging.error(f"Error checking subscription or join request: {e}")
        return True

    # Default to True (indicating user is not subscribed) if any error occurs
    return True



@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    buttons = []
    force_subscribed = await check_subscription(client, message.from_user.id, Config.FORCE_SUB)
    req_subscribed = await check_subscription(client, message.from_user.id, Config.REQ_CHANNEL)
    join_req_sent = await db.find_join_req(message.from_user.id, Config.REQ_CHANNEL)

    if not force_subscribed:
        buttons.append([InlineKeyboardButton("⚡ Join Force Channel ⚡", url=f"https://t.me/{Config.FORCE_SUB}")])

    if not (req_subscribed or join_req_sent):
        invite_link = await get_join_request_link(client, Config.REQ_CHANNEL)
        if invite_link:
            buttons.append([InlineKeyboardButton("⚡ Request to Join ⚡", url=invite_link)])

    # Always include the "Verify" button
    buttons.append([InlineKeyboardButton("Verify", callback_data="verify_subscription")])

    if buttons:
        await message.reply_text(
            "<b>Hello! To use this bot, you must join the required channels. After joining, press Verify.</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        pass

@Client.on_callback_query(filters.regex("verify_subscription"))
async def verify_subscription(client, query):
    user_id = query.from_user.id
    force_subscribed = await check_subscription(client, user_id, Config.FORCE_SUB)
    req_subscribed = await check_subscription(client, user_id, Config.REQ_CHANNEL)
    join_req_sent = await db.find_join_req(user_id, Config.REQ_CHANNEL)

    if force_subscribed and (req_subscribed or join_req_sent):
        await query.message.edit_text("✅ You have successfully joined all the required channels. You can now use the bot!")
        await db.req_col.delete_one({'id': user_id, 'channel_id': Config.REQ_CHANNEL})
    else:
        buttons = []
        if not force_subscribed:
            buttons.append([InlineKeyboardButton("⚡ Join Force Channel ⚡", url=f"https://t.me/{Config.FORCE_SUB}")])
        if not (req_subscribed or join_req_sent):
            invite_link = await get_join_request_link(client, Config.REQ_CHANNEL)
            if invite_link:
                buttons.append([InlineKeyboardButton("⚡ Request to Join ⚡", url=invite_link)])

        buttons.append([InlineKeyboardButton("Verify", callback_data="verify_subscription")])

        await query.message.edit_text(
            "❌ You haven't joined the required channels yet. Please join and then click Verify.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

@Client.on_message(filters.command("delreq") & filters.user(Config.ADMIN))
async def delreq_command(client, message):
    await db.del_join_req()  # Clear all join requests from the database
    await message.reply_text("All join requests have been deleted.")

    """
