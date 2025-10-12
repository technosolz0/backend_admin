import requests
import os
import logging

logger = logging.getLogger(__name__)

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

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
    
    # Add data payload if provided
    if data:
        payload["data"] = data
    
    try:
        response = requests.post(FCM_URL, headers=headers, json=payload)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        result = response.json()
        logger.info(f"FCM notification sent successfully to {token}: {result}")
        return result
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send FCM notification: {str(e)}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error sending FCM notification: {str(e)}")
        return {"error": str(e)}