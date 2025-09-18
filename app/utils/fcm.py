import requests
import os

FCM_SERVER_KEY = os.getenv("FCM_SERVER_KEY")
FCM_URL = "https://fcm.googleapis.com/fcm/send"

def send_push_notification(token: str, title: str, body: str):
    headers = {
        "Authorization": f"key={FCM_SERVER_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": token,
        "notification": {"title": title, "body": body}
    }
    response = requests.post(FCM_URL, headers=headers, json=payload)
    return response.json()
