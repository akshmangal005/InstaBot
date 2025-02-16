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
    cl = Client()
    cl.login(instagram_username, instagram_password)
    print("Login Successful")

    try:
        print("Checking new messages...")
        threads = cl.direct_threads(20, "unread")

        if threads:
            my_chat = threads[0]
            print(my_chat)
            thread_id = my_chat.id

            if hasattr(my_chat, 'messages'):
                for item in my_chat.messages:
                    if hasattr(item, 'clip') and hasattr(item.clip, 'video_url'):
                        url_list.append(item.clip.video_url)
                cl.direct_thread_hide(thread_id)  # Deletes the entire chat
            else:
                print("Message field not found in thread.")
        else:
            print("No new messages.")
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")