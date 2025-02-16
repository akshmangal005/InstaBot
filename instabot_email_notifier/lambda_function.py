import smtplib
import pandas as pd
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from instabot_sqs_lambda import *
from instabot_search_engine import *

load_dotenv()

sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')

def send_and_create_email(songs,receiver_email):

    email_body = """\
<html>
<head>
    <meta charset="UTF-8">
    <style>
        table {border-collapse: collapse; width: 100%;}
        th, td {border: 1px solid black; padding: 8px; text-align: left;}
        th {background-color: #f2f2f2;}
        a {text-decoration: none; color: blue;}
    </style>
</head>
<body>
    <p>Hello,</p>
    <p>Given below is the list of songs you shared with Instabot.</p>
    <table>
        <tr>
            <th>Song Name</th>
            <th>YouTube Link</th>
            <th>YouTube Music Link</th>
        </tr>
"""
    # Adding songs dynamically
    for song in songs:
        email_body += f"""
            <tr>
                <td>{song[0]}</td>
                <td><a href="{song[1]}" target="_blank">YouTube</a></td>
                <td><a href="{song[2]}" target="_blank">YouTube Music</a></td>
            </tr>
        """

    email_body += """
        </table>
        <p>Best regards,<br>InstaBot</p>
    </body>
    </html>
    """

    # Create email message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = "List of Songs from Instabot"

    # Ensure HTML content type is properly set
    msg.attach(MIMEText(email_body, "html"))
    # Connect to Gmail SMTP server and send email
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error: {e}")