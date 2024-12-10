from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from helper.extraction import extract_episode_number  # Importing the helper function

# Dictionary to track the check process for each user
user_check_mode = {}

# Start the check process by asking for the first episode link
@Client.on_message(filters.command("startcheck") & filters.private)
async def start_check(client, message):
    user_id = message.from_user.id

    if user_id in user_check_mode and user_check_mode[user_id]:
        await message.reply_text("You are already in the check process. Use /endcheck to finish.")
        return

    user_check_mode[user_id] = {"state": "start", "episodes": []}
    await message.reply_text("Please provide the link of the first episode.")

# Handle the link of the first episode
@Client.on_message(filters.text & filters.private)
async def handle_start_check(client, message):
    user_id = message.from_user.id

    if user_id not in user_check_mode or user_check_mode[user_id]["state"] != "start":
        return

    # Use the helper function to extract the episode number from the link
    episode_num = extract_episode_number(message.text)
    if episode_num:
        user_check_mode[user_id]["episodes"].append({"episode": episode_num, "link": message.text})
        user_check_mode[user_id]["state"] = "end"  # Now expect the last episode link
        await message.reply_text("Now, please provide the link of the last episode.")
    else:
        await message.reply_text("Could not find episode number in the link. Please try again with a valid episode link.")

# End the check process by asking for the last episode link
@Client.on_message(filters.command("endcheck") & filters.private)
async def end_check(client, message):
    user_id = message.from_user.id

    if user_id not in user_check_mode or user_check_mode[user_id]["state"] != "end":
        await message.reply_text("You need to use /startcheck first to start the check process.")
        return

    # Ask for the last episode link
    await message.reply_text("Please provide the link of the last episode.")

# Handle the link of the last episode and perform the check for missing episodes
@Client.on_message(filters.text & filters.private)
async def handle_end_check(client, message):
    user_id = message.from_user.id

    if user_id not in user_check_mode or user_check_mode[user_id]["state"] != "end":
        return

    # Use the helper function to extract the episode number from the last episode link
    last_episode = extract_episode_number(message.text)
    if last_episode:
        user_check_mode[user_id]["episodes"].append({"episode": last_episode, "link": message.text})

        # Sort the list of episodes and check for missing numbers
        episodes = sorted(user_check_mode[user_id]["episodes"], key=lambda x: x["episode"])
        missing_episodes = []
        
        # Collect missing episodes and send messages with links to previous episodes
        for i in range(episodes[0]["episode"], episodes[-1]["episode"]):
            if i not in [ep["episode"] for ep in episodes]:
                missing_episodes.append(i)

        # Generate the episode messages with buttons
        for ep in episodes:
            episode_num = ep["episode"]
            episode_link = ep["link"]
            prev_episode_link = None
            
            # Find the link to the previous episode if available
            prev_episode = next((ep["link"] for ep in episodes if ep["episode"] == episode_num - 1), None)
            if prev_episode:
                prev_episode_link = InlineKeyboardButton(
                    text=f"Episode {episode_num - 1}",
                    url=prev_episode
                )
            
            # Send the episode number and the button with the previous episode link
            keyboard = [[prev_episode_link]] if prev_episode_link else []
            await message.reply_text(
                f"Episode {episode_num}", 
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        if missing_episodes:
            missing_str = ", ".join(map(str, missing_episodes))
            await message.reply_text(f"Missing episodes: {missing_str}")
        else:
            await message.reply_text("No missing episodes. All episodes are accounted for.")

        # Reset the check process for the user
        user_check_mode[user_id]["state"] = "start"
        user_check_mode[user_id]["episodes"] = []
    else:
        await message.reply_text("Could not find episode number in the link. Please try again with a valid episode link.")
        
