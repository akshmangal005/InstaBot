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
    url_list = check_messages()
    if url_list:
        for i, url in enumerate(url_list):
            song_name = search_song(i, url)
            print(song_name)
            if(song_name == "Title not found"):
                continue
            youtube_url = f"https://www.youtube.com/results?search_query={song_name}"
            youtube_music_url = f"https://music.youtube.com/search?q={song_name}"
            songs.append((song_name, youtube_url,youtube_music_url))

        send_and_create_email(songs,receiver_email)
    else:
        print("Mail Not Send Due to no new messages")

main()