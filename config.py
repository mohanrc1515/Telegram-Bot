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
    FORCE_SUB_CHANNELS = os.environ.get('FORCE_SUB_CHANNELS', 'Elites_Bots,Elites_Assistance').split(',')
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "-1002491891768"))
    NEW_USER_LOG = int(os.environ.get("NEW_USER_LOG", "-1002367669203"))
    
    # wes response configuration     
    WEBHOOK = bool(os.environ.get("WEBHOOK", "True"))


class Txt(object):
    # part of text configuration
        
    START_TXT = """<b>Aʜᴏʏ {} ⚔️ !

Wᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ Uʟᴛɪᴍᴀᴛᴇ Fɪʟᴇ Rᴇɴᴀᴍɪɴɢ Bᴏᴛ! 

🎭 <u>Pᴜʀᴘᴏꜱᴇ oғ Tʜᴇ Bᴏᴛ:</u>
Tʜɪꜱ ʙᴏᴛ ɪꜱ ᴅᴇꜱɪɢɴᴇᴅ ᴛᴏ ᴍᴀᴋᴇ ʀᴇɴᴀᴍɪɴɢ ᴀɴɪᴍᴇ ᴀɴᴅ ꜱᴇʀɪᴇꜱ ғɪʟᴇꜱ ᴀ ʙʀᴇᴇᴢᴇ, ᴇʟɪᴍɪɴᴀᴛɪɴɢ ᴀɴʏ ꜱᴛʀᴇꜱꜱ ᴀɴᴅ ᴇɴꜱᴜʀɪɴɢ ᴀɴ ᴇғғᴏʀᴛʟᴇꜱꜱ ᴘʀᴏᴄᴇꜱꜱ. 

──────────────────</b> """
