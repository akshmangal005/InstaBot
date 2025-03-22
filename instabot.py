import os
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from dotenv import load_dotenv
from instabot_sqs_lambda.lambda_function import *
from instabot_search_engine.lambda_function import *
from instabot_email_notifier.lambda_function import *

load_dotenv()
receiver_email = os.getenv('RECEIVER_EMAIL')
instagram_username = os.getenv('USERNAME')
instagram_password = os.getenv('PASSWORD')

def loginId():
    cl = Client()
    print("Attempting Instagram login...")
    try:
        print("Logging in using session id.")
        session_id = get_sessionid()
        if session_id == None:
            print("No sessions id found.")
            raise Exception
        cl.login_by_sessionid(session_id)
        print("Login Successful using session id.")
        return cl
    except Exception as e:
        print("Logging in using username and password ")
        cl.login(instagram_username, instagram_password, True)
        session_id = cl.get_settings()
        create_db()
        post_sessionid(session_id['authorization_data']['sessionid'])
        print("Login Successful using username and password")
        return cl

def main():
    cl = loginId()
    users_Dict = check_messages(cl)
    for key, values in users_Dict.items():
        thread_id = values[0]
        songs = [] # List of songs
        if values:
            for i, url in enumerate(values[1:], start=1): 
                song_name = search_song(i, url)
                print(song_name)
                if(song_name == "Title not found"):
                    continue
                youtube_url = f"https://www.youtube.com/results?search_query={song_name}"
                youtube_music_url = f"https://music.youtube.com/search?q={song_name}"
                songs.append((song_name, youtube_url,youtube_music_url))

            if songs:
                if(os.getenv('CLIENT1') == key):
                    send_and_create_email(songs,os.getenv('CLIENT1_EMAIL'))
                    send_messages(songs,thread_id, cl)
                else:
                    send_messages(songs,thread_id, cl)
            else:
                print("No new messages to send")
        else:
            print("No New Messages Received!")

main()
