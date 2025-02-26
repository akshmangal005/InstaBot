import os
from dotenv import load_dotenv
from instabot_sqs_lambda.lambda_function import *
from instabot_search_engine.lambda_function import *
from instabot_email_notifier.lambda_function import *

load_dotenv()
receiver_email = os.getenv('RECEIVER_EMAIL')

# List of songs
songs = []

def main():
    users_Dict = check_messages()
    for key, values in users_Dict.items():
        thread_id = values[0]
        if values:
            for i, url in enumerate(values[1:], start=1): 
                song_name = search_song(i, url)
                print(song_name)
                if(song_name == "Title not found"):
                    continue
                youtube_url = f"https://www.youtube.com/results?search_query={song_name}"
                youtube_music_url = f"https://music.youtube.com/search?q={song_name}"
                songs.append((song_name, youtube_url,youtube_music_url))

            if(os.getenv('Client1') == key):
                send_and_create_email(songs,os.getenv('Client1_email'))
                send_messages(songs,thread_id)
            elif(os.getenv('Client2') == key):
                # send_and_create_email(songs,os.getenv('Client2_email'))
                send_messages(songs,thread_id)
        else:
            print("No new messages to send")

main()