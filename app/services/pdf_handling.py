import logging

def process_pdf_document(file_path: str, wa_id:str, media_id:str, caption: str, filename: str, qdrant_api_key:str, qdrant_url: str, qdrant_collection_name: str, openai_api_key:str):
    from llama_index import (
        SimpleDirectoryReader, 
        Document
    )
    from app.services.databases.qdrant_setup import build_sentence_window_index
    from app.services.service_utilities import (
        get_current_time, 
        datetime_to_str
    )
    try:
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
        summary = generate_summary(document.text[:6000], openai_api_key)
        sentence_index = build_sentence_window_index(openai_api_key, qdrant_url, qdrant_api_key, qdrant_collection_name)
        sentence_index.insert(document=document)
        return summary
    except Exception as e:
        logging.error(f"An error occurred while indexing the document: {e}")

def generate_summary(text:str, openai_api_key:str):
    from langchain.chains.summarize import load_summarize_chain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    llm = ChatOpenAI(temperature=0, openai_api_key =openai_api_key)
    from typing_extensions import Concatenate

    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 3000, chunk_overlap = 20)
    chunks = text_splitter.create_documents([text])
    chunk_prompt=""""
    The following is a set of documents
    {text}
    Based on this list of docs, please identify the main themes 
    Helpful Answer:
    """
    map_prompt_template = PromptTemplate(input_variables=['text'], template=chunk_prompt)
    final_combine_prompt = """The following is set of summaries:
    {text}
    Take these and distill it into a very short, final, consolidated summary of the main themes.
    Append 3 example questions(without answers) from the consolidated summary. 
    Helpful Answer:"""
    final_combine_prompt_template=PromptTemplate(input_variables=['text'], template=final_combine_prompt)
    summary_chain = load_summarize_chain(
        llm=llm,
        chain_type='map_reduce',
        map_prompt=map_prompt_template,
        combine_prompt=final_combine_prompt_template,
        verbose = True
    )
    return summary_chain.run(chunks)

if __name__ == "__main__":
    pass


