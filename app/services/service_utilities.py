from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from langchain.docstore.document import Document
from typing import List, Dict
from urlextract import URLExtract
from datetime import datetime
import pytz
import pyshorteners
import logging

# Function to split texts by token
def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding('cl100k_base')
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

def split_text_by_token(text: str) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        separators = ["\n\n", "\n", ".", ""],
        chunk_size = 128,
        chunk_overlap = 30,
        length_function = tiktoken_len
    )
    docs = text_splitter.split_text(text)
    return docs

# Function to detect and extract urls
def detect_and_extract_urls(text: str)->List[str]:
    extractor = URLExtract()
    urls = []
    if extractor.has_urls(text):
        urls.extend(extractor.find_urls(text))
    return urls

# Functions for handling date and time
def get_current_time() -> datetime:
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    return current_time

# Function to convert datetime.datetime object into str
def datetime_to_str(date: datetime) -> str:
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    return date_str

# Function to convert str into datetime.datetime object
def str_to_datetime(date: str) -> datetime:
    parsed_date = date.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return parsed_date

# Function for merging list of documents into a single source
def merge_docs_to_source(docs: List[Document]) -> List[str]:
    source_dict: Dict[str, int] = {}

    for doc in docs:
        doc_source = doc.metadata.get("media_id", "_blank")
        if doc_source in source_dict.keys():
            source_dict[doc_source] += 1
        else:
            source_dict[doc_source] = 1
    
    max_frequency = max(source_dict.values())

    max_frequency_keys = [key for key, value in source_dict.items() if value == max_frequency]

    return max_frequency_keys

def shorten_url(long_url:str):
    try:
        type_tiny = pyshorteners.Shortener()
        short_url = type_tiny.tinyurl.short(long_url)
        return short_url
    except Exception as e:
        return long_url
    


if __name__ == "__main__":
    pass

    # docs = [
    #     Document(
    #         page_content="abc", 
    #         metadata={
    #             "source": "X"
    #         }
    #     ),
    #     Document(
    #         page_content="def", 
    #         metadata={
    #             "source": "Y"
    #         }
    #     ),
    #     Document(
    #         page_content="ghi", 
    #         metadata={
    #             "source": "Y"
    #         }
    #     ),
    #     Document(
    #         page_content="jkl", 
    #         metadata={
    #             "source": "X"
    #         }
    #     ),
    #     Document(
    #         page_content="mno", 
    #         metadata={
    #             "source": "Z"
    #         }
    #     ),
    #     Document(
    #         page_content="pqr", 
    #         metadata={
    #             "source": "P"
    #         }
    #     ),
        
    #     ]
    # print(merge_docs_to_source(docs))
