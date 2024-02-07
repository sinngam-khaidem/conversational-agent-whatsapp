import logging
import json

def build_sentence_window_index(openai_api_key:str, qdrant_url:str, qdrant_api_key:str, qdrant_collection_name:str):
    import openai
    from llama_index.embeddings import FastEmbedEmbedding
    from llama_index.embeddings import OpenAIEmbedding
    from llama_index.llms import OpenAI
    import qdrant_client
    from llama_index.node_parser import SentenceWindowNodeParser
    from llama_index.vector_stores.qdrant import QdrantVectorStore
    from llama_index import (
            ServiceContext,
            StorageContext,
            VectorStoreIndex
    )

    try:
        openai.api_key = openai_api_key
        
        client = qdrant_client.QdrantClient(
            url = qdrant_url,
            api_key = qdrant_api_key,
            timeout=60
        )

        llm = OpenAI(model = "gpt-3.5-turbo", temperature = 0.1, max_tokens=128)

        # Create an instance of the embedding model to be used
        # embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")
        embed_model = OpenAIEmbedding(model_name="text-embedding-3-small")

        sentence_node_parser = SentenceWindowNodeParser.from_defaults(
                            window_size = 4,
                            window_metadata_key = "window",
                            original_text_metadata_key= "original_text"
                        )
        sentence_context = ServiceContext.from_defaults(
                    llm=llm,
                    embed_model = embed_model,
                    node_parser=sentence_node_parser
                    )

        vector_store = QdrantVectorStore(client=client, collection_name=qdrant_collection_name)
        sentence_index = VectorStoreIndex.from_vector_store(vector_store=vector_store, service_context=sentence_context, use_async=True, show_progress=True)
        return sentence_index
    except Exception as e:
        logging.error(f"An error occurred while builing the sentence window index: {e}")

def build_sentence_window_query_engine(
        senders_wa_id:str, 
        cohere_api_key:str, 
        openai_api_key:str, 
        qdrant_url:str, 
        qdrant_api_key:str, 
        qdrant_collection_name:str, 
        similarity_top_k=6, 
        rerank_top_n=2
    ):
    from llama_index.postprocessor.cohere_rerank import CohereRerank
    from llama_index.indices.postprocessor import MetadataReplacementPostProcessor
    from llama_index.vector_stores.types import MetadataFilters, ExactMatchFilter
    from app.services.databases.qdrant_setup import build_sentence_window_index
    
    sentence_index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
    postproc = MetadataReplacementPostProcessor(
        target_metadata_key="window"
    )
    cohere_rerank = CohereRerank(api_key=cohere_api_key, top_n=rerank_top_n)
    sentence_window_engine = sentence_index.as_query_engine(
                                filters=MetadataFilters(
                                    filters=[
                                        ExactMatchFilter(
                                            key="group_id",
                                            value=senders_wa_id,
                                        )
                                    ]
                                ),
                                similarity_top_k=similarity_top_k, 
                                node_postprocessors=[postproc, cohere_rerank]
                            )
    return sentence_window_engine

def build_index_retriever(
        senders_wa_id:str, 
        cohere_api_key:str,
        openai_api_key:str, 
        qdrant_url:str, 
        qdrant_api_key:str, 
        qdrant_collection_name:str, 
        similarity_top_k=6, 
        rerank_top_n=3
    ):
    from llama_index.vector_stores.types import MetadataFilters, ExactMatchFilter
    from app.services.databases.qdrant_setup import build_sentence_window_index
    from llama_index.indices.postprocessor import MetadataReplacementPostProcessor
    from llama_index.postprocessor.cohere_rerank import CohereRerank
    postproc = MetadataReplacementPostProcessor(
        target_metadata_key="window"
    )
    index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
    cohere_rerank = CohereRerank(api_key=cohere_api_key, top_n=rerank_top_n)
    node_retriever = index.as_retriever(
                                filters=MetadataFilters(
                                    filters=[
                                        ExactMatchFilter(
                                            key="group_id",
                                            value=senders_wa_id,
                                        )
                                    ]
                                ),
                                similarity_top_k=similarity_top_k,
                                node_postprocessors=[postproc, cohere_rerank]
                            )
    return node_retriever

def load_qdrant_connection(qdrant_url: str, qdrant_api_key:str, qdrant_collection_name:str):
    try:
        import qdrant_client
        from langchain.vectorstores import Qdrant
        from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
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
    pass