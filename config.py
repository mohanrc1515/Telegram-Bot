import re, os, time
id_pattern = re.compile(r'^.\d+$') 

class Config(object):
    # pyro client config
    API_ID    = os.environ.get("API_ID", "10964975")
    API_HASH  = os.environ.get("API_HASH", "86588233b82bdec8e1c18929851642cc")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "7759643743:AAFwEzw3TCCseGbirYK_YEDV8Fr1p89Z0pk") 

    # database config
    DB_NAME = os.environ.get("DB_NAME","auth-autorename")     
    DB_URL  = os.environ.get("DB_URL","mongodb+srv://arsenalbotz05:arsenalbotz05@auth-autorename.md8ze.mongodb.net/?retryWrites=true&w=majority&appName=auth-autorename")
   
    # other configs
    BOT_UPTIME  = time.time()
    START_PIC   = os.environ.get("START_PIC", "https://envs.sh/7Bt.jpg")
    ADMIN       = [int(admin) if id_pattern.search(admin) else admin for admin in os.environ.get('ADMIN', '6070793480 6006418463').split()]
    FORCE_SUB_CHANNELS   = os.environ.get("FORCE_SUB_CHANNELS", "Elites_Bots") 
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002491891768"))
    NEW_USER_LOG = int(os.environ.get("NEW_USER_LOG", "-1002367669203"))
    FILES_CHANNEL = int(os.environ.get("FILES_CHANNEL", "-1002261537046"))
    REFER_CHANNEL = int(os.environ.get("REFER_CHANNEL", "-1002259020030"))
    POINTS_PER_REFERRAL = int(os.environ.get("POINTS_PER_REFERRAL", "10"))
    USER_REPLY = "You are not authorised to use this bot..!\n\n- Enter /premium to learn more about getting authorization.\n- Or use /refer to get FREE authorization!"
    
    # wes response configuration     
    WEBHOOK = bool(os.environ.get("WEBHOOK", "True"))


class Txt(object):
    # part of text configuration
        
    START_TXT = """<b>Aʜᴏʏ {} ⚔️ !

Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ Uʟᴛɪᴍᴀᴛᴇ Fɪʟᴇ Rᴇɴᴀᴍɪɴɢ Bᴏᴛ! 

🎭 <u>Pᴜʀᴘᴏꜱᴇ oғ Tʜᴇ Bᴏᴛ:</u>
Tʜɪꜱ ʙᴏᴛ ɪꜱ ᴅᴇꜱɪɢɴᴇᴅ ᴛᴏ ᴍᴀᴋᴇ ʀᴇɴᴀᴍɪɴɢ ᴀɴɪᴍᴇ ᴀɴᴅ ꜱᴇʀɪᴇꜱ ғɪʟᴇꜱ ᴀ ʙʀᴇᴇᴢᴇ, ᴇʟɪᴍɪɴᴀᴛɪɴɢ ᴀɴʏ ꜱᴛʀᴇꜱꜱ ᴀɴᴅ ᴇɴꜱᴜʀɪɴɢ ᴀɴ ᴇғғᴏʀᴛʟᴇꜱꜱ ᴘʀᴏᴄᴇꜱꜱ. 

──────────────────</b> """

    
    FILE_NAME_TXT = """ <u><b>SETUP AUTO RENAME FORMAT</b></u>
    
Use These Keywords To Setup Custom File Name
    
➝ title :- to replace anime or series title name
➝ season :- to replace season number
➝ episode :- to replace episode number
➝ quality :- to replace video resolution
➝ audio :- to replace video language
➝ volume :- to replace manga volume number
➝ chapter :- to replace manga chapter number
    
‣ <b>Example :</b> <code>/autorename S{season} E{episode} - {title} [{audio}] [{quality}] @Anime_Elites</code>
    
‣ <b>Example 2:</b> <code>/autorename Vol{volume} Ch{chapter} - {title} @Manga_Elites</code> """
   
    
    THUMB_TXT = """ **<u>ᴛᴏ ꜱᴇᴛ ᴄᴜꜱᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ</u>**
➜ /start: ꜱᴇɴᴅ ᴀɴʏ ᴘʜᴏᴛᴏ ᴛᴏ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ꜱᴇᴛ ɪᴛ ᴀꜱ ᴀ ᴛʜᴜᴍʙɴᴀɪʟ..
➜ /del_thumb: ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴏʟᴅ ᴛʜᴜᴍʙɴᴀɪʟ.
➜ /view_thumb: ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴠɪᴇᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴛʜᴜᴍʙɴᴀɪʟ.
➜ /getthumb: ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴇxᴛʀᴀᴄᴛ ᴛʜᴜᴍʙɴᴀɪʟ ғʀᴏᴍ ᴀɴʏ ғɪʟᴇ. """
    

    CAPTION_TXT = """<b><u>Tᴏ Sᴇᴛ Cᴜꜱᴛᴏᴍ Cᴀᴘᴛɪᴏɴ ᴀɴᴅ Mᴇᴅɪᴀ Tʏᴘᴇ</u> :

<u>Vᴀʀɪᴀʙʟᴇꜱ</u>
• Sɪᴢᴇ: {filesize}  
• Dᴜʀᴀᴛɪᴏɴ: {duration}  
• Fɪʟᴇɴᴀᴍᴇ: {filename}

➜ /set_caption: Uꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ꜱᴇᴛ ᴀ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.  
➜ /see_caption: Uꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴠɪᴇᴡ ʏᴏᴜʀ ᴄᴜʀʀᴇɴᴛ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.  
➜ /del_caption: Uꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.
➜ /caption_mode: Usᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ sᴇʟᴇᴄᴛ ʏᴏᴜʀ ᴄᴀᴘᴛɪᴏɴ ᴛʏᴘᴇ

Exᴀᴍᴘʟᴇ:</b> <code>/set_caption {filename}</code>"""

    
    COMMANDS_TXT = """<b><u> Eꜱꜱᴇɴᴛɪᴀʟ Cᴏᴍᴍᴀɴᴅꜱ: </b></u>
➲ /settings : <b>Cᴏɴғɪɢᴜʀᴇ ʏᴏᴜʀ ʙᴏᴛ'ꜱ ꜱᴇᴛᴛɪɴɢꜱ.</b>
➲ /autorename : <b>Tʜᴇ ᴍᴀɪɴ ᴄᴏᴍᴍᴀɴᴅ ғᴏʀ ᴄᴏɴғɪɢᴜʀɪɴɢ ʏᴏᴜʀ ᴀᴜᴛᴏ ʀᴇɴᴀᴍᴇ ꜱᴇᴛᴛɪɴɢꜱ.</b>
➲ /setmediatype : <b>Sᴘᴇᴄɪғʏ ʏᴏᴜʀ ᴘʀᴇғᴇʀʀᴇᴅ ᴍᴇᴅɪᴀ ᴛʏᴘᴇ ғᴏʀ ᴜᴘʟᴏᴀᴅꜱ. </b>
➲ /leaderboard : <b>Lᴇᴀᴅᴇʀʙᴏᴀʀᴅ ᴏғ ᴏᴜʀ ᴛᴏᴘ ʀᴇɴᴀᴍᴇʀꜱ.</b>
➲ /about : <b>Pʀᴏᴠɪᴅᴇꜱ ʙᴀꜱɪᴄ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ᴀʙᴏᴜᴛ ᴛʜᴇ ʙᴏᴛ.</b>

<b>Iғ ʏᴏᴜ ꜱᴛɪʟʟ ʜᴀᴠᴇ ᴅᴏᴜʙᴛꜱ ʜɪᴛ /tutorial ғᴏʀ ᴀ ᴄᴏᴍᴘʟᴇᴛᴇ ᴡᴀʟᴋᴛʜʀᴏᴜɢʜ ᴠɪᴅᴇᴏ.</b> """

    SEQUENCE_TXT = """ <b><u>Tᴏ Bᴇɢɪɴ Fɪʟᴇ Sᴇǫᴜᴇɴᴄɪɴɢ:</u>

➜ /startsequence: Uꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ɪɴɪᴛɪᴀᴛᴇ ᴛʜᴇ ғɪʟᴇ ꜱᴇǫᴜᴇɴᴄɪɴɢ ᴘʀᴏᴄᴇꜱꜱ. Aғᴛᴇʀ ꜱᴛᴀʀᴛɪɴɢ, ʏᴏᴜ ᴄᴀɴ ꜱᴇɴᴅ ᴛʜᴇ ғɪʟᴇꜱ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ꜱᴇǫᴜᴇɴᴄᴇ ᴏɴᴇ ʙʏ ᴏɴᴇ.

➜ /endsequence: Oɴᴄᴇ ʏᴏᴜ’ᴠᴇ ꜱᴇɴᴛ ᴀʟʟ ᴛʜᴇ ғɪʟᴇꜱ, ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴛᴏ ᴄᴏᴍᴘʟᴇᴛᴇ ᴛʜᴇ ᴘʀᴏᴄᴇꜱꜱ. Tʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴛʜᴇɴ ꜱᴏʀᴛ ᴀɴᴅ ꜱᴇɴᴅ ᴛʜᴇ ғɪʟᴇꜱ ɪɴ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ᴏʀᴅᴇʀ.

Nᴏᴛᴇ: Aғᴛᴇʀ ғɪɴᴀʟɪᴢɪɴɢ ᴛʜᴇ ꜱᴇǫᴜᴇɴᴄᴇ ᴡɪᴛʜ /endsequence, ʏᴏᴜ ᴄᴀɴɴᴏᴛ ᴀᴅᴅ ᴍᴏʀᴇ ғɪʟᴇꜱ ᴛᴏ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ꜱᴇǫᴜᴇɴᴄᴇ. Tᴏ ꜱᴛᴀʀᴛ ᴀ ɴᴇᴡ ꜱᴇǫᴜᴇɴᴄᴇ, ꜱɪᴍᴘʟʏ ᴜꜱᴇ ᴛʜᴇ /startsequence ᴄᴏᴍᴍᴀɴᴅ ᴀɢᴀɪɴ.</b> """
      
    
    PREMIUM_TXT = """ **Hey** {} ✨
    
**<u>Upgrade to Premium</u>**

Unlock exclusive features and elevate your experience:

**Unlimited Renaming**: Rename as many files as you need without limits.  
**Early Access**: Be first to try our newest features.  
**Enhanced Speed**: Enjoy faster downloading and uploading.

**Pricing**:  
- 🗓️ **Monthly Premium**: ₹70/month  
- 📅 **Weekly Premium**: ₹29/week  
- 🕒 **Daily Premium**: ₹5/day  
- 🔒 **Private Bot**: Contact the owner for details

**Check your current status**: /myplan

**Want Premium for free ?** Simply use the command /refer and get premium at no cost!

Get Premium: Enhance your file renaming capabilities and enjoy the full potential of the bot!"""
    
    
    DUMP_TXT = """ 🌊 <u>**𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝘁𝗵𝗲 𝗗𝘂𝗺𝗽 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀 𝗚𝘂𝗶𝗱𝗲 !</u>**
    
1. 💻 𝗔𝗱𝗷𝘂𝘀𝘁 𝗦𝗲𝘁𝘁𝗶𝗻𝗴𝘀
   - **Command**: /dumpsettings
   - **Purpose**: Check the current status of your dump file setting, forward mode, and the connected channel.

2. 🛠️ 𝗖𝗼𝗻𝗳𝗶𝗴𝘂𝗿𝗲 𝗬𝗼𝘂𝗿 𝗗𝘂𝗺𝗽 𝗖𝗵𝗮𝗻𝗻𝗲𝗹
   - **Command**: /dump channel_id
   - **Purpose**: Set the channel where all your files will be dumped. This saves you from manually selecting and forwarding each file.
   
3. 📤 𝗗𝘂𝗺𝗽 𝗙𝗶𝗹𝗲𝘀
   - **Enabled**: Files will be directly to your dump channel.
   - **Disabled**: Files will be sent to you in bot's PM as usual.

4. 🔄 𝗙𝗼𝗿𝘄𝗮𝗿𝗱 𝗠𝗼𝗱𝗲
   - **Normal Mode**: Files are dispatched immediately to the dump channel after renaming.
   - **Sequence Mode**: Files are queued, and after using the /sequencedump command, they are sent in the correct order based on their season and episode...
   
**Note :**Make sure this bot is admin in your dump channel """
    
    PROGRESS_BAR = """<b>
    
🗃️ Size: {1} / {2}
🔄 Progress: {0}%
🚀 Speed: {3}/s
⏱️ ETA: {4} </b>"""
    

    # other text variables
    NEW_USER_TXT = (
    "🆕 **New User Alert!**\n"
    "A new user has started the bot\n"
    "• **Name:** {}\n"
    "• **User ID:** {}"
)


    METADATA_TXT = """**<u>Metadata Guide</u>**

<u>**Features**:</u>
1. **Toggle Metadata**: Enable/disable metadata handling.
2. **View Metadata**: Display current metadata:
   - **Title, Author, Artist, Subtitle, Audio, Video**
3. **Set Metadata**: Update values for the fields above.
4. **Edit Metadata**: Modify specific fields via chat.
5. **Reset Metadata**: Restore fields to default.

<u>**Description**:</u>
   - **Title**: The title of the media file.
   - **Author**: The creator or owner of the media.
   - **Artist**: The associated artist (e.g., musician, illustrator).
   - **Subtitle**: Any subtitle information.
   - **Audio**: Description or title of audio content.
   - **Video**: Details about the video content.

<u>**Instructions**:</u>
- Enter /metadata for the menu.
- Use buttons to enable/disable, view, or set metadata."""

    REFER_TXT = """ **<u>Refferal System</u>**

**Features**:
1. **Referral Links**: Get your refferal link from /refer.
2. **Track Referral Points**: View earned points.
3. **Claim Authorization**: Redeem points for authorization.

**Usage**:
- /refer: **Get your referral link.**
- /claim: **Claim authorization.**
- /top_referrals: **Leaderboard of our top referrals**

**Additional Info**:
- Refferal points per invite: 10 Points
- Total referral Points needed: 150 Points
- Authorization Duration: 1 Month
"""

    FEATURES_TXT = """
⚡ <u>**Welcome to our Feature Showcase !**</u> ⚡ 

➤ **Autorename Feature**  
➤ **Metadata Editing**
➤ **Files Dumping**
➤ **Custom Message Before & After Dump**
➤ **Files Sequencing**
➤ **Refer & Gain Authentication**  
➤ **Custom Thumbnail & Caption**

<blockquote>For any advices : @Elites_Assistance</blockquote>
"""
    

    
    DUMPMESSAGE_TXT= """**📖 <u>Dump Messages Guide</u> 📖**  

1. **/startdump** : Reply to a text, image, or sticker to set the **Dump start message**.  
- You can also use placeholders:  
 - `{quality}` = Quality (e.g., 1080p)  
 - `{title}` = Series title  
 - `{season}` = Season number
 - `{firstepisode}` = Episode number of first file
  - `{lastepisode}` = Episode number of last file  
  
• **Example:**  
`✧ Title : {title}
✧ Season : {season} | {quality}
✧ Episodes : {firstepisode} - {lastepisode}`  

2. **/enddump** : Same as `/startdump` but for the **end message**.

3. **/dlt_startdump** : Delete the dump start message.  

4. **/dlt_enddump** : Delete the dump end message.  

5. **/showdumptext** : View your current dump messages status.  

6. **/dumptextmode** : Set when to show messages: **Season**, **Quality**, **Both**, **Episode Batch**, **Custom Dump**.
   
Here’s a demo showcasing the various modes in action. [Click Here](https://t.me/+aar-9BKME342YTJk)."""

