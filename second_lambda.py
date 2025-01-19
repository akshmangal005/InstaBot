import requests
import base64
import http
import json
from pydub import AudioSegment

def download_audio(url, output_file):
    try:
        # Send a GET request to the URL
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Check for HTTP request errors

        # Open a local file with write-binary mode
        with open(output_file, 'wb') as file:
            # Write the content to the file in chunks
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:  # Filter out keep-alive chunks
                    file.write(chunk)

        print(f"Audio downloaded successfully as {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the audio: {e}")

def trim_audio(input_file, output_file, duration=5):
    try:
        # Load the audio file
        audio = AudioSegment.from_file(input_file)

        # Trim to the first 'duration' seconds
        trimmed_audio = audio[:duration * 1000]  # Convert seconds to milliseconds

        # Export the trimmed audio
        trimmed_audio.export(output_file, format="mp3")
        print(f"Audio trimmed to {duration} seconds and saved as {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

def convert_to_mono(input_path: str, output_path: str):
    try:
        # Load the MP3 file
        audio = AudioSegment.from_file(input_path)

        # Convert to mono
        mono_audio = audio.set_channels(1)

        # Export the mono audio file
        mono_audio.export(output_path, format="raw")
        print(f"Converted file saved at: {output_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

def convert_mp3_to_base64(input_path: str) -> str:
    try:
        # Read the MP3 file in binary mode
        with open(input_path, "rb") as mp3_file:
            binary_data = mp3_file.read()

        # Encode the binary data to a Base64 string
        base64_data = base64.b64encode(binary_data).decode("utf-8")
        return base64_data
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""

def fetch_song(base64_string):
    conn = http.client.HTTPSConnection("API_HOST")
    headers = {
        'x-rapidapi-key': "API_KEY",
        'x-rapidapi-host': "API_HOST",
        'Content-Type': "TYPE"
    }

    conn.request("POST", "/songs/v2/detect", base64_string, headers)

    res = conn.getresponse()
    data = res.read()
    parsed_data = json.loads(data.decode('utf-8'))
    title = parsed_data.get('track', {}).get('title', 'Title not found')

    print(title)

def lambda_handler(event, context):
    print("Received Event:", event)
    message = json.loads(event['Records'][0]['body'])
    id = message['id']
    item = message['link']

    download_audio(item, f'''../testing/{id}_output.mp3''')
    
    trim_audio(f'''../testing/{id}_output.mp3''', f'''../testing/{id}_trimmed.mp3''')
    
    convert_to_mono(f'''../testing/{id}_trimmed.mp3''',f'''../testing/{id}_mono.raw''')
    
    base64_string = convert_mp3_to_base64(f'''../testing/{id}_mono.raw''')
    
    with open("../testing/b64.txt", "w") as file: # remove after completing 
        file.write(base64_string) # remove after completing

    
    song_name = fetch_song(base64_string)
    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }