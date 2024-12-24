import os
# import openai
# import requests
import io
import json
# import random
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client



instagram_username = os.getenv("INSTAGRAM_USERNAME")
instagram_password = os.getenv("INSTAGRAM_PASSWORD")

# Check if credentials are set
if not instagram_username or not instagram_password:
    raise ValueError("Username and password must be set in environment variables.")

# Initialize the client
print("Logging trying")
cl = Client()
cl.login(instagram_username, instagram_password)
print("Login Successful")


# thread = cl.direct_threads(10, selected_filter = "unread")[0]
# # thread = cl.direct_thread(thread_id = 340282366841710301244259531620826145935, amount= 20)[0]
# # cl.direct_thread_hide(thread_id = 340282366841710301244259531620826145935)
# # cl.direct_thread_mark_unread(thread_id = thread.id)
# print(thread)

# # print(thread)
# # print(len(thread))
# # for item in thread[0]:
# #     print(item)


# print("printing something")

# # Your URL
# # track_url = "https://www.instagram.com/reel/C-lFRL5yCz5/?igsh=ejdtNDI0eGR2ZHFj"

# # # Define the download folder (replace with your desired path)
# # download_folder = "C:\\Users\\Akash\\Downloads"


# # # Download the track
# # downloaded_path = cl.track_download_by_url(track_url, folder=download_folder)

# # print(f"Track downloaded to: {downloaded_path}")