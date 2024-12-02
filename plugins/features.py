from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from config import Txt

# Define callback data constants
AUTO_RENAME_CALLBACK = "auto_rename"
META_DATA_CALLBACK = "meta_data"
THUMBNAIL_SETUP_CALLBACK = "thumbnail_setup"
CAPTION_SETUP_CALLBACK = "caption_setup"
FILE_SEQUENCE_CALLBACK = "file_sequence"
AUTHENTICATION_CALLBACK = "authentication"
DUMP_CALLBACK = "dump"

# /features command to list all the bot features with a button UI
@Client.on_message(filters.private & filters.command(["features"]))
async def features_command(client, message):
    await message.reply_photo(
        photo="https://graph.org/file/304a4a1c70aa0c520e956.jpg",
        caption="""
📌 **Welcome to our Feature Showcase!** 📌

Here are some of the advanced functionalities you can explore with our bot:

🔹 **Autorename Feature**  
🔹 **Metadata Editing**
🔹 **Files Dumping**
🔹 **Files Sequencing**
🔹 **Refer & Gain Authentication**  
🔹 **Custom Thumbnail & Caption**

Feel free to explore these features by using the buttons below. For suggestions, reach out to our [Support Group](https://t.me/elites_assistance).
       """,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Autorename", callback_data=AUTO_RENAME_CALLBACK),
                InlineKeyboardButton("Metadata", callback_data=META_DATA_CALLBACK),
                InlineKeyboardButton("Thumbnail", callback_data=THUMBNAIL_SETUP_CALLBACK)
            ],
            [
                InlineKeyboardButton("Caption", callback_data=CAPTION_SETUP_CALLBACK),
                InlineKeyboardButton("Dump", callback_data=DUMP_CALLBACK),
                InlineKeyboardButton("Refer", callback_data=AUTHENTICATION_CALLBACK)
            ],
            [
                InlineKeyboardButton("Sequencing", callback_data=FILE_SEQUENCE_CALLBACK),
                InlineKeyboardButton("Back", callback_data="commands"),
                InlineKeyboardButton("Support", url="https://t.me/elites_assistance")
            ]
        ])
    )

@Client.on_callback_query(filters.regex("features"))
async def features_callback(client, query: CallbackQuery):
    await query.message.edit_text(
        text="""
📌 **Welcome to our Feature Showcase!** 📌

Here are some of the advanced functionalities you can explore with our bot:

🔹 **Autorename Feature**  
🔹 **Metadata Editing**
🔹 **Files Dumping**
🔹 **Files Sequencing**
🔹 **Refer & Gain Authentication**  
🔹 **Custom Thumbnail & Caption**

Feel free to explore these features by using the buttons below. For suggestions, reach out to our [Support Group](https://t.me/elites_assistance).
        """,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Autorename", callback_data=AUTO_RENAME_CALLBACK),
                InlineKeyboardButton("Metadata", callback_data=META_DATA_CALLBACK),
                InlineKeyboardButton("Thumbnail", callback_data=THUMBNAIL_SETUP_CALLBACK)
            ],
            [
                InlineKeyboardButton("Caption", callback_data=CAPTION_SETUP_CALLBACK),
                InlineKeyboardButton("Dump", callback_data=DUMP_CALLBACK),
                InlineKeyboardButton("Refer", callback_data=AUTHENTICATION_CALLBACK)
            ],
            [
                InlineKeyboardButton("Sequencing", callback_data=FILE_SEQUENCE_CALLBACK),
                InlineKeyboardButton("Back", callback_data="commands"),
                InlineKeyboardButton("Support", url="https://t.me/elites_assistance")
            ]
        ])
    )
    await query.answer()

# Handle all feature-related callbacks in one function
@Client.on_callback_query(filters.regex("|".join([
    AUTO_RENAME_CALLBACK,
    META_DATA_CALLBACK,
    THUMBNAIL_SETUP_CALLBACK,
    CAPTION_SETUP_CALLBACK,
    FILE_SEQUENCE_CALLBACK,
    AUTHENTICATION_CALLBACK,
    DUMP_CALLBACK    
])))
async def feature_callback(client, query: CallbackQuery):
    callback_data = query.data
    
    # Feature texts from Txt module
    feature_texts = {
        AUTO_RENAME_CALLBACK: Txt.FILE_NAME_TXT,
        META_DATA_CALLBACK: Txt.METADATA_TXT,
        THUMBNAIL_SETUP_CALLBACK: Txt.THUMB_TXT,
        CAPTION_SETUP_CALLBACK: Txt.CAPTION_TXT,
        FILE_SEQUENCE_CALLBACK: Txt.SEQUENCE_TXT,
        AUTHENTICATION_CALLBACK: Txt.REFER_TXT,
        DUMP_CALLBACK: Txt.DUMP_TXT,
    }
    
    # Get the text for the selected feature
    text = feature_texts.get(callback_data, "Feature details not found.")

    await query.message.edit_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="features")]
        ])
    )
    await query.answer()
