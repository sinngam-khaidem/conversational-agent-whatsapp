import requests
import trafilatura
from langchain_core.embeddings import Embeddings
from langchain.text_splitter import TextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
import json
from duckduckgo_search import DDGS
import logging

class DDGWithVectorSearchWrappper:
    def __init__(
        self, 
        text_splitter: TextSplitter = RecursiveCharacterTextSplitter(
                chunk_size = 1024, 
                chunk_overlap = 30,
                separators = ["\n\n", "\n", ".", ""],
                length_function = len
            ),
        # embedding_model = TextEmbedding(model_name = "BAAI/bge-small-en-v1.5")
        ):

        self.text_splitter = text_splitter
        # self.embeddings = embedding_model

    def _get_content(self, url):
        downloaded = trafilatura.fetch_url(
                        url=url
                    )
        content = trafilatura.extract(downloaded)
        return content

    # def descriptive_search(self, query: str, page_result_count: int = 2, search_result_count: int = 4):
    #     with DDGS() as ddgs:
    #         results = [r for r in ddgs.text(keywords = f"{query} -site:youtube.com", region="wt-wt", safesearch = "moderate", backend="api", max_results=page_result_count)]
    #         results_list = []
            
    #         for result in results:
    #             link = result["href"]
    #             title = result["title"]
    #             raw_content = self._get_content(link)
    #             content = raw_content if raw_content else result.get("body", "")
    #             doc = Document(page_content=content, metadata={"source": link, "title": title})
    #             results_list.append(doc)

    #         logging.info(f"{len(results_list)} results in results_list")
    #         docs = self.text_splitter.split_documents(results_list)
    #         logging.info(f"Created {len(docs)} documents.")
    #         db = FAISS.from_documents(docs, self.embeddings)

    #         found_docs = db.similarity_search(query, k=search_result_count)
    #         return found_docs

    def quick_search(self, query: str, page_result_count: int = 4):
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(keywords = f"{query} -site:youtube.com", region="wt-wt", safesearch = "moderate", backend="api", max_results=page_result_count)]
            results_list = []
            
            for result in results:
                link = result["href"]
                title = result["title"]
                content = result.get("body", "")
                doc = Document(page_content=content, metadata={"source": link, "title": title})
                results_list.append(doc)

            return results_list

if __name__ == "__main__":
    ddg = DDGWithVectorSearchWrappper()
    result = ddg.quick_search("Tech specifications of Macbook pro M3 2023 model.")
    for item in result:
        print(item.page_content)