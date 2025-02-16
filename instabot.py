import smtplib
import pandas as pd
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from "instabot-sqs-lambda"

load_dotenv()

sender_email = os.getenv('SENDER_EMAIL')
sender_password = os.getenv('SENDER_PASSWORD')
receiver_email = os.getenv('RECEIVER_EMAIL')

# List of songs
songs = []

def read_urls_row_by_row(filepath):
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
        if "gaana" not in df.columns:
            print("Error: 'URL List' column not found! Check the column name in Excel.")
            return

        # Loop through each row one by one
        for index, row in df.iterrows():
            song_name = row["gaana"]  # Extract URL from current row
            if(song_name == "Title not found"):
                continue
            youtube_url = f"https://www.youtube.com/results?search_query={song_name}"
            youtube_music_url = f"https://music.youtube.com/search?q={song_name}"
            songs.append((song_name, youtube_url,youtube_music_url))


        send_and_create_email()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found!")
    except Exception as e:
        print(f"An error occurred: {e}")

def send_and_create_email():

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


file_path = r"C:\Users\Akash\OneDrive\Desktop\InstaBot\instabot-search-engine\songs.xlsx"

read_urls_row_by_row(file_path)


def main():
    check