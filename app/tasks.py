from app.data_models.request_data_models import (
        PdfFileRequest,
        ImageFileRequest,
        TextFileRequest,
        UrlRequest,
        AgentCallRequest
    )

from app.services.general_utilities import (
    get_media_file_content_from_whatsapp,
    process_text_for_whatsapp,
    send_message,
    get_text_message_input,
    get_media_message_input,
    write_file_to_s3,
    read_file_from_s3
    )

from app.services.pdf_handling import process_pdf_document
from app.services.url_handling import process_url_document
from app.services.conversation_service import RealtyaiBot
from app.services.databases.dynamodb_setup import DynamoDBSessionManagement
from langchain_core.messages import SystemMessage
import logging
import os
from dotenv import load_dotenv
load_dotenv()

# Load the environment variables and qdrant collection name
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AWS_ACCESS_KEY=os.getenv("AWS_ACCESS_KEY_ID") 
AWS_SECRET_KEY=os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_BUCKET_NAME=os.getenv("AWS_BUCKET_NAME")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv("COLLECTION_NAME")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERSION = os.getenv("WHATSAPP_VERSION")
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

def post_embedd_pdf(embed_pdf_request):
    """Embeds the pdf document to the vector database"""
    temp_files_dir = "./app/temp_files_dir"
    s3_object_key = f"user_resources/{embed_pdf_request['senders_wa_id']}/{embed_pdf_request['media_id']}.pdf"

    if not os.path.exists(temp_files_dir):
        raise ValueError("Please provide a temporary folder to save the files.")

    path_to_file = f'{temp_files_dir}/{embed_pdf_request["media_id"]}.pdf'

    try:
        with open(path_to_file, 'wb') as file:
            file.write(get_media_file_content_from_whatsapp(embed_pdf_request["media_id"], WHATSAPP_VERSION, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID))

        summary = process_pdf_document(
            path_to_file, 
            embed_pdf_request["senders_wa_id"], 
            embed_pdf_request["media_id"], 
            embed_pdf_request["caption"], 
            embed_pdf_request["filename"], 
            QDRANT_API_KEY, 
            QDRANT_URL, 
            QDRANT_COLLECTION_NAME, 
            OPENAI_API_KEY
        )
        DynamoDBSessionManagement(
            DYNAMODB_TABLE_NAME, 
            embed_pdf_request["senders_wa_id"], 
            AWS_ACCESS_KEY, 
            AWS_SECRET_KEY).add_message(SystemMessage(content = f"These context might help you:\n\n{summary}"))
        try:
            send_bot_response = send_message(
                get_text_message_input(embed_pdf_request["senders_wa_id"], summary + "\n\n_Use the_ *Rag* _keyword to ask these questions._"),
                WHATSAPP_VERSION,
                WHATSAPP_ACCESS_TOKEN,
                WHATSAPP_PHONE_NUMBER_ID 
            )
            assert send_bot_response.status_code == 200
        except Exception as e:
            logging.error(f"An error occurred while sending the summary: {e}")
        write_file_to_s3(path_to_file, AWS_BUCKET_NAME, s3_object_key, AWS_ACCESS_KEY, AWS_SECRET_KEY)
    except Exception as e:
        logging.error(f"An error occurred while embedding pdf: {e}")
    finally:
        os.remove(path_to_file)    
    


def post_embedd_url(embed_url_request):
    """Embeds the url address to the vector database"""
    logging.info("Embedding URL document.")

    try:
        summary = process_url_document(
            embed_url_request["url_address"], 
            embed_url_request["senders_wa_id"], 
            embed_url_request["caption"], 
            QDRANT_API_KEY, 
            QDRANT_URL, 
            QDRANT_COLLECTION_NAME, 
            OPENAI_API_KEY
        )
        DynamoDBSessionManagement(
            DYNAMODB_TABLE_NAME, 
            embed_url_request["senders_wa_id"], 
            AWS_ACCESS_KEY, 
            AWS_SECRET_KEY).add_message(SystemMessage(content = f"These context might help you:\n\n{summary}"))
        try:
            send_bot_response = send_message(
                get_text_message_input(embed_url_request["senders_wa_id"], summary + "\n\n_Use the_ *Rag* _keyword to ask these questions._"),
                WHATSAPP_VERSION,
                WHATSAPP_ACCESS_TOKEN,
                WHATSAPP_PHONE_NUMBER_ID 
            )
            assert send_bot_response.status_code == 200
        except Exception as e:
            logging.error(f"An error occurred while sending the summary: {e}")

    except Exception as e:
        logging.error(f"An error occurred while embedding url: {e}")
    

def agent_call(agent_call_request):
    """Requests action from the agent"""

    realtyai_bot = RealtyaiBot(
            1000,
            agent_call_request["senders_wa_id"],
            OPENAI_API_KEY,
            COHERE_API_KEY, 
            AWS_ACCESS_KEY, 
            AWS_SECRET_KEY,
            QDRANT_API_KEY,
            QDRANT_URL,
            QDRANT_COLLECTION_NAME,
            WHATSAPP_VERSION,
            WHATSAPP_ACCESS_TOKEN,
            WHATSAPP_PHONE_NUMBER_ID,
            DYNAMODB_TABLE_NAME
        )
    bot_response = realtyai_bot(agent_call_request["message_body"])
    bot_response = process_text_for_whatsapp(bot_response)
    try:
        send_bot_response = send_message(
            get_text_message_input(agent_call_request["senders_wa_id"], bot_response),
            WHATSAPP_VERSION,
            WHATSAPP_ACCESS_TOKEN,
            WHATSAPP_PHONE_NUMBER_ID 
        )
        assert send_bot_response.status_code == 200
        return bot_response
    except Exception as e:
        logging.error(f"An error occurred while sending the reply of agent call: {e}")
        return "Agent Response error."