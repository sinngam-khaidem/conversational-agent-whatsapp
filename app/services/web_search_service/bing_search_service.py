import requests
import trafilatura
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.text_splitter import TextSplitter, RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document
import logging


class BingWithVectorSearchWrappper:
    def __init__(
        self, 
        subscription_key:str, 
        text_splitter: TextSplitter = RecursiveCharacterTextSplitter(
                chunk_size = 1024, 
                chunk_overlap = 30,
                separators = ["\n\n", "\n", ".", ""],
                length_function = len
            ),
        embeddings = FastEmbedEmbeddings(model_name = "BAAI/bge-small-en-v1.5")
        ):

        self.subscription_key = subscription_key
        self.text_splitter = text_splitter
        self.embeddings = embeddings

    def _get_content(self, url):
        downloaded = trafilatura.fetch_url(
                        url=url
                    )
        content = trafilatura.extract(downloaded)
        return content

    def descriptive_search(self, query: str, page_result_count: int = 2, search_result_count: int = 4):
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
        params = {
            "q": f"{query} -site:youtube.com",
            "count": page_result_count,
            "cc": "IN",
            "mkt": "en-IN",
            "responseFilter": "Webpages",
            "textDecorations": True,
            "textFormat": "HTML"
        }
        response = requests.get(endpoint, headers=headers, params=params)
        search_results = response.json().get("webPages", {}).get("value", [])
        results_list = []
        for result in search_results:
            link = result.get("url", "")
            title = result.get("name", "")
            raw_content = self._get_content(link)
            content = raw_content if raw_content else result.get("snippet", "")

            doc = Document(page_content=content, metadata={"source": link, "title": title})
            results_list.append(doc)

        logging.info(f"{len(results_list)} results in bing search results_list")

        docs = self.text_splitter.split_documents(results_list)
        logging.info(f"Created {len(docs)} documents from the bing search.")

        db = FAISS.from_documents(docs, self.embeddings)

        found_docs = db.similarity_search(query, k=search_result_count)
        return found_docs

    def quick_search(self, query: str, page_result_count: int = 4):
        endpoint = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.subscription_key}
        params = {
            "q": f"{query} -site:youtube.com",
            "count": page_result_count,
            "cc": "IN",
            "mkt": "en-IN",
            "responseFilter": "Webpages",
            "textDecorations": True,
            "textFormat": "HTML"
        }
        response = requests.get(endpoint, headers=headers, params=params)
        search_results = response.json().get("webPages", {}).get("value", [])
        results_list = []
        for result in search_results:
            link = result.get("url", "")
            title = result.get("name", "")
            content = result.get("snippet", "")
            doc = Document(page_content=content, metadata={"source": link, "title": title})
            results_list.append(doc)
        return results_list

if __name__ == "__main__":
    pass