from cachetools import TTLCache
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv
from app.tasks import (
    embedd_pdf,
    embedd_url,
    agent_call
)
from app.services.general_utilities import (
    mark_msg_as_read,
    is_valid_whatsapp_message,
    send_message,
    get_text_message_input
)
from app.services.service_utilities import detect_and_extract_urls
import time
load_dotenv()

# Load the necessary Whatsapp Cloud API credentials.
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN')
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN')
WHATSAPP_VERSION = os.getenv('WHATSAPP_VERSION')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID')

myapp = FastAPI()
# Creating a cache with a TTL of 300 seconds. This will be use to deduplicate incoming packets.
cache = TTLCache(maxsize=1000, ttl=300)

# Whatsapp Cloud API Verification Requests endpoint.
@myapp.get("/webhook")
def verify(request: Request):
    print("subscribe is being called")
    print(VERIFY_TOKEN)
    if request.query_params.get('hub.verify_token') == VERIFY_TOKEN:
        return JSONResponse(content=int(request.query_params.get('hub.challenge')), status_code=200)
    return "Authentication failed. Invalid Token."

# Whatapp Cloud API Event Notifications endpoint.
@myapp.post("/webhook")
async def handle_message(request: Request):
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = await request.json()

    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        print("Received a whatsapp status update.")
        return JSONResponse(content= {"status": "Whatsapp status update received."}, status_code = 200)
    
    try:
        if is_valid_whatsapp_message(body):
            msg_id = body["entry"][0]["changes"][0]["value"]["messages"][0]["id"]
            wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
            message = body["entry"][0]["changes"][0]["value"]["messages"][0]
            message_type = message["type"]
            timestamp = message["timestamp"]

            # If message ID is in cache or notification is older than 5 mins, we won't entertain such event notifications.
            if cache.get(msg_id) is not None or int(timestamp) < int(time.time()) - 300:
                return JSONResponse(content = {'body': "message already seen"}, status_code=200)
            else:
                cache[msg_id] = True
            
            # Incoming notification is for a text message.
            if message_type == "text":
                message_body = message["text"]["body"]
                detected_urls = detect_and_extract_urls(message_body)
                if len(detected_urls) > 0:
                    send_message(
                        get_text_message_input(
                            wa_id, 
                            f"_Processing your urls_..."
                        ),
                        WHATSAPP_VERSION,
                        WHATSAPP_ACCESS_TOKEN,
                        WHATSAPP_PHONE_NUMBER_ID
                    )
                    for url in detected_urls:
                        url_request_body = {
                            "url_address": url,
                            "senders_wa_id": wa_id,
                            "caption": message_body
                        }
                        embedd_url(embed_url_request = url_request_body)
                    return JSONResponse(content = {'answer': "Url indexed."})
                else:
                    agent_call_body = {
                        "message_body": message_body,
                        "senders_wa_id": wa_id
                    }
                    agent_call_response = agent_call(agent_call_request=agent_call_body)
                    return JSONResponse(content = {'answer': agent_call_response})
            
            # Incoming notification is for a document or an image.
            elif message_type == "document" or message_type == "image":
                mime_type = message[message_type]["mime_type"]
                if mime_type in ["application/pdf", "image/jpeg", "image/png"]:
                    send_message(
                        get_text_message_input(
                            wa_id, 
                            f"_Processing your media_..."
                        ),
                        WHATSAPP_VERSION,
                        WHATSAPP_ACCESS_TOKEN,
                        WHATSAPP_PHONE_NUMBER_ID
                    )
                    if mime_type == "application/pdf":
                        pdf_file_request_body = {
                            "filename": message[message_type].get("filename", "Unamed"),
                            "media_id": message[message_type]["id"],
                            "senders_wa_id": wa_id,
                            "caption": message[message_type].get("caption", "No caption"),
                            "media_type": message_type,
                            "mime_type": mime_type
                        }
                        embedd_pdf(embed_pdf_request=pdf_file_request_body)
                        return JSONResponse(content = {'body': 'Successfully indexed your media.'}, status_code = 200)
                    else:
                        return JSONResponse(content= {'body': 'Invalid mime type'}, status_code = 200)
    except Exception as e:
        print(f"An error occured: {e}")
        return JSONResponse(status_code = 500)

# Payload examples:
# https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples