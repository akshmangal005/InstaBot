import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

instagram_username = os.getenv('USERNAME')
instagram_password = os.getenv('PASSWORD')

url_list = []

def check_messages():
    global url_list
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")
    
    print("Attempting Instagram login...")
    settings_file_path = '/tmp/dump.json'
    try:
        if os.path.exists(settings_file_path):
            print("sessionID exists.")
            cl = Client()
            cl.load_settings(settings_file_path)
            print("Login Successful")
        else:
            print("sessionID does not exist.")
            raise Exception
    except:
        print("Logging in using username and password")
        cl = Client()
        cl.login(instagram_username, instagram_password)
        cl.dump_settings(settings_file_path)
        print("Login Successful")

    try:
        print("Checking new messages...")
        threads = cl.direct_threads(20, "unread")

        if threads:
            my_chat = threads[0]
            # print(my_chat)
            thread_id = my_chat.id

            if hasattr(my_chat, 'messages'):
                for item in my_chat.messages:
                    if hasattr(item, 'clip') and hasattr(item.clip, 'video_url'):
                        url_list.append(item.clip.video_url)
                cl.direct_thread_hide(thread_id)  # Deletes the entire chat
                return url_list
            else:
                print("Message field not found in thread.")
                raise Exception
        else:
            print("No new messages.")
            raise Exception
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")
        return []