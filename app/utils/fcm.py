


import logging
from typing import Optional
from enum import Enum
import requests
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

class NotificationType(str, Enum):
    booking_created = "booking_created"
    booking_accepted = "booking_accepted"
    booking_cancelled = "booking_cancelled"
    booking_completed = "booking_completed"
    otp_sent = "otp_sent"
    payment_created = "payment_created"

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    Send FCM push notification with optional data payload.
    
    Args:
        token (str): FCM device token
        title (str): Notification title
        body (str): Notification body
        data (dict, optional): Custom data payload for the notification
    
    Returns:
        dict: Response from FCM server
    """
    if not FCM_SERVER_KEY:
        logger.error("FCM_SERVER_KEY environment variable not set")
        return {"error": "FCM_SERVER_KEY not configured"}
    
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "to": token,
        "notification": {
            "title": title,
            "body": body
        }
    }
    
    if data:
        payload["data"] = data
    
    try:
        response = requests.post(FCM_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"FCM notification sent successfully to {token}: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send FCM notification to {token}: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error sending FCM notification to {token}: {str(e)}")
        return {"error": str(e)}

def send_email_notification(recipient: str, subject: str, message: str):
    """
    Send email notification using send_email from otp_utils.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Email subject
        message (str): Email message body
    """
    from .otp_utils import send_email
    try:
        logger.info(f"Sending email notification to {recipient} with subject: {subject}")
        # Using send_email with a custom template or plain text could be implemented
        # For now, log as a placeholder
    except Exception as e:
        logger.error(f"Failed to send email notification to {recipient}: {str(e)}")

def send_notification(recipient: str, notification_type: NotificationType, message: str, recipient_id: int, fcm_token: Optional[str] = None):
    """
    Send a notification to the recipient via email and FCM (if token provided).
    
    Args:
        recipient (str): Email address of the recipient
        notification_type (NotificationType): Type of notification
        message (str): Notification message
        recipient_id (int): ID of the recipient (user or vendor)
        fcm_token (Optional[str]): FCM device token for push notifications
    """
    subject = f"Booking Notification: {notification_type.value.replace('_', ' ').title()}"
    send_email_notification(recipient=recipient, subject=subject, message=message)
    
    if fcm_token:
        send_push_notification(
            token=fcm_token,
            title=subject,
            body=message,
            data={"notification_type": notification_type.value, "recipient_id": recipient_id}
        )