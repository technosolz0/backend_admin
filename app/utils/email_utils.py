# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart


# def send_email_otp(receiver_email: str, otp: str):
#     sender_email = "yourgmail@gmail.com"
#     sender_password = "your-app-password"

#     message = MIMEMultipart("alternative")
#     message["Subject"] = "Your OTP Code"
#     message["From"] = sender_email
#     message["To"] = receiver_email

#     text = f"Your OTP code is: {otp}"
#     message.attach(MIMEText(text, "plain"))

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, receiver_email, message.as_string())
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def send_email_otp(receiver_email: str, otp: str):
    # sender_email = os.getenv("EMAIL_USERNAME")
    # sender_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your OTP Code"
    # message["From"] = sender_email
    # message["To"] = receiver_email

    text = f"Your OTP code is: {otp}"
    message.attach(MIMEText(text, "plain"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        pass
        # server.login(sender_email, sender_password)
        # server.sendmail(sender_email, receiver_email, message.as_string())
