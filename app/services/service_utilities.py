from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
from langchain.docstore.document import Document
from typing import List, Dict
from urlextract import URLExtract
from datetime import datetime
import pytz
from llama_index.schema import NodeWithScore

# Function to count the number of tokens using tiktoken. (IGNORE)
# https://github.com/openai/tiktoken
def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding('cl100k_base')
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

# Function to split long texts into chunks based on number of tokens (not number of characters) (IGNORE)
def split_text_by_token(text: str) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        separators = ["\n\n", "\n", ".", ""],
        chunk_size = 128,
        chunk_overlap = 30,
        length_function = tiktoken_len
    )
    docs = text_splitter.split_text(text)
    return docs

# Function to detect and extract urls from given text.
def detect_and_extract_urls(text: str)->List[str]:
    extractor = URLExtract()
    urls = []
    if extractor.has_urls(text):
        urls.extend(extractor.find_urls(text))
    return urls

# Functions for retrieving current time for the specified timezone using pytz
# pytz Documentation: https://pypi.org/project/pytz/
def get_current_time() -> datetime:
    """Returns date and time for the specified timezone as datetime.datetime data type"""
    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)
    return current_time

# Function to convert datetime.datetime datatype into string. 
def datetime_to_str(date: datetime) -> str:
    # strftime - string from time
    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    return date_str

# Function to convert string into datetime.datetime datatype
def str_to_datetime(date: str) -> datetime:
    parsed_date = date.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    return parsed_date

# Function for merging media ids of a list of documents into a unique media ids.
# This function will be used in the Retrieve agent tool implementation.
def merge_nodes_to_source(nodes: List[NodeWithScore]) -> List[str]:
    # https://docs.llamaindex.ai/en/stable/api/llama_index.schema.NodeWithScore.html#llama_index.schema.NodeWithScore.metadata
    source_dict: Dict[str, int] = {}
    # Counting the frequency of each media ID
    # eg.
    # {
    #     "1234": 3,
    #     "9875": 3
    # }
    for node in nodes:
        node_source = node.metadata.get("media_id", "_blank")
        if node_source in source_dict.keys():
            source_dict[node_source] += 1
        else:
            source_dict[node_source] = 1

    max_frequency = max(source_dict.values())

    max_frequency_keys = [key for key, value in source_dict.items() if value == max_frequency]

    return max_frequency_keys

# Generates a summary of the indexed document using Langchain Map Reduce algorithm.
# There are also other summarisation methods in Langchain.
# https://python.langchain.com/docs/use_cases/summarization
def generate_summary(text:str, openai_api_key:str):
    from langchain.chains.summarize import load_summarize_chain
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    llm = ChatOpenAI(temperature=0, openai_api_key =openai_api_key)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 20)
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

