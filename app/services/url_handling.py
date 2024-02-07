import logging



def process_url_document(
    source_url: str, 
    wa_id:str, 
    caption:str, 
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
        import trafilatura
        from app.services.service_utilities import generate_summary
        downloaded = trafilatura.fetch_url(
            url=source_url
        )
        content = trafilatura.extract(downloaded)

        # Create a document using content of the URL
        document = Document(
            text = content,
            metadata= {
                'group_id': wa_id,
                'type': 'rag',
                'media_id':source_url,
                'source': source_url,
                'source_type': 'url',
                "caption":caption,
                'date': datetime_to_str(get_current_time())
            }
        )

        # Generate summary of the first 3000 characters
        summary = generate_summary(document.text[:3000], openai_api_key)

        # Insert the document of the vector store
        sentence_index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
        sentence_index.insert(document=document)
        
        return summary
        
    except Exception as e:
        logging.error(f"An error occurred while indexing html: {e}")

if __name__ == "__main__":
    pass
    