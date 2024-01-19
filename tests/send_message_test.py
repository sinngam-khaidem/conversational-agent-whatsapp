import requests
import logging

import json
from starlette.responses import JSONResponse
import os
from dotenv import load_dotenv
load_dotenv()

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERSION = os.getenv("WHATSAPP_VERSION")

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def get_text_message_input(recipient, text, preview_url=False):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": preview_url, "body": text},
        }
    )


def send_message(data, whatsapp_version:str, whatsapp_access_token: str, whatsapp_phone_number_id: str):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {whatsapp_access_token}",
    }

    url = f"https://graph.facebook.com/{whatsapp_version}/{whatsapp_phone_number_id}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return JSONResponse({"status": "error", "message": "Request timed out", "status_code": 408})
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return JSONResponse({"status": "error", "message": "Request timed out", "status_code": 500})
    else:
        # Process the response as normal
        log_http_response(response)
        return response

def get_media_message_input(recepient, media_id):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recepient,
            "type": "document",
            "document": {
                "id": media_id
            },
        }
    )

if __name__ == "__main__":
    url = f"https://graph.facebook.com/{WHATSAPP_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    response = requests.post(
                    url, data=get_text_message_input("919089342948", "This is a test"), headers=headers, timeout=10
                )  # 10 seconds timeout as an example