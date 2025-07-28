import os
import json
import requests
import base64
import subprocess
import boto3

# --- Environment Variables ---
API_HOST=os.getenv("api_host")
API_KEY=os.getenv("api_key")
CONTENT_TYPE=os.getenv("content_type")
EMAIL_LAMBDA_NAME = os.getenv("email_lambda_name")

def download_direct_audio(url, output_file):
    """
    Downloads audio from a direct URL to the specified output file.
    """
    print(f"Downloading audio from direct URL: {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"Audio successfully downloaded to {output_file}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download audio file: {e}")
        raise

def process_audio_with_subprocess(input_file, output_file, start_time_ms, duration_ms=5000):
    """
    Trims and converts an audio file to mono raw PCM using a direct ffmpeg subprocess call.
    """
    start_seconds = start_time_ms / 1000
    duration_seconds = duration_ms / 1000

    command = [
        'ffmpeg',
        '-i', input_file,
        '-ss', str(start_seconds),
        '-t', str(duration_seconds),
        '-ac', '1',
        '-f', 's16le',
        '-ar', '44100',
        '-y',
        output_file
    ]
    
    # print(f"Running command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        # print("ffmpeg stderr:", result.stderr)
    except FileNotFoundError:
        print("ERROR: 'ffmpeg' command not found. Ensure the FFmpeg Lambda Layer is attached.")
        raise
    except subprocess.CalledProcessError as e:
        # print(f"ffmpeg failed with exit code {e.returncode}")
        # print("ffmpeg stderr:", e.stderr)
        raise

def file_to_base64(file_path):
    """Converts a file to a Base64 encoded string."""
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")

def fetch_song(base64_string):
    """
    CORRECTED: Sends audio data to the v3 detection API with required parameters.
    """
    # Use the correct v3 endpoint
    url = f"https://{API_HOST}/songs/v2/detect" 
    
    # Add the required query string parameters
    # querystring = {"timezone":"America/Chicago", "locale":"en-US"}
    # print(f"Querystring: {querystring}")
    # print(f"API Host: {API_HOST}")
    # print(f"API Key: {API_KEY}")
    # print(f"Content Type: {CONTENT_TYPE}")
    # print(f"Base64 String Length: {(base64_string)}")
    headers = {
        'x-rapidapi-key': API_KEY,
        'x-rapidapi-host': API_HOST,
        'Content-Type': "text/plain" 
    }
    
    # Make the request with the data and the new querystring parameters
    response = requests.post(url, data=base64_string, headers=headers)
    
    response.raise_for_status()
    data = response.json()
    
    # The response structure for v3 might be different, adjust parsing if needed.
    # This is based on the previous structure.
    return data.get('track', {}).get('share', {}).get('subject', 'Title not found')

def invoke_email_lambda(thread_id, user_name, songs):
    """
    Invokes another Lambda function asynchronously to send an email.
    """
    if not EMAIL_LAMBDA_NAME:
        print("ERROR: EMAIL_LAMBDA_NAME environment variable not set. Skipping invocation.")
        return

    lambda_client = boto3.client('lambda')
    
    # Construct the payload for the email Lambda
    # Note: We map 'user_name' to 'receiver_email' to match the other Lambda's expected input
    payload = {
        "thread_id": thread_id,
        "user_name": user_name,
        "songs": songs
    }

    print(f"Invoking email Lambda '{EMAIL_LAMBDA_NAME}' for thread '{thread_id}'...")
    try:
        lambda_client.invoke(
            FunctionName=EMAIL_LAMBDA_NAME,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        print("Successfully invoked email Lambda.")
    except Exception as e:
        print(f"ERROR: Failed to invoke email Lambda: {e}")
        # Depending on requirements, you might want to raise the exception
        # to have the SQS message retried.
        raise

def lambda_handler(event, context):
    """
    This Lambda function is triggered by an SQS queue, processes audio files,
    identifies songs, and invokes another Lambda to send the results.
    """
    for record in event['Records']:
        try:
            message_body = json.loads(record['body'])
            thread_id = message_body.get('thread_id')
            username = message_body.get('user_name') # This will be the recipient email
            audio_urls = message_body.get('audio_urls', [])
            
            if not thread_id or not username or not audio_urls:
                print(f"Skipping message due to missing data: {record['messageId']}")
                continue

            songs_found = []
            for i, audio_url in enumerate(audio_urls):
                if not audio_url:
                    continue
                
                # Use a unique identifier for temporary files
                file_identifier = f"{username}_{i}"
                original_file_path = f"/tmp/{file_identifier}_input.mp3"
                mono_file_path = f"/tmp/{file_identifier}_mono.raw"
                song_name = 'Title not found'
                try:
                    download_direct_audio(audio_url, original_file_path)
                    
                    # Attempt to recognize the song at different start times
                    for attempt in range(3):
                        start_ms = attempt * 5000
                        print(f"Attempt {attempt + 1}: trying to detect song for {file_identifier} starting at {start_ms // 1000}s.")
                        
                        process_audio_with_subprocess(original_file_path, mono_file_path, start_ms)
                        base64_string = file_to_base64(mono_file_path)
                        song_name = fetch_song(base64_string)
                        
                        if song_name != 'Title not found':
                            break
                            
                    if song_name != 'Title not found':
                        youtube_link = f"https://www.youtube.com/results?search_query={song_name}"
                        youtube_music_link = f"https://music.youtube.com/search?q={song_name}"
                        print(f"Result: {song_name}")
                        songs_found.append((song_name, youtube_link, youtube_music_link))
                finally:
                    # Clean up temporary files
                    for file_path in [original_file_path, mono_file_path]:
                        if os.path.exists(file_path):
                            os.remove(file_path)

            if songs_found:
                invoke_email_lambda(thread_id, username, songs_found)

        except Exception as e:
            print(f"ERROR processing message {record.get('messageId', 'N/A')}: {e}")
            raise e
            
    return {
        'statusCode': 200,
        'body': json.dumps('Successfully processed batch.')
    }