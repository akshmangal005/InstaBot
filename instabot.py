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
    # url_list = ["https://instagram.fblr23-1.fna.fbcdn.net/o1/v/t16/f2/m86/AQPeu5y3VoiQgCo6TuggmNBA77WVoBMliRJ5WWElHWqNCqwnmC8cDwL9Cp_6nVtSogSIPzPx8vTGMkr7iSiZgJedJ7JI5-vhoPMAp9Q.mp4?efg=eyJ4cHZfYXNzZXRfaWQiOjU0NjA0MzE5ODQ5MTQ1MiwidmVuY29kZV90YWciOiJ4cHZfcHJvZ3Jlc3NpdmUuSU5TVEFHUkFNLkNMSVBTLkMzLjcyMC5kYXNoX2Jhc2VsaW5lXzFfdjEifQ&_nc_ht=instagram.fblr23-1.fna.fbcdn.net&_nc_cat=106&vs=43ef438e6e605fda&_nc_vs=HBksFQIYUmlnX3hwdl9yZWVsc19wZXJtYW5lbnRfc3JfcHJvZC8yNzREOUVFOUREQUQzNTc0OUI4RjUzQkRBNzdFNEFCNV92aWRlb19kYXNoaW5pdC5tcDQVAALIAQAVAhg6cGFzc3Rocm91Z2hfZXZlcnN0b3JlL0dNMV9lUnl0ekc2bndlMEZBSkE2ZWNHLVI1SXRicV9FQUFBRhUCAsgBACgAGAAbAogHdXNlX29pbAExEnByb2dyZXNzaXZlX3JlY2lwZQExFQAAJvishu7yp_gBFQIoAkMzLBdAF_752yLQ5RgSZGFzaF9iYXNlbGluZV8xX3YxEQB1_gcA&ccb=9-4&oh=00_AYDPWnHDqkHN6bK7NlBlhpbZQRgw-TOOlKirZ-d07ecnaA&oe=67B41486&_nc_sid=1d576d"]
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


main()