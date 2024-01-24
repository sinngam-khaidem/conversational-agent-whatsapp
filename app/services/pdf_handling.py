import logging
from typing import Optional


def process_pdf_document(
    file_path: str, 
    wa_id:str, 
    media_id:str, 
    caption: str, 
    filename: str, 
    qdrant_api_key:str, 
    qdrant_url: str, 
    qdrant_collection_name: str, 
    openai_api_key:str
    ):
    try:
        from llama_index import (
            SimpleDirectoryReader, 
            Document
        )
        from app.services.databases.qdrant_setup import build_sentence_window_index
        from app.services.service_utilities import (
            get_current_time, 
            datetime_to_str
        )
        from app.services.service_utilities import generate_summary 
        reader = SimpleDirectoryReader(input_files = [file_path])
        documents = reader.load_data()
        logging.info("Document successfully read from the directory.")
        document = Document(
            text = "\n\n".join([doc.text for doc in documents]),
            metadata={
                "group_id": wa_id,
                "type": "rag",
                "source": filename,
                "source_type": "document",
                "media_id": media_id,
                "caption": caption,
                "date": datetime_to_str(get_current_time())
                }
            )
        summary = generate_summary(document.text[:3000], openai_api_key)
        sentence_index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
        sentence_index.insert(document=document)
        return summary
    except Exception as e:
        logging.error(f"An error occurred while indexing the document: {e}")



if __name__ == "__main__":
    pass


