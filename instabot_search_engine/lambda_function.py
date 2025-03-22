import requests
import base64
import json
import http.client
import os
from pydub import AudioSegment
from dotenv import load_dotenv

load_dotenv()
api_host = os.getenv('API_HOST')
api_key = os.getenv('API_KEY')
content_type = os.getenv('TYPE')

def download_audio(url, output_file):
    try:
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        response = requests.get(url, stream=True)
        response.raise_for_status()  

        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)

        # print(f"Audio downloaded and saved as {output_file}")

    except requests.exceptions.RequestException as e:
        print(f"Failed to download the audio: {e}")

def trim_audio(input_file, output_file, start = 0, duration=5):
    try:
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        audio = AudioSegment.from_file(input_file)
        trimmed_audio = audio[start * 1000: (start + duration) * 1000] 
        trimmed_audio.export(output_file, format="mp3")

        # print(f"Audio trimmed to {duration} seconds and saved as {output_file}")

    except Exception as e:
        print(f"Error trimming audio: {e}")

def convert_to_mono(input_file, output_file):
    try:
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        audio = AudioSegment.from_file(input_file)
        mono_audio = audio.set_channels(1)
        mono_audio.export(output_file, format="raw")

        # print(f"Mono audio saved as {output_file}")

    except Exception as e:
        print(f"Error converting to mono: {e}")

def convert_mp3_to_base64(output_file):
    try:
        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file, "rb") as file:
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
    return parsed_data.get('track', 'Title not found').get('share', 'Title not found').get('subject', 'Title not found')

def search_song(id, audio_url):

    for retry in range(0, 15, 5):
        print(f'''Attempting {retry// 5 + 1} try for Searching Music.''')
        original_file = f"../../testing/tmp/{id}_original.mp3"
        trimmed_file = f"../../testing/tmp/{id}_trimmed.mp3"
        mono_file = f"../../testing/tmp/{id}_mono.raw"
        if(retry == 0):
            download_audio(audio_url, original_file)
        trim_audio(original_file, trimmed_file, retry)

        convert_to_mono(trimmed_file, mono_file)

        base64_string = convert_mp3_to_base64(mono_file)
        song_name = fetch_song(base64_string)
        if song_name == 'Title not found':
            continue
        else:
            break
    return song_name
    