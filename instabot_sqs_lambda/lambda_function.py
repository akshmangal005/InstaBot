import os
import json
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from dotenv import load_dotenv
import subprocess

load_dotenv()

instagram_username = os.getenv('USERNAME')
instagram_password = os.getenv('PASSWORD')

url_list = []

cl = Client()
def writing():
    subprocess.Popen('echo "Geeks 4 Geeks" > session.txt ', shell=True)
    subprocess.Popen('pwd', shell=True)
    # result = subprocess.run(['pwd'], capture_output=True, text=True, check_returncode=True)
    # print(result.stdout.strip())    

def check_messages():
    global url_list
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")
    
    print("Attempting Instagram login...")
    filename = "session.txt"
    try:
        if os.path.exists(filename):
            print("sessionID exists.")
            
            with open(filename, "r") as file:
                session_id = file.read()
            print("printing session id", session_id)
            cl.login_by_sessionid(session_id)
            print("Login Successful")
        else:
            print("sessionID does not exist.")
            raise Exception
    except:
        print("Logging in using username and password")
        cl.login(instagram_username,instagram_password)
        data = cl.get_settings()
        print(data)
        session_id = data["authorization_data"]["sessionid"]
        print(session_id)
        writing()
        with open(filename, "w") as file:
            file.write(session_id)
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
                return []
        else:
            print("No new messages.")
            return []
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")
        return []

check_messages()