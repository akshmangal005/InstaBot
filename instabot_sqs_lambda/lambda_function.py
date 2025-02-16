import os
import boto3
import botocore
import json
import pandas as pd
from botocore.exceptions import ClientError
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from instagrapi import Client
from botocore.config import Config

config = Config(
    retries={
        'max_attempts': 5,
        'mode': 'standard'
    }
)

instagram_username = os.environ['USERNAME']
instagram_password = os.environ['PASSWORD']

url_list = [] 


def create_excel_with_urls(urls, filename="url_list.xlsx"):
    """
    Creates an Excel file with a single column 'URL List' and stores the given list of URLs.

    :param urls: List of URLs to be stored in the Excel file.
    :param filename: Name of the Excel file to be saved (default: url_list.xlsx).
    """
    # Create a DataFrame with a single column "URL List"
    df = pd.DataFrame({"urls": urls})

    # Save DataFrame to an Excel file
    df.to_excel(filename, index=False)

    print(f"Excel file '{filename}' created successfully!")


def check_messages():
    global url_list

    if not instagram_username or not instagram_password:
        raise ValueError("Username and password must be set in environment variables.")
    
    print("Attempting Instagram login...")
    cl = Client()
    cl.login(instagram_username, instagram_password)
    print("Login Successful")

    try:
        print("Checking new messages...")
        threads = cl.direct_threads(20, "unread")

        if len(threads) > 0:
            my_chat = threads[0]
            thread_id = my_chat.id

            if hasattr(my_chat, 'messages'):
                for item in my_chat.messages:
                    if hasattr(item, 'clip') and hasattr(item.clip, 'video_url'):
                        url_list.append(item.clip.video_url)
                    else:
                        continue
                cl.direct_thread_hide(thread_id)  # Deletes the entire chat
            else:
                print("Message field not found in thread.")
        else:
            print("No new messages.")
    except Exception as e:
        print(f"Error occurred while checking new messages: {e}")


# def lambda_handler(event, context):
check_messages()
# print(url_list)
create_excel_with_urls(url_list)
    
    # sqs_client = boto3.client('sqs', config=config)
    # sqs_queue_url = os.getenv('INSTABOTSQSQUEUEURL')

    # if not sqs_queue_url:
    #     raise ValueError("Queue Url must be set in environment variables.")

    # for i, url in enumerate(url_list):
    #     try:
    #         message_payload = {
    #             'id': i,
    #             'url': url
    #         }
    #         response = sqs_client.send_message(
    #             QueueUrl=sqs_queue_url,
    #             MessageBody=json.dumps({'url_list': message_payload})
    #         )
    #         print(f"Message sent to SQS: {response['MessageId']}")
    #     except ClientError as e:
    #         print(f"Error sending message to SQS: {e}")
    #         raise e

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Success')
    # }
