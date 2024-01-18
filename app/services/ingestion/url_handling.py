from langchain.docstore.document import Document
from app.services.service_utilities import (
        split_text_by_token,
        get_current_time,
        datetime_to_str, 
        str_to_datetime
    )
from app.services.databases.qdrant_setup import load_qdrant_connection
import trafilatura
import logging

def prepare_for_indexing_html(source_url: str, wa_id:str, caption:str) -> list[Document]:
    try:
        downloaded = trafilatura.fetch_url(
            url=source_url
        )
        content = trafilatura.extract(downloaded)

        record_texts = split_text_by_token(content)
        record_docs=[Document(
                        page_content = text, 
                        metadata= {
                            'group_id': wa_id,
                            'type': 'rag',
                            'source': source_url,
                            'source_type': 'url',
                            "caption":caption,
                            'date': datetime_to_str(get_current_time())
                        }
                    ) for text in record_texts
                    ]
        return record_docs
    except Exception as e:
        logging.error(f"An error occurred while indexing html: {e}")

def process_url_document(url: str, wa_id:str, caption:str, qdrant_api_key:str, qdrant_url: str, qdrant_collection_name: str) -> int:
    docs = prepare_for_indexing_html(source_url=url, wa_id=wa_id, caption=caption)
    qdrant_index = load_qdrant_connection(qdrant_url, qdrant_api_key, qdrant_collection_name)
    qdrant_index.add_documents(docs)
    logging.info(f"{len(docs)} successfully processed\n")

if __name__ == "__main__":
    pass
    