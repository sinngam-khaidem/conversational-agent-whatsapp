import trafilatura
from langchain.docstore.document import Document
from duckduckgo_search import DDGS

# https://pypi.org/project/duckduckgo-search/#1-text---text-search-by-duckduckgocom
class DDGWrappper:
    def _get_content(self, url):
        downloaded = trafilatura.fetch_url(
                        url=url
                    )
        content = trafilatura.extract(downloaded)
        return content

    def quick_search(self, query: str, page_result_count: int = 4):
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(keywords = f"{query} -site:youtube.com", region="wt-wt", safesearch = "moderate", backend="api", max_results=page_result_count)]
            results_list = []
            # Structure of each result from the search results is as follow:
            # {
            #     "href": "......",
            #     "title": ".......",
            #     "body": "Summary of the webpage"
            # }
            # Document schema in LlamaIndex and Langchain are little different.
            # LlamaIndex document: Documet(text = "", metadata="")
            # Langchain document: Documet(page_content = "", metadata="")
            for result in results:
                link = result["href"]
                title = result["title"]
                content = result.get("body", "")
                doc = Document(page_content=content, metadata={"source": link, "title": title})
                results_list.append(doc)
            return results_list

if __name__ == "__main__":
    ddg = DDGWrappper()
    result = ddg.quick_search("Tech specifications of Macbook pro M3 2023 model.")
    for item in result:
        print(item.page_content)