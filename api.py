from fastapi import FastAPI
from starlette.responses import JSONResponse
from app.data_models.request_data_models import (
        PdfFileRequest,
        ImageFileRequest,
        TextFileRequest,
        UrlRequest,
        AgentCallRequest
    )
from app.data_models.response_data_models import (
        EmbeddingResponse
    )

from app.general_utilities import (
    get_media_file_content_from_whatsapp,
    process_text_for_whatsapp,
    send_message,
    get_text_message_input,
    get_media_message_input,
    write_file_to_s3,
    read_file_from_s3
    )

from app.services.ingestion.pdf_handling import process_pdf_document
from app.services.ingestion.url_handling import process_url_document
from app.services.conversation_service import RealtyaiBot
import logging
import os
from dotenv import load_dotenv

load_dotenv()

myapp = FastAPI()


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


@myapp.get("/")
def read_root():
    return {"data": "Hello World"}

@myapp.post('/embeddings/pdf')
def post_embedd_pdf(embed_pdf_request: PdfFileRequest):
    """Embeds the pdf document to the vector database"""
    logging.info("Embedding PDF document.")
    temp_files_dir = "/app/temp_files_dir"
    s3_object_key = f"user_resources/{embed_pdf_request.senders_wa_id}/{embed_pdf_request.media_id}.pdf"

    if os.path.exists(temp_files_dir):
        raise ValueError("Please provide a temporary folder to save the files.")

    path_to_file = f'{temp_files_dir}/{embed_pdf_request.media_id}.pdf'

    try:
        with open(path_to_file, 'wb') as file:
            file.write(get_media_file_content_from_whatsapp(embed_pdf_request.media_id, WHATSAPP_VERSION, WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID))
        process_pdf_document(path_to_file, embed_pdf_request.senders_wa_id, embed_pdf_request.media_id, embed_pdf_request.caption, embed_pdf_request.filename, QDRANT_API_KEY, QDRANT_URL, QDRANT_COLLECTION_NAME, OPENAI_API_KEY)
        write_file_to_s3(path_to_file, AWS_BUCKET_NAME, s3_object_key, AWS_ACCESS_KEY, AWS_SECRET_KEY)
    except Exception as e:
        logging.error(f"An error occurred while embedding pdf: {e}")
    finally:
        os.remove(path_to_file)    
    return JSONResponse(content={"status":"success"}, status_code=200)


@myapp.post('/embeddings/url')
def post_embedd_url(embed_url_request: UrlRequest):
    """Embeds the url address to the vector database"""
    logging.info("Embedding URL document.")

    try:
        process_url_document(embed_url_request.url_address, embed_url_request.senders_wa_id, embed_url_request.caption, QDRANT_API_KEY, QDRANT_URL, QDRANT_COLLECTION_NAME, OPENAI_API_KEY)
    except Exception as e:
        logging.error(f"An error occurred while embedding url: {e}")
    return JSONResponse(content={"status":"success"}, status_code=200)
    
@myapp.post('/agent')
def agent_call(agent_call_request: AgentCallRequest):
    """Requests action from the agent"""

    realtyai_bot = RealtyaiBot(
            agent_call_request.senders_wa_id, 
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
    response = realtyai_bot(agent_call_request.message_body)
    response = process_text_for_whatsapp(response)
    try:
        send_message(
            get_text_message_input(agent_call_request.senders_wa_id, response),
            WHATSAPP_VERSION,
            WHATSAPP_ACCESS_TOKEN,
            WHATSAPP_PHONE_NUMBER_ID 
        )
    except Exception as e:
        logging.error(f"An error occurred while sending the reply of agent call: {e}")

    return {'Agent Response': response}