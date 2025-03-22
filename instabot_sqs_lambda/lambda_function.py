import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from dotenv import load_dotenv
from instabot_db.lambda_function import *

load_dotenv()

instagram_username = os.getenv('USERNAME')
instagram_password = os.getenv('PASSWORD')

users_Dict = {}

def send_messages(songs_list, thread_id,cl):
    for song in songs_list:
        song_url = song[1].replace(" ", "_") #replacing spaces as url is getting break in message
        cl.direct_answer(thread_id, song_url)
    cl.direct_thread_hide(thread_id) # Deletes the entire chat
    print("Direct Message send successfully!")
    return
def check_messages(cl):
    global users_Dict
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")

    try:
        print("Checking new messages...")
        threads = cl.direct_threads(20, "unread")

        if threads:
            for thread in threads:
                url_list = []
                my_chat = thread
                thread_id = my_chat.id
                url_list.append(thread_id)
                user_name = my_chat.users[0].username
                if hasattr(my_chat, 'messages'):
                    for item in my_chat.messages:
                        if hasattr(item, 'clip') and hasattr(item.clip, 'video_url'):
                            url_list.append(item.clip.video_url)
                    cl.direct_thread_hide(thread_id)  # Deletes the entire chat
                    users_Dict[user_name] = url_list
                else:
                    print(f'''Message field not found in {user_name}.''')
            return users_Dict
        else:
            print("No new messages.")
            return users_Dict
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")
        return {}