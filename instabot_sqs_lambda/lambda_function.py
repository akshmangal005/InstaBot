import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from dotenv import load_dotenv
from instabot_db.lambda_function import *

load_dotenv()

instagram_username = os.getenv('USERNAME')
instagram_password = os.getenv('PASSWORD')

cl = Client()
users_Dict = {}

def loginId():
    print("Attempting Instagram login...")
    try:
        print("Logging in using session id.")
        session_id = get_sessionid()
        if session_id == None:
            print("No sessions id found.")
            raise Exception
        cl.login_by_sessionid(session_id)
        print("Login Successful using session id.")
    except:
        print("Logging in using username and password")
        cl.login(instagram_username, instagram_password)
        session_id = cl.get_settings()
        create_db()
        post_sessionid(session_id['authorization_data']['sessionid'])
        print("Login Successful using username and password")

def send_messages(songs_list, thread_id):
    for song in songs_list:
        song_url = song[1].replace(" ", "_") #replacing spaces as url is getting break in message
        cl.direct_answer(thread_id, song_url)
    cl.direct_thread_hide(thread_id) # Deletes the entire chat
    print("Direct Message send successfully!")
    return

def check_messages():
    global users_Dict
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")
    
    loginId()

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