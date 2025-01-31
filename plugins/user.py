from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from helper.database import db  # Import the database helper

@Client.on_message(filters.command("user"))
async def user_handler(client: Client, message: Message):
    args = message.command[1:]  # Get the arguments after /user
    if not args:
        await message.reply("❌ Please provide a user ID or username.\nExample: `/user 123456789` or `/user @username`")
        return

    identifier = args[0]
    
    # Fetch user profile from the database
    profile = await db.get_profile_by_id_or_username(identifier)
    if not profile:
        await message.reply("❌ User profile not found.")
        return

    user_id = profile["user_id"]
    likes_count = await db.get_like_count(user_id)

    # Create "Like" button
    like_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"👍 {likes_count} Likes", callback_data=f"like_{user_id}")]]
    )

    await message.reply_photo(
        photo=profile["photo"],
        caption=(
            f"**Profile Card**\n"
            f"👤 **Name:** {profile['name']}\n"
            f"📛 **Telegram Name:** {profile['first_name']} {profile['last_name']}\n"
            f"🆔 **User ID:** `{user_id}`\n"
            f"🌍 **Location:** {profile['city']}, {profile['country']}\n"
            f"🎂 **Age:** {profile['age']}\n"
            f"💎 **Premium:** {'Yes' if profile['is_premium'] else 'No'}\n"
        ),
        reply_markup=like_button
    )

# Handle Like Button
@Client.on_callback_query(filters.regex(r"^like_(\d+)$"))
async def handle_like(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[1])  # Extract the user ID
    liker_id = callback_query.from_user.id  # The user who clicked the button
    
    # Toggle like status in the database
    liked = await db.toggle_like(liker_id, user_id)

    # Get updated like count
    likes_count = await db.get_like_count(user_id)

    # Update the button text dynamically
    like_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton(f"👍 {likes_count} Likes", callback_data=f"like_{user_id}")]]
    )

    # Edit the message to reflect the new like count
    await callback_query.message.edit_reply_markup(reply_markup=like_button)

    # Send an alert message
    action = "liked" if liked else "unliked"
    await callback_query.answer(f"You {action} the profile of {user_id}!")
