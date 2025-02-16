import requests
import base64
import json
import http.client
import os
import pandas as pd
import botocore
from botocore.exceptions import ClientError
from pydub import AudioSegment
from botocore.config import Config

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)

api_host = os.environ['API_HOST']
api_key = os.environ['API_KEY']
content_type = os.environ['TYPE']

def download_audio(url, output_file):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  

        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

        print(f"Audio downloaded and saved as {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the audio: {e}")

def trim_audio(input_file, output_file, duration=5):
    try:
        audio = AudioSegment.from_file(input_file)
        trimmed_audio = audio[:duration * 1000] 
        trimmed_audio.export(output_file, format="mp3")

        print(f"Audio trimmed to {duration} seconds and saved as {output_file}")

    except Exception as e:
        print(f"Error trimming audio: {e}")

def convert_to_mono(input_file, output_file):
    try:
        audio = AudioSegment.from_file(input_file)
        mono_audio = audio.set_channels(1)
        mono_audio.export(output_file, format="raw")

        print(f"Mono audio saved as {output_file}")

    except Exception as e:
        print(f"Error converting to mono: {e}")

def convert_mp3_to_base64(input_file):
    try:
        with open(input_file, "rb") as file:
            binary_data = file.read()
        return base64.b64encode(binary_data).decode("utf-8")

    except Exception as e:
        print(f"Error converting to Base64: {e}")
        return ""

def fetch_song(base64_string):
    conn = http.client.HTTPSConnection(api_host)
    headers = {
        'x-rapidapi-key': api_key,
        'x-rapidapi-host': api_host,
        'Content-Type': content_type
    }

    conn.request("POST", "/songs/v2/detect", base64_string, headers)
    res = conn.getresponse()
    data = res.read()
    
    parsed_data = json.loads(data.decode('utf-8'))
    return parsed_data.get('track', {}).get('title', 'Title not found')


def add_song_to_excel(song_name, filename="songs.xlsx"):
    # Create a DataFrame for the new song
    new_data = pd.DataFrame({"gaana": [song_name]})

    # Check if file exists
    if os.path.exists(filename):
        existing_data = pd.read_excel(filename)  # Read existing data
        df = pd.concat([existing_data, new_data], ignore_index=True)  # Append new song
    else:
        df = new_data  # Create new file with only this song

    # Save back to Excel
    df.to_excel(filename, index=False)
    print(f"Song '{song_name}' added to '{filename}' successfully!")

def run_loop(id, audio_url):
    original_file = f"../../testing/tmp/{id}_original.mp3"
    trimmed_file = f"../../testing/tmp/{id}_trimmed.mp3"
    mono_file = f"../../testing/tmp/{id}_mono.raw"
    download_audio(audio_url, original_file)
    trim_audio(original_file, trimmed_file)

    convert_to_mono(trimmed_file, mono_file)

    base64_string = convert_mp3_to_base64(mono_file)

    song_name = fetch_song(base64_string)
    print(f"Detected Song: {song_name}")
    add_song_to_excel(song_name)



def read_urls_row_by_row(filepath):
    """
    Reads the 'URL List' column from an Excel file and processes each row one by one.
    
    :param filepath: Full path to the Excel file.
    """
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            print(f"Error: File '{filepath}' not found!")
            return

        # Read the Excel file
        df = pd.read_excel(filepath)

        # Debugging: Print column names to check if 'URL List' exists
        print("Columns in Excel:", df.columns.tolist())

        # Check if 'URL List' column exists
        if "urls" not in df.columns:
            print("Error: 'URL List' column not found! Check the column name in Excel.")
            return

        count = 0
        # Loop through each row one by one
        for index, row in df.iterrows():
            url = row["urls"]  # Extract URL from current row
            print(url)
            count = count + 1
            run_loop(1, url)  # Call function to process URL

    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found!")
    except Exception as e:
        print(f"An error occurred: {e}")


file_path = f"C:/Users/Akash/OneDrive/Desktop/InstaBot/instabot_sqs_lambda/url_list.xlsx"  # Change this to your file path
# file_path =  f"../instabot-sqs-lambda/url_list.xlsx"
df = read_urls_row_by_row(file_path)
print("Completed")
# def lambda_handler(event, context):
#     print("Received Event:", event)

#     message = json.loads(event['Records'][0]['body'])
#     url_list = message['url_list']

#     id = url_list['id']
#     audio_url = url_list['url']

#     original_file = f"/tmp/{id}_original.mp3"
#     trimmed_file = f"/tmp/{id}_trimmed.mp3"
#     mono_file = f"/tmp/{id}_mono.raw"

#     download_audio(audio_url, original_file)

#     trim_audio(original_file, trimmed_file)

#     convert_to_mono(trimmed_file, mono_file)

#     base64_string = convert_mp3_to_base64(mono_file)

#     song_name = fetch_song(base64_string)
#     print(f"Detected Song: {song_name}")

#     return {
#         'statusCode': 200,
#         'body': json.dumps({'Detected Song': song_name})
#     }
