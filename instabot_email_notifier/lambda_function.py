import smtplib
import json
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import ClientError as InstagrapiClientError
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import random
import time

S3_BUCKET_NAME = os.getenv("bucket_name")
SESSION_FILE_KEY = "instagram_session.json" 
instagram_username = os.getenv('instagram_username')
instagram_password = os.getenv('instagram_password')

AWS_REGION = 'us-west-2'
s3_client = boto3.client('s3',region_name=AWS_REGION)

def get_session_from_s3(bucket: str, key: str) -> dict | None:
    """
    Downloads the session file from S3, parses it, and returns a dictionary.
    """
    print(f"Attempting to load session from s3://{bucket}/{key}")
    try:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        session_json = response['Body'].read().decode('utf-8')
        # Parse the JSON string into a Python dictionary
        return json.loads(session_json)
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print("Session file not found in S3.")
        else:
            print(f"An S3 error occurred: {e}")
        return None
    except json.JSONDecodeError:
        print("Error decoding JSON from the session file.")
        return None


def put_session_to_s3(settings_dict: dict, bucket: str, key: str):
    """
    Uploads the session dictionary to an S3 object as a JSON string.
    """
    print(f"Saving new session to s3://{bucket}/{key}")
    try:
        # Convert the dictionary to a JSON string for storing
        session_json = json.dumps(settings_dict, indent=4)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=session_json,
            ContentType='application/json'
        )
        print("Session successfully saved to S3.")
    except Exception as e:
        print(f"Failed to save session to S3: {e}")


def login_with_s3_session() -> Client:
    """
    Handles Instagram login using a session stored in S3.
    """
    cl = Client()

    try:
        # 1. Attempt to get session dictionary from S3
        settings = get_session_from_s3(S3_BUCKET_NAME, SESSION_FILE_KEY)
        if not settings:
            raise ValueError("No session found in S3.")

        # 2. Load the session from the dictionary
        cl.set_settings(settings)
        print("Session settings loaded from S3. Verifying...")

        # 3. Verify the session is still active
        cl.account_info()
        print("✅ Login successful using S3 session.")

    except Exception as e:
        print(f"Could not use S3 session ({e}). Logging in with credentials.")

        # 4. If S3 session fails, log in normally
        cl.login(instagram_username, instagram_password)
        print("✅ Login successful with credentials.")

        # 5. Get new session dictionary and save it to S3
        new_settings = cl.get_settings()
        put_session_to_s3(new_settings, S3_BUCKET_NAME, SESSION_FILE_KEY)

    return cl

def retry_with_exponential_backoff(func, max_retries=5, base_delay=1, max_delay=60):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        Result of the function call
    """
    for attempt in range(max_retries):
        try:
            return func()
        except (InstagrapiClientError, ConnectionError, Exception) as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit or server error that we should retry
            if any(keyword in error_msg for keyword in ['500', 'rate limit', 'too many', 'connection', 'timeout', 'server error']):
                if attempt < max_retries - 1:
                    # Calculate delay with exponential backoff and jitter
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    print(f"Instagram API error (attempt {attempt + 1}/{max_retries}): {e}")
                    print(f"Retrying in {delay:.2f} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"Max retries ({max_retries}) exceeded. Last error: {e}")
                    raise
            else:
                # For non-retryable errors, raise immediately
                print(f"Non-retryable Instagram API error: {e}")
                raise
    
    raise Exception(f"Function failed after {max_retries} attempts")

def send_messages_to_instagram(songs_list, thread_id):
    cl = login_with_s3_session()
    
    # Send each song with retry logic
    for i, song in enumerate(songs_list):
        song_url = song[1].replace(" ", "_")  # replacing spaces as url is getting break in message
        
        def _send_message():
            return cl.direct_answer(thread_id, song_url)
        
        try:
            retry_with_exponential_backoff(_send_message, max_retries=3, base_delay=1)
            print(f"Successfully sent song {i+1}/{len(songs_list)}: {song[0]}")
        except Exception as e:
            print(f"Failed to send song {i+1}/{len(songs_list)} ({song[0]}): {e}")
            # Continue with other songs even if one fails
    
    # Hide thread with retry logic
    def _hide_thread():
        return cl.direct_thread_hide(thread_id)
    
    try:
        retry_with_exponential_backoff(_hide_thread, max_retries=2, base_delay=1)
        print("Successfully hid thread")
    except Exception as e:
        print(f"Warning: Failed to hide thread: {e}")
        # Don't fail the entire function if hiding fails
    
    print("Direct Message sending process completed!")
    return

def lambda_handler(event, context):
    """
    Lambda handler to build and send an email with a list of songs.
    Reads credentials from environment variables and input from the event payload.
    """
    # 1. Get credentials securely from environment variables 🔒
    try:
        sender_email = os.environ['sender_email']
        sender_password = os.environ['sender_password']
    except KeyError as e:
        print(f"ERROR: Environment variable not set: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f"Configuration error: Missing environment variable {e}")
        }

    # 2. Get input from the event payload ✨
    try:
        # These values are now correctly read from the event dictionary
        songs = event['songs']
        thread_id = event['thread_id']
        user_name = event['user_name']
        receiver_email = os.getenv('receiver_email')
        send_messages_to_instagram(songs, thread_id)
    except KeyError as e:
        print(f"Missing required key in event: {e}")
        return {
            'statusCode': 400,
            'body': json.dumps(f"Bad Request: Missing key {e}")
        }

    # 3. Build the HTML email body
    email_body = """
    <html><head><style>
    table {border-collapse: collapse; width: 100%;}
    th, td {border: 1px solid black; padding: 8px; text-align: left;}
    th {background-color: #f2f2f2;}
    a {text-decoration: none; color: blue;}
    </style></head><body>
    <p>Hello,</p>
    <p>Given below is the list of songs you shared with Track Hunter.</p>
    <table>
        <tr>
            <th>Song Name</th><th>YouTube Link</th><th>YouTube Music Link</th>
        </tr>
    """
    for song in songs:
        song_name = song[0]
        youtube_link = song[1]
        youtube_music_link = song[2]
        email_body += f"""
        <tr>
            <td>{song_name}</td>
            <td><a href="{youtube_link}" target="_blank">YouTube</a></td>
            <td><a href="{youtube_music_link}" target="_blank">YouTube Music</a></td>
        </tr>
        """
    email_body += "</table><p>Best regards,<br>Track Hunter</p></body></html>"

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = receiver_email
        msg["Subject"] = "List of Songs from Track Hunter"
        msg.attach(MIMEText(email_body, "html"))

        # Connect to Gmail SMTP and send
        print(f"Sending email from {sender_email} to {receiver_email}")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        
        print("Email sent successfully!")
        return {
            'statusCode': 200,
            'body': json.dumps('Email sent successfully!')
        }
    except Exception as e:
        print(f"Failed to send email: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }