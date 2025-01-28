import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client

instagram_username = os.getenv("INSTAGRAM_USERNAME")
instagram_password = os.getenv("INSTAGRAM_PASSWORD")

url_list = []
def check_messages():
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")
    
    print("Login trying")
    cl = Client()
    cl.login(instagram_username, instagram_password)
    print("Login Successful")

    try:
        print("Checking new messages")
        thread = cl.direct_threads(20, "unread")
        if(len(thread) > 0):
            my_chat = thread[0]
            thread_id = my_chat.id
            if hasattr(my_chat, 'messages'):
                for item in my_chat.messages:
                    url_list.append(item.clip.video_url)
                cl.direct_thread_hide(thread_id)      #delete the entire chat
            else:
                print("Message field not found")
        else:
            print("No new messages")
    except:
        print("Error occured while checking new messages")


def lambda_handler(event, context):
    check_messages()
    