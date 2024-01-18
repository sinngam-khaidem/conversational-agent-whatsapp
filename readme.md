# Realtyai-bot
This is a conversation agent powered by OpenAI, Langchain, and Qdrant vector database.
The agent has access to three tools(currently): Web Search tool, RAG(Retrieval Augmented Generation) tool to answer questions from PDFs and links that you shared, and  Retrieval tool for those PDFs and links.

![DEMO](Resources/diagrams/realtyai-bot.jpg)

## Things you can do with the bot
### 1. Web Search 
You can ask the bot to Search or Lookup for specific queries by asking for it using prompts like "Search for tech specifications of IPAD 9th gen. Summarise your answer in 3 points." or "Lookup how Conversational Retrieval Agent Works in Langchain." Using keywords like 'Search' or 'Lookup' is recommended to incline the bot more into using the Web Search tool. The bot will retrieve webpages straight from the internet, scrape the contents of those webpages, and answer with any relevant infomations it manages to find. In the occasion where those keywords are omitted from the prompt, the bot will still use the search tool, if the prompt is related to current events or current state of the world.

### 2. Retreival Augmented Generation
In order to use this tool, we need to provide/share the bot with some resource/materials before prompting. This resource could be a PDF file or a link. Share atleast one resource first, preferably with a caption. **DO NOT write your prompt in the caption field of your media. The bot will not use it as a prompt or a question. It will simply use it as a filename, in case the file you shared is unnamed. !!!** The bot will take some time to process your document. It will inform you once it's done.

Once your document/link is properly proceessed, you can start asking questions from it. Using the keyword "Rag"(not case sensitive) is strongly recommended here to incline the bot to answer from the documents you shared. Some example prompts include "Rag about how to write a good letter of recommendation." or "Rag about the different components of Logistic Regression". You can also try prompts like "Answer from my documents about the different components of Logistic Regression" or "I shared some documents about Graduate School Talk before. What does it say about writing a good letter of recommendation.". 

### 3. File/URL Retrieval
This is another tool you can use to retrieve the files/URL that you shared back. Use keywords like "Retrieve" to trigger this tool. Example prompts include "Retrieve my file on logistic regression" of "Send me back my file on logistic regression". This could be useful tool for bookmarking links or files, and retrieving them through natural language.


### Handling Media Message
