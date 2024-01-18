# Deprecated

import easyocr
from langchain.docstore.document import Document
from uuid import uuid4
import os
from dotenv import load_dotenv

from service_utilities.splitter import text_splitter
from service_utilities.date_and_time import get_current_time, datetime_to_str

reader = easyocr.Reader(['en'], gpu = False)


def extract_text_from_image(image_path: str) ->str:
    print("Extracting text from image using ocr......")
    text = ""
    result = reader.readtext(image_path, detail = 0)
    for item in result:
        text += item + "\n"
    print("Text extraction completed.")
    print(f"Length of extracted text: ", len(text))
    return text


def prepare_for_indexing_text_image(content: str, media_info: dict) -> list[Document]:
    record_texts = text_splitter.split_text(content)
    record_docs = [Document(page_content = text, metadata= {\
            'chunk': j, 'id': str(uuid4()), 'source': media_info['filename'] + ".png",'date': datetime_to_str(get_current_time()),\
            'source_content_type': media_info['content_type']}) for j, text in enumerate(record_texts)]
    return record_docs

def process_text_based_image(image_source: str, media_info: dict) -> None:
    texts = extract_text_from_image(image_source)
    docs = prepare_for_indexing_text_image(content=texts, media_info= media_info)
    embed_document(docs)

def embed_document(docs: list[Document])->None:
    """Embed the splits, store in a vector database and store the vector store in a persistent directory
    for future use"""
    content_db = get_db_connection(url, api_key, collection_name)
    content_db.add_documents(docs)
    print(f"{len(docs)} documents embedded")

if __name__ == "__main__":
    print(extract_text_from_image("./test-documents/Id_page-0001.jpg"))

