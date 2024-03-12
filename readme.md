# Realtyai-bot
This is a conversation agent powered by OpenAI, Langchain, and Qdrant vector database.
The agent has access to three tools(currently): Web Search tool, RAG(Retrieval Augmented Generation) tool to answer questions from PDFs and links that you shared, and  Retrieval tool for those PDFs and links.

![DEMO](Resources/diagrams/realtyai-bot.PNG)

## Things you can do with the bot
### 1. Web Search 
You can ask the bot to Search or Lookup for specific queries by asking for it using prompts like "Search for tech specifications of IPAD 9th gen. Summarise your answer in 3 points." or "Lookup how Conversational Retrieval Agent Works in Langchain." Using keywords like 'Search' or 'Lookup' is recommended to incline the bot more into using the Web Search tool. The bot will retrieve webpages straight from the internet, scrape the contents of those webpages, and answer with any relevant infomations it manages to find. In the occasion where those keywords are omitted from the prompt, the bot will still use the search tool, if the prompt is related to current events or current state of the world.

### 2. Retreival Augmented Generation
In order to use this tool, we need to provide/share the bot with some resource/materials before prompting. This resource could be a PDF file or a link. Share atleast one resource first, preferably with a caption. **DO NOT write your prompt in the caption field of your media. The bot will not use it as a prompt or a question. It will simply use it as a filename, in case the file you shared is unnamed. !!!** The bot will take some time to process your document. It will inform you once it's done.

Once your document/link is properly proceessed, you can start asking questions from it. Using the keyword "Rag"(not case sensitive) is strongly recommended here to incline the bot to answer from the documents you shared. Some example prompts include "Rag about how to write a good letter of recommendation." or "Rag about the different components of Logistic Regression". You can also try prompts like "Answer from my documents about the different components of Logistic Regression" or "I shared some documents about Graduate School Talk before. What does it say about writing a good letter of recommendation.". 

### 3. File/URL Retrieval
This is another tool you can use to retrieve the files/URL that you shared back. Use keywords like "Retrieve" to trigger this tool. Example prompts include "Retrieve my file on logistic regression" of "Send me back my file on logistic regression". This could be useful tool for bookmarking links or files, and retrieving them through natural language.

# Running it on your system
## Prerequisites:
1. [A Meta for developer account and Whatsapp Business app.](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
2. [A free instance of Qdrant Cloud Cluster.](https://qdrant.tech/documentation/cloud/quickstart-cloud/)
3. Cohere API key.
4. [⁠Ngrok installed on your system.](https://ngrok.com/docs/getting-started/)
5. OpenAI API key.
6. ⁠A working AWS account.

## Steps
1. Create a clone of the repostitory on your local machine using the following command.
```
git clone https://github.com/sinngam-khaidem/Realtyai-Whatsapp-Conversation-Agent.git
```
2. Inside the project directory, create a python virtual environment.
For **Windows**,
```
python -m venv myvenv
```
For **Unix/MacOS**,
```
python3 -m venv myvenv
```
3. Activate the python virtual environment we just created.
For **Windows**,
```
myvenv\Scripts\activate
```
For **Unix/MacOS**,
```
source myvenv/bin/activate
```
4. Install the required packages using the following command.
```
pip install -r requirements.txt
```
or
```
pip3 install -r requirements.txt
```