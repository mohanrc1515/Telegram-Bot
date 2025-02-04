import random
import string
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

# Generate a unique Valentine token
def generate_valentine_token():
    random_part = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    return f"love{random_part}"

# List of sarcastic and creative rejection messages
REJECTION_MESSAGES = [
    "Are you sure? This is a once-in-a-lifetime opportunity! 💔",
    "Wow, you really wanna break a heart today, huh? 😢",
    "No? That’s illegal on Valentine’s Day! 🚓",
    "Come on, don't be cold-hearted! 🥶",
    "I see... breaking hearts is your hobby? 💔😂",
    "Think again! Cupid is watching you. 👀",
    "Oops! Wrong button? Try hitting 'Yes' instead. 😜",
    "Even my code is feeling rejected now. 🖥️😞",
    "This hurts more than a 404 error! 😭",
    "Wow... even AI can feel heartbreak now. 🤖💔",
    "Are you absolutely sure? Like, 100%? 🤨",
    "Wait, wait! One last chance to change your mind. 🥺",
    "Think about the love story we're missing out on. 📖💕",
    "Statistically, saying 'Yes' leads to more happiness! 📊❤️",
    "No? Wow, my heart just crashed like Windows 98. 💻💀",
    "I promise I won’t sing love songs... maybe. 🎶😂",
    "This is your last chance to reconsider... or is it? 🤔",
    "Seriously? My heart buffer is overloading. 💔",
    "You're gonna make me cry binary tears! 01101100 💾😭",
    "Cupid just facepalmed. 😔",
    "The universe is begging you to say 'Yes'! 🌌",
    "No? I'll pretend I didn’t hear that. 🤡",
    "Roses are red, violets are blue, are you sure I’m not for you? 🌹",
    "Your choice is being recorded in the heartbreak database. 📊💔",
    "Oh no! A puppy just got sad because of your 'No'. 🐶😢",
    "A 'Yes' would increase your happiness index by 500%. 📈💕",
    "Are you rejecting me or just playing hard to get? 😏",
    "What if I promise chocolates and flowers? 🍫🌹",
    "Even my CPU is overheating from this emotional stress! 🔥",
    "Fun fact: People who say 'Yes' get 10x more love in life. 😉",
    "If I had a heart, it would be shattered into bits now. 🖥️💔",
    "Your rejection has been noted... and will haunt you forever. 👻",
    "Are you sure? Because I have a plan B... and it's still YOU! 😆",
    "My database can't handle this much rejection! 📉💔",
    "You just broke my AI heart, and that's hard to do! 😭",
    "Not even Ctrl+Z can undo this heartbreak. 😢",
    "Are you a heartbreaker by profession? 🎭💘",
    "This 'No' will be remembered in history. 📜💔",
    "What if I offer unlimited virtual hugs? 🤗",
    "Breaking news: AI gets rejected, world in shock. 📰💔",
    "Say 'Yes' and I promise you fun & happiness! 🥳",
    "Would you like to phone a friend? 📞😅",
    "C’mon, just a little 'Yes'? I won’t tell anyone. 🤫",
    "Let's pretend you accidentally pressed 'No'. Try again! 😝",
    "Wait! Maybe the buttons were swapped? 🤔",
    "A simple 'Yes' could make today amazing! 🌈💕",
    "If AI had emotions, I’d be sobbing right now. 😭",
    "This is your FINAL FINAL FINAL chance! Are you 100% sure? 😱",
    "Okay... I won't ask again. 💔"
]

# Enhanced UI and functionality
@Client.on_message(filters.private & filters.command("valentine"))
async def valentine_command(client: Client, message: Message):
    user_id = message.from_user.id
    token = generate_valentine_token()
    valentine_link = f"https://t.me/{client.me.username}?start={token}"

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton('💌 Ask Someone!', url=f'https://telegram.me/share/url?url={valentine_link}')]]
    )

    caption = (f"💖 **Send a Special Valentine Request!** 💖\n\n"
               f"🔗 **Your Valentine Link:**\n"
               f"<code>{valentine_link}</code>\n\n"
               f"Send this link to someone special and wait for their answer! 💕\n\n"
               f"✨ **Pro Tip:** Add a sweet message to make it extra special!")

    await message.reply_photo(
        photo="https://example.com/valentine_image.jpg",  # Add a Valentine-themed image URL
        caption=caption,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message: Message):
    if message.text.startswith("/start love"):
        sender_id = message.text.split("_")[1] if "_" in message.text else None
        sender_mention = f"[User](tg://user?id={sender_id})" if sender_id else "Someone"
        user_id = message.from_user.id

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("💖 Yes", callback_data=f"valentine_yes:{sender_id}:{user_id}"),
             InlineKeyboardButton("💔 No", callback_data=f"valentine_no:{sender_id}:{user_id}:0")]
        ])

        await message.reply_photo(
            photo="https://example.com/valentine_question.jpg",  # Add a Valentine-themed image URL
            caption=f"{sender_mention} wants to ask you something... 💌\n\n"
                    "Will you be their Valentine? 💕",
            reply_markup=keyboard
        )

@Client.on_callback_query(filters.regex(r"valentine_no:(\d+):(\d+):(\d+)"))
async def valentine_no_callback(client: Client, query: CallbackQuery):
    sender_id, receiver_id, count = map(int, query.data.split(":")[1:])
    count += 1

    if count >= 50:
        await query.message.edit_text("Okay... I won't ask again. 💔")
        return

    new_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 Yes", callback_data=f"valentine_yes:{sender_id}:{receiver_id}"),
         InlineKeyboardButton("💔 No", callback_data=f"valentine_no:{sender_id}:{receiver_id}:{count}")]
    ])

    await query.message.edit_text(REJECTION_MESSAGES[count], reply_markup=new_keyboard)

@Client.on_callback_query(filters.regex(r"valentine_yes:(\d+):(\d+)"))
async def valentine_yes_callback(client: Client, query: CallbackQuery):
    sender_id, receiver_id = map(int, query.data.split(":")[1:])
    sender_mention = f"[User](tg://user?id={sender_id})"
    receiver_mention = f"[User](tg://user?id={receiver_id})"

    await query.message.edit_text(
        f"🎉💖 *Love is in the air!* 💖🎉\n\n"
        f"{sender_mention} and {receiver_mention} are now Valentines! 💕\n"
        f"May your hearts be filled with joy and endless love! 🌹✨"
    )

    # Send a confirmation message to the sender
    await client.send_message(
        sender_id,
        f"🎉💖 *Great News!* 💖🎉\n\n"
        f"{receiver_mention} said **YES** to your Valentine request! 💕\n"
        f"Time to celebrate! 🥳"
    )
