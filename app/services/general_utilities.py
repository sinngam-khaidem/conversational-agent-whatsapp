import requests
import logging
import boto3
import re
import json
from starlette.responses import JSONResponse
import httpx

def get_media_file_content_from_whatsapp(media_id:str, whatsapp_version:str, whatsapp_access_token: str, whatsapp_phone_number_id: str):
    """"
        Retrieves the content of a media file from Whatsapp Cloud API using its Media ID.
        This function makes two separate get request from Whatsapp Cloud API - First to retrieve Media URL using
        Media ID, and Second to retrieve media file content using Media URL.
    """
    # Retrieve the media URL and filesize by making a GET request to this endpoint. The url will last only 5 mins. Check Whatsapp Business API docs.
    url_request_response = requests.get(
        url=f"https://graph.facebook.com/{whatsapp_version}/{media_id}/", 
        headers={
            "Authorization": f"Bearer {whatsapp_access_token}"
        },
        params=whatsapp_phone_number_id
    )
    url_request_response.raise_for_status()
    media_url = url_request_response.json()["url"]
    # file_size = url_request_response.json()["file_size"]

    # Get the content of the media associated with the URL.
    media_file_resp = requests.get(
        url=media_url,
        headers={
            "Authorization": f"Bearer {whatsapp_access_token}"
        }
    )
    return media_file_resp.content

# Some cleaning up of the text before sending a text message from us(server) to user.
def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text

def read_file_from_s3(bucketName:str, key:str, aws_access_key_id:str, aws_secret_access_key:str):
    """Function for reading file from an S3 bucket. INCOMPLETE IMPLEMENTATION"""
    try:
        s3_resource = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        bucket = s3_resource.Bucket(bucketName)

    except Exception as e:
        logging.error(f"An error occurred while reading file from s3: {e}")


def write_file_to_s3(file:str, bucketName:str, key:str, aws_access_key_id:str, aws_secret_access_key:str):
    """Function for writing file to an S3 bucket."""
    try:
        s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        s3.upload_file(file, bucketName, key) 
        logging.info(f"Successfully wrote file to s3: s3://{bucketName}/{key}")
    except Exception as e:
        logging.error(f"Error writing file to s3: {e}")


def log_http_response(response):
    """Logging HTTP response to console"""
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")

def get_text_message_input(recipient, text, preview_url=False):
    """
        Setting up the text message to be sent from us(server) to the user.
        Arguments:
            recipient - Recipient's whatsapp phone number
            text - Content of the text message to be sent
            preview_url - Do we want to display thumbnails/preview when we send URL?
    """
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
    """
        Function for sending text or media message from us(server) to the user.
        Arguments:
            data - JSON representation of the data to be sent. We can easily create this using
            get_text_message_input() or get_media_message_input() functions.
    """
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
    """
        Setting up the media message to be sent from us(server) to the user.
        Arguments:
            recipient - Recipient's whatsapp phone number
            media_id - Content of the media message to be sent
            preview_url - Do we want to display thumbnails/preview when we send URL?
    """
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

async def mark_msg_as_read(msg_id:str, whatsapp_version:str, whatsapp_phone_number_id:str, whatsapp_access_token:str):
    """
        Asynchronous implementation of a function to mark a message that was sent by user to us(server) as read. The double blue tick you see 
        every day on whatsapp. 
    """
    async with httpx.AsyncClient() as client:
        try:
            url = f"https://graph.facebook.com/{whatsapp_version}/{whatsapp_phone_number_id}/messages"
            payload = json.dumps({
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": msg_id
            })
            headers = {
                'Authorization': f"Bearer {whatsapp_access_token}",
                'Content-Type': 'application/json'
            }
            response = await client.post(url, headers=headers, data=payload)
            logging.info(response)
        except httpx.RequestError as e:
            logging.error(f"Request error in marking message as read: {e}")
        except httpx.HTTPError as e:
            logging.error(f"HTTP error while marking message as read: {e}")

def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event/messsage payload has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )