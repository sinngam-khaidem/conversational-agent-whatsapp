import qdrant_client
from langchain.vectorstores import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
import logging
import json


def load_qdrant_connection(qdrant_url: str, qdrant_api_key:str, qdrant_collection_name:str):
    try:
        # https://python.langchain.com/docs/integrations/text_embedding/fastembed
        embeddings = FastEmbedEmbeddings(model_name = "BAAI/bge-small-en-v1.5")
        client = qdrant_client.QdrantClient(
            url = qdrant_url,
            api_key=qdrant_api_key, # For Qdrant Cloud, None for local instance
            timeout=10
        )
        qdrant_index = Qdrant(client=client, collection_name=qdrant_collection_name, embeddings=embeddings)
        return qdrant_index
    except Exception as e:
        logging.error(f"An error occurred while establishing connection to vector database: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import os 
    qdrant_index = load_qdrant_connection(os.getenv("QDRANT_URL"),
                                           os.getenv("QDRANT_API_KEY"), 
                                            os.getenv("COLLECTION_NAME"))
    results = qdrant_index.similarity_search("Logistic Regression")
    print(results)