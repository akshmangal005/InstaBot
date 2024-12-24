import os
import io
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client



instagram_username = os.getenv("INSTAGRAM_USERNAME")
instagram_password = os.getenv("INSTAGRAM_PASSWORD")

# Check if credentials are set
if not instagram_username or not instagram_password:
    raise ValueError("Username and password must be set in environment variables.")

print("Login trying")
cl = Client()
cl.login(instagram_username, instagram_password)
print("Login Successful")

li = []
try:
    print("Checking new messages")
    thread = cl.direct_threads(20, "unread")
    if(len(thread) > 0):
        my_chat = thread[0]
        thread_id = my_chat.id
        if hasattr(my_chat, 'messages'):
            for item in my_chat.messages:
                li.append(item.clip.video_url)
        else:
            print("Message field not found")
        cl.direct_thread_hide(thread_id) #delete the entire chat
    else:
        print("No new messages")
except:
    print("Error occured while checking new messages")
