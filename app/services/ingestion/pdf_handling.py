from langchain.document_loaders import PyPDFLoader
from langchain.docstore.document import Document

from app.services.service_utilities import (
    split_text_by_token,
    get_current_time, 
    datetime_to_str, 
    str_to_datetime
    )
from app.services.databases.qdrant_setup import load_qdrant_connection
import logging


def load_pdf_document(doc_path: str) -> list[Document]:
    """Loads the document using PyPDFLoader
    parameters:
        doc_path: path of the document we need to load
    
    returns:
        pages[list]: list of objects of type Document(page_content =  '...', metadata = {'source': '...', 'page': 0})
    """
    try:
        loader = PyPDFLoader(doc_path)
        pages = loader.load()
        return pages
    except Exception as e:
        logging.error(f"An error occurred while loading PDF: {e}")

def prepare_for_indexing_pdf(pages: list[Document], wa_id:str, media_id:str, caption: str, filename: str) -> list[Document]:
    """Splits the document into small chunks"""
    docs = []
    for item in pages:
        texts = item.page_content
        record_texts = split_text_by_token(texts) # split long str text into small str text 
        page_number = item.metadata.get("page", "-")
        record_docs = [
            Document(
                page_content = text,
                metadata= {
                    'group_id': wa_id, # Who is the owner of this pdf?
                    'type': "rag", # One of "rag" or "history"
                    'source': filename,
                    'source_type': "document", 
                    'media_id': media_id,
                    'caption': caption, 
                    'page': page_number,
                    'date': datetime_to_str(get_current_time())
                }
            ) for text in record_texts
        ]
        docs.extend(record_docs)
    return docs


def process_pdf_document(file_path: str, wa_id:str, media_id:str, caption: str, filename: str, qdrant_api_key:str, qdrant_url: str, qdrant_collection_name: str):
    pages = load_pdf_document(file_path)
    docs = prepare_for_indexing_pdf(pages, wa_id, media_id, caption, filename)
    qdrant_index = load_qdrant_connection(qdrant_url, qdrant_api_key, qdrant_collection_name)
    qdrant_index.add_documents(docs)
    logging.info(f"{len(docs)} documents processed.\n")


