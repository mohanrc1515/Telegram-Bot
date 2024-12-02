import time
import subprocess
import os
import ffmpeg
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from pyrogram.types import Message


async def fix_thumb(thumb):
    width = 0
    height = 0
    try:
        if thumb != None:
            parser = createParser(thumb)
            metadata = extractMetadata(parser)
            if metadata.has("width"):
                width = metadata.get("width")
            if metadata.has("height"):
                height = metadata.get("height")
                
            # Open the image file
            with Image.open(thumb) as img:
                # Convert the image to RGB format and save it back to the same file
                img.convert("RGB").save(thumb)
            
                # Resize the image
                resized_img = img.resize((width, height))
                
                # Save the resized image in JPEG format
                resized_img.save(thumb, "JPEG")
            parser.close()
    except Exception as e:
        print(e)
        thumb = None 
       
    return width, height, thumb
    
async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = f"{output_directory}/{time.time()}.jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    return None
    
    
async def get_mediainfo(file_path):
    process = subprocess.Popen(
        ["mediainfo", file_path, "--Output=HTML"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise Exception(f"Error getting media info: {stderr.decode().strip()}")
    return stdout.decode().strip()    
  
async def get_and_upload_mediainfo(bot, output_file, media):
    media_info_html = get_mediainfo(output_file)

    media_info_html = (
        f"<strong>ELITES BOTZ</strong><br>"
        f"<strong>MediaInfo X</strong><br>"
        f"{media_info_html}"
        f"<p>Designed By Zᴇɴɪᴛꜱᴜ 様</p>"
    )

    response = telegraph.post(
        title="MediaInfo",
        author="ELITES BOTZ",
        author_url="https://t.me/Elites_Bots",
        text=media_info_html
    )
    link = f"https://graph.org/{response['path']}"

    return media_info_html, link


async def add_metadata(input_path, output_path, sub_title, sub_author, sub_subtitle, sub_audio, sub_video, sub_artist, download_msg):
    try:
        #  await download_msg.edit("<i>I Found Metadata, Adding Into Your File ⚡</i>")
        command = [
            'ffmpeg', '-y', '-i', input_path, '-map', '0', '-c:s', 'copy', '-c:a', 'copy', '-c:v', 'copy',
            '-metadata', f'title={sub_title}',  # Set title metadata
            '-metadata', f'author={sub_author}',  # Set author metadata
            '-metadata:s:s', f'title={sub_subtitle}',  # Set subtitle metadata
            '-metadata:s:a', f'title={sub_audio}',  # Set audio metadata
            '-metadata:s:v', f'title={sub_video}',  # Set video metadata
            '-metadata', f'artist={sub_artist}',  # Set artist metadata
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        e_response = stderr.decode().strip()
        t_response = stdout.decode().strip()
        print(e_response)
        print(t_response)

        if os.path.exists(output_path):
            print("Metadata has been successfully added to the file.")
            return output_path
        else:
            print("Failed to add metadata to the file.")
            return None
    except Exception as e:
        print(f"Error occurred while adding metadata: {str(e)}")
        return None
        
