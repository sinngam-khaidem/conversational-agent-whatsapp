from typing import List, Union, Optional, Dict
from langchain.tools.base import BaseTool, Tool
from langchain_core.messages import (
        SystemMessage, 
        HumanMessage, 
        AIMessage, 
        get_buffer_string
    )
from langchain_core.prompts.chat import (
        MessagesPlaceholder, 
        ChatPromptTemplate, 
        HumanMessagePromptTemplate, 
        BasePromptTemplate
    )
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
import logging
import openai
from langchain.globals import set_debug
set_debug(False)

from app.services.web_search_service.ddg_search_service import DDGWithVectorSearchWrappper
from app.services.databases.qdrant_setup import (
    build_sentence_window_index,
    build_sentence_window_query_engine,
    load_qdrant_connection
)
from app.services.databases.dynamodb_setup import DynamoDBSessionManagement
from app.services.service_utilities import (
        merge_docs_to_source, 
        detect_and_extract_urls
    )
from app.general_utilities import (
        send_message,
        get_text_message_input,
        get_media_message_input
    )

class RealtyaiBot:
    def __init__(
        self,
        senders_wa_id: str = None,
        openai_api_key: str = None,
        cohere_api_key:str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        qdrant_api_key: str = None,
        qdrant_url:str = None,
        qdrant_collection_name:str = None,
        whatsapp_version: str = None,
        whatsapp_access_token: str = None,
        whatsapp_phone_number_id: str = None,
        dynamo_db_table_name: str = None,
        system_message: str = ("You are an AI personal assistant, specialised in all things retrieval and search."
            "Do your best to answer the questions at the end. Feel free to use any tools available to look up relevant information," 
            "only if necessary. Ask follow-up questions in case of vague or unclear questions, to get more information about what is being asked."
            "Keep your answers short and precise."),
        verbose: bool = True,
    ):  
        self.openai_api_key = openai_api_key
        self.cohere_api_key = cohere_api_key
        self.qdrant_url = qdrant_url
        self.qdrant_api_key = qdrant_api_key
        self.qdrant_collection_name = qdrant_collection_name
        self.whatsapp_version = whatsapp_version
        self.whatsapp_access_token = whatsapp_access_token
        self.whatsapp_phone_number_id = whatsapp_phone_number_id
        # Define 2 important state variables
        self.senders_wa_id = senders_wa_id
        self.citations = []

        # Define prompt for the conversation agent
        self.prompt = ChatPromptTemplate(
            messages = [
                SystemMessage(content=system_message),
                MessagesPlaceholder(variable_name = "history"),
                HumanMessagePromptTemplate.from_template("{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ]
        )

        # Define tools that can be used by the OpenaiFunctionsAgent
        self.tools = [
            Tool(
                name="Search",
                func=self._search,
                description="Useful for when you need to answer questions about current events, current state of the world, health, medicine and pop culture. This is your default tool, until told otherwise."
            ),
            Tool(
                name="Rag",
                func=self._rag,
                description="Useful when you need to look for answers in documents, pdfs, text files, or webpages user shared in the past, and perform Retrieval Augmented Generation(RAG).",
                return_direct="True"
            ),
            # https://stackoverflow.com/questions/76364591/langchain-terminating-a-chain-on-specific-tool-output
            Tool(
                name="Retrieve",
                func=self._retrieve,
                description="Useful when you are asked to retrieve or user wants you to send him Files, PDFs, text files, URLs etc.",
                return_direct = "True"
            ),

        ]

        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key,max_tokens=256, temperature=0.1)

        # Create an instance of the DynamoDBSessionManagement to handle chat history, number of interaction etc.abs
        self.dynamodb = DynamoDBSessionManagement(
                table_name=dynamo_db_table_name,
                session_id=senders_wa_id,
                aws_access_key_id = aws_access_key_id,
                aws_secret_access_key= aws_secret_access_key
            )
        # Create an instance of the agent executor
        self.agent_executor = self._create_agent_executor(self.llm, self.prompt, self.tools, verbose=verbose)
    
    def _create_agent_executor(self, llm: ChatOpenAI, prompt: BasePromptTemplate, tools: List[Tool], verbose: bool = False, return_intermediate_steps:bool = True):        
        # Create an instance of the OpenaiFunctionsAgent
        agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)
        # Create an instance of the runtime of the agent
        return AgentExecutor(agent=agent, tools=tools, verbose=verbose, remember_intermediate_steps=False)

    # This is the main function that will generate the response of the conversation agent
    def __call__(self, user_input:str)-> str:
        final_answer = ""
        try:
            citations_to_append = ""
            unique_citations = set()

            # Retreive the chat interactions of the user from DynamoDB
            chat_history = self.dynamodb.messages()
            last_few_chat_interactions = chat_history[-2:]
            response = self.agent_executor.invoke({"input": user_input, "history": last_few_chat_interactions})

            print(response["output"])
            # Append the new interactions to dynamoDB
            self.dynamodb.add_message(HumanMessage(content = user_input))
            self.dynamodb.add_message(AIMessage(content=response["output"]))

            for item in self.citations:
                unique_citations.add(item)
            for i, item in enumerate(unique_citations):
                citations_to_append += f"{i+1}. {item}\n"

            final_answer = f"""{response["output"]}\n\n{citations_to_append}"""
            return final_answer
        except Exception as e:
            logging.error(f"An error occurred in response call: {e}")
            

    def _rag(self, query:str) -> str:
        try:
            send_message(
                get_text_message_input(self.senders_wa_id, f"Running *Retrieval Augmented Generation*📄 with the query _{query}_...."), 
                self.whatsapp_version, 
                self.whatsapp_access_token, 
                self.whatsapp_phone_number_id
            )

            sentence_query_engine = build_sentence_window_query_engine(self.senders_wa_id, self.cohere_api_key, self.openai_api_key, self.qdrant_url, self.qdrant_api_key, self.qdrant_collection_name)
            window_response = sentence_query_engine.query(query)

            for node in window_response.source_nodes:
                self.citations.append(node.metadata.get("source", "_blank"))
            return str(window_response.response)
        except Exception as e:
            logging.error(f"An error occurred in the rag tool: {e}")
            

    def _search(self, query:str) -> str:
        send_message(
            get_text_message_input(self.senders_wa_id, f"Running *Search*🌐 with the query _{query}_.... "),
            self.whatsapp_version, 
            self.whatsapp_access_token, 
            self.whatsapp_phone_number_id
        )

        try:
            result_str = ""
            docs = DDGWithVectorSearchWrappper().quick_search(query, page_result_count=4)
            for doc in docs:
                result_str += "\n"+doc.page_content+"\n"
                self.citations.append(doc.metadata.get("source", "_blank"))
            return result_str
        except Exception as e:
            logging.error(f"An error occurred in the Search tool: {e}")
    
    def _retrieve(self, query: str):
        docs = []
        try:
            send_message(
                get_text_message_input(self.senders_wa_id, f"Running *Retrieve* with the query _{query}_...."), 
                self.whatsapp_version, 
                self.whatsapp_access_token, 
                self.whatsapp_phone_number_id
            )
            qdrant_index = load_qdrant_connection(self.qdrant_url, self.qdrant_api_key, self.qdrant_collecion_name)
            docs = qdrant_index.similarity_search(query, 
                                                k=5,
                                                filter=qdrant_models.Filter(
                                                    must=[
                                                        qdrant_models.FieldCondition(
                                                            key="metadata.group_id",
                                                            match=qdrant_models.MatchValue(value=self.senders_wa_id),
                                                        )
                                                    ]
                                                )
                                                )
            final_media_ids = merge_docs_to_source(docs)
            for each_id in final_media_ids:
                if each_id != "_blank":
                    check_urls = detect_and_extract_urls(each_id)
                    if len(check_urls) > 0:
                        send_message(
                            get_text_message_input(self.senders_wa_id, each_id, preview_url=True),
                            self.whatsapp_version, 
                            self.whatsapp_access_token, 
                            self.whatsapp_phone_number_id
                        )
                    else:
                        send_message(
                            get_media_message_input(self.senders_wa_id, each_id),
                            self.whatsapp_version, 
                            self.whatsapp_access_token, 
                            self.whatsapp_phone_number_id
                        )
            return "_Retrieved successfully_"
        except Exception as e:
            logging.error(f"An error occurred in the retrieve tool: {e}")

            

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    bot = RealtyaiBot(
            "919089342948", 
            os.getenv("OPENAI_API_KEY"), 
            os.getenv("AWS_ACCESS_KEY_ID"), 
            os.getenv("AWS_SECRET_ACCESS_KEY"),
            os.getenv("QDRANT_API_KEY"),
            os.getenv("QDRANT_URL"),
            os.getenv("QDRANT_COLLECTION_NAME"),
            os.getenv("WHATSAPP_VERSION"),
            os.getenv("WHATSAPP_ACCESS_TOKEN")
        )