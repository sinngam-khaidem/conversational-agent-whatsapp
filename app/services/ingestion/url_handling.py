import logging

def process_url_document(url: str, wa_id:str, caption:str, qdrant_api_key:str, qdrant_url: str, qdrant_collection_name: str, openai_api_key:str):
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
        import trafilatura
        downloaded = trafilatura.fetch_url(
            url=source_url
        )
        content = trafilatura.extract(downloaded)

        document = Document(
            text = content,
            metadata= {
                'group_id': wa_id,
                'type': 'rag',
                'source': source_url,
                'source_type': 'url',
                "caption":caption,
                'date': datetime_to_str(get_current_time())
            }
        )
        sentence_index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
        sentence_index.insert(document=document)
        
    except Exception as e:
        logging.error(f"An error occurred while indexing html: {e}")

if __name__ == "__main__":
    pass
    