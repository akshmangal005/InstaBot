import os
import json
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from instagrapi import Client
import time
import uuid
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pydantic import HttpUrl

# --- Environment Variables ---
instagram_username = os.getenv('username')
instagram_password = os.getenv('password')
TABLE_NAME = os.getenv('session_table_name')
SQS_QUEUE_URL = os.getenv('SQS_QUEUE_URL')
S3_BUCKET_NAME = os.getenv('Bucket_name')
SESSION_FILE_KEY = "instagram_session.json" 

users_Dict = {}
AWS_REGION = 'us-west-2'
dynamodb = boto3.client('dynamodb',region_name=AWS_REGION)
sqs = boto3.client('sqs', region_name=AWS_REGION)
s3_client = boto3.client('s3',region_name=AWS_REGION)

# def get_latest_sessionId_from_table(table_name: str) -> str | None:
#     """
#     Scans the entire DynamoDB table to find the SessionId associated with the
#     latest 'created_at' timestamp.

#     WARNING: This operation can be very inefficient and expensive for large tables.
#     Consider using a Global Secondary Index (GSI) for better performance.
#     """
#     print(f"Scanning table '{table_name}' to find the latest SessionId...")
#     latest_SessionId = None
#     latest_created_at = None # Will store datetime objects for comparison

#     try:
#         # Initial scan
#         response = dynamodb.scan(
#             TableName=table_name,
#             ProjectionExpression="SessionId, created_at" # Only fetch necessary attributes
#         )

#         while True:
#             items = response.get('Items', [])
#             for item in items:
#                 # DynamoDB returns items with type descriptors (e.g., {'S': 'value'})
#                 current_SessionId = item.get('SessionId', {}).get('S')
#                 current_created_at_str = item.get('created_at', {}).get('S')

#                 if current_SessionId and current_created_at_str:
#                     try:
#                         # Parse the timestamp string to a datetime object for comparison
#                         # Assuming ISO 8601 format: 'YYYY-MM-DDTHH:MM:SSZ' or 'YYYY-MM-DDTHH:MM:SS.ffffffZ'
#                         # We need to handle potential microseconds if they exist, or just seconds.
#                         # Let's try parsing with microseconds first, then without.
#                         try:
#                             current_dt = datetime.strptime(current_created_at_str, "%Y-%m-%dT%H:%M:%SZ")
#                         except ValueError:
#                             current_dt = datetime.strptime(current_created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ")


#                         if latest_created_at is None or current_dt > latest_created_at:
#                             latest_created_at = current_dt
#                             latest_SessionId = current_SessionId
#                     except ValueError:
#                         print(f"Warning: Could not parse created_at timestamp: {current_created_at_str}")
#                         continue # Skip this item if timestamp is invalid

#             # Check if there are more items to scan (pagination)
#             last_evaluated_key = response.get('LastEvaluatedKey')
#             if last_evaluated_key:
#                 print("Continuing scan with LastEvaluatedKey...")
#                 response = dynamodb.scan(
#                     TableName=table_name,
#                     ProjectionExpression="SessionId, created_at",
#                     ExclusiveStartKey=last_evaluated_key
#                 )
#             else:
#                 break # No more items to scan

#         if latest_SessionId:
#             print(f"\nSuccessfully found the latest SessionId: {latest_SessionId}")
#             print(f"Associated created_at: {latest_created_at.isoformat()}Z")
#         else:
#             print("\nNo items found or no valid created_at timestamps in the table.")

#         return latest_SessionId

#     except ClientError as e:
#         print(f"Error scanning table: {e.response['Error']['Message']}")
#         return None
#     except Exception as e:
#         print(f"An unexpected error occurred: {e}")
#         return None

# def put_session_data(SessionId: str) -> bool:
#     """
#     Inserts a new session item into the DynamoDB table.
#     Automatically generates a unique 'id' and the current 'created_at' timestamp.

#     Args:
#         SessionId (str): The session ID.

#     Returns:
#         bool: True if the item was successfully put, False otherwise.
#     """
#     # Generate a unique ID for the item (e.g., using UUID)
#     item_id = str(uuid.uuid4())
#     # Generate the current UTC timestamp in ISO 8601 format
#     created_at = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

#     print(f"\nAttempting to put session data: SessionId={SessionId}, id={item_id}, created_at={created_at}")
#     try:
#         response = dynamodb.put_item(
#             TableName=TABLE_NAME,
#             Item={
#                 'SessionId': {'S': SessionId},
#                 'id': {'S': item_id},
#                 'created_at': {'S': created_at}
#             }
#         )
#         # Check for successful put operation (no error raised)
#         if response['ResponseMetadata']['HTTPStatusCode'] == 200:
#             print("Successfully put item into DynamoDB.")
#             return True
#         else:
#             print(f"Failed to put item. Response: {response}")
#             return False
#     except ClientError as e:
#         print(f"Error putting item: {e.response['Error']['Message']}")
#         return False
#     except Exception as e:
#         print(f"An unexpected error occurred while putting item: {e}")
#         return False

def check_messages(cl):
    """
    Retrieves unread direct message threads from an Instagram account,
    extracts video URLs from messages within those threads, and hides the threads.

    Args:
        cl: An authenticated Instagram client object.

    Returns:
        dict: A dictionary mapping usernames to lists containing their thread ID
            (as the first element) and extracted video URLs. Returns an empty
            dictionary if no new messages are found or an error occurs.
    """
    global users_Dict
    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")

    try:
        print("Checking new messages...")
        threads = cl.direct_threads(20, "unread")

        if threads:
            for thread in threads:
                url_list = []
                my_chat = thread
                thread_id = my_chat.id
                url_list.append(thread_id)
                user_name = my_chat.users[0].username
                if hasattr(my_chat, 'messages'):
                    for item in my_chat.messages:
                        if hasattr(item, 'clip') and hasattr(item.clip, 'video_url'):
                            url_list.append(item.clip.video_url)
                        else:
                            continue
                    cl.direct_thread_hide(thread_id)  # Deletes the entire chat
                    users_Dict[user_name] = url_list
                else:
                    print(f'''Message field not found in {user_name}.''')
            return users_Dict
        else:
            print("No new messages.")
            return users_Dict
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")
        return {}

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


# def loginId():
#     """
#     Handles Instagram login.
#     In a real-world scenario, session data should be stored persistently (e.g., in DynamoDB or S3).
#     """
#     cl = Client()
#     print("Attempting Instagram login...")
#     try:
#         # --- Placeholder for session-based login ---
#         SessionId = get_latest_sessionId_from_table(TABLE_NAME)
#         if SessionId is None:
#             print("No valid session id found. A new login is required.")
#             raise Exception("No session ID available")
        
#         print("Logging in using session id.")
#         cl.login_by_sessionid(SessionId)
#         print("Login Successful using session id.")
#         return cl

#     except Exception as e:
#         print(f"Session login failed ({e}). Logging in with username and password.")
#         cl.login(instagram_username, instagram_password, True)
#         session_data = cl.get_settings()
#         SessionId = session_data['authorization_data']['sessionid']
        
#         # --- Placeholder for storing the new session ---
#         put_session_data(SessionId)
        
#         print(f"Login Successful using username and password. New session ID: {SessionId}")
#         return cl

def send_data_to_sqs(data_to_send: dict, queue_url: str) -> bool:
    """
    Sends a dictionary of data as a JSON string message to an SQS queue.

    Args:
        data_to_send (dict): The Python dictionary to send.
        queue_url (str): The URL of the SQS queue.

    Returns:
        bool: True if the message was sent successfully, False otherwise.
    """
    try:
        # Convert the dictionary to a JSON string, as SQS message bodies must be strings
        message_body = json.dumps(data_to_send)

        print(f"Attempting to send message to SQS queue: {queue_url}")
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=message_body
        )
        print(f"Message sent successfully. MessageId: {response['MessageId']}")
        return True
    except ClientError as e:
        print(f"Error sending message to SQS: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def main_logic():
    """
    Contains the main business logic of the application.
    """
    # cl = loginId()
    cl = login_with_s3_session()
    users_Dict = check_messages(cl)

    for key, values in users_Dict.items():
        thread_id = values[0]
        extracted_urls = []
        # Check if the list has more than one item before proceeding
        if len(values) > 1:
            # Loop through the list of URLs starting from the second element
            for url in values[1:]: 
                # CORRECT: Check the type of the 'url' variable
                if isinstance(url, HttpUrl):
                    extracted_urls.append(str(url)) # Convert HttpUrl object to string
                elif isinstance(url, str) and url.startswith('http'):
                    extracted_urls.append(url)
        sqs_data = {
            "user_name": key,
            "thread_id": thread_id,
            "audio_urls": extracted_urls # This is the list of strings
        }
        print("\nPrepared SQS message data")
        if SQS_QUEUE_URL == 'YOUR_SQS_QUEUE_URL_HERE':
            print("\nWARNING: SQS_QUEUE_URL is not set. Please update 'YOUR_SQS_QUEUE_URL_HERE' with your actual SQS Queue URL to send messages.")
        else:
            success = send_data_to_sqs(sqs_data, SQS_QUEUE_URL)
            if success:
                print("\nData successfully queued to SQS.")
            else:
                print("\nFailed to send data to SQS.")
    
    print("Main logic executed.")
    # You can return data from your logic to be sent in the response
    return {"status": "success"}

def lambda_handler(event, context):
    """
    Main Lambda handler function that gets invoked by AWS.
    """
    try:
        result = main_logic()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'InstaBot executed successfully.',
                'result': result
            })
        }
        
    except Exception as e:
        print(f"An error occurred in the handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }