# import random
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import os
# from dotenv import load_dotenv

# load_dotenv()

# def generate_otp() -> str:
#     return str(random.randint(100000, 999999))

# def send_email_otp(receiver_email: str, otp: str):
#     sender_email = os.getenv("EMAIL_USERNAME")
#     sender_password = os.getenv("EMAIL_PASSWORD")

#     message = MIMEMultipart("alternative")
#     message["Subject"] = "Your OTP Code"
#     message["From"] = sender_email
#     message["To"] = receiver_email

#     text = f"Your OTP code is: {otp}"
#     message.attach(MIMEText(text, "plain"))

#     with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, receiver_email, message.as_string())


import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_email_otp(receiver_email: str, otp: str):
    sender_email = os.getenv("EMAIL_USERNAME")
    sender_password = os.getenv("EMAIL_PASSWORD")

    message = MIMEMultipart("alternative")
    message["Subject"] = "Your Serwex OTP Code"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Plain text fallback
    text = f"Your OTP code is: {otp}"

    # HTML styled template
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin:0; padding:0; background-color:#f9f9f9;">
        <table align="center" width="100%" cellpadding="0" cellspacing="0" style="max-width:600px;">
            <tr>
                <td style="background-color:#FAC94E; padding:20px; text-align:center; border-radius:8px 8px 0 0;">
                    <h1 style="margin:0; color:#000;">Serwex</h1>
                </td>
            </tr>
            <tr>
                <td style="background-color:#ffffff; padding:30px; text-align:center; border:1px solid #eee;">
                    <h2 style="color:#333;">Your OTP Code</h2>
                    <p style="font-size:16px; color:#555;">
                        Please use the following OTP code to complete your verification:
                    </p>
                    <div style="display:inline-block; padding:15px 25px; margin:20px 0;
                                font-size:24px; font-weight:bold; color:#000;
                                background-color:#FFD97C; border-radius:6px;">
                        {otp}
                    </div>
                    <p style="font-size:14px; color:#888;">
                        This code will expire in 10 minutes. Please do not share it with anyone.
                    </p>
                </td>
            </tr>
            <tr>
                <td style="background-color:#FACC59; text-align:center; padding:15px; border-radius:0 0 8px 8px;">
                    <p style="margin:0; font-size:12px; color:#333;">
                        © {2025} Serwex. All rights reserved.
                    </p>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Attach both plain text and HTML
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
