from typing import List, Union, Optional, Dict
from langchain.tools.base import BaseTool, Tool
from langchain_core.messages import (
        SystemMessage, 
        HumanMessage, 
        AIMessage,
        ToolMessage, 
        get_buffer_string
    )
from langchain_core.prompts.chat import (
        MessagesPlaceholder, 
        ChatPromptTemplate, 
        HumanMessagePromptTemplate, 
        BasePromptTemplate,

    )
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_functions_agent
import logging
import openai

from qdrant_client.http import models as qdrant_models
from langchain.globals import set_debug
set_debug(True)

from app.services.web_search_service.ddg_search_service import DDGWithVectorSearchWrappper
from app.services.databases.qdrant_setup import (
    build_sentence_window_index,
    build_sentence_window_query_engine,
    build_index_retriever,
    load_qdrant_connection
)
from app.services.databases.dynamodb_setup import DynamoDBSessionManagement
from app.services.service_utilities import (
        merge_nodes_to_source, 
        detect_and_extract_urls,
        shorten_url
    )
from app.services.general_utilities import (
        send_message,
        get_text_message_input,
        get_media_message_input
    )

class RealtyaiBot:
    def __init__(
        self,
        max_token_length: int = 1000,
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
            "Keep your answers very very short and extremely precise. If you do not know the answer, simply say so. DO NOT MAKE UP ANSWERS."),
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
        self.max_token_length = max_token_length
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
                description="Useful for when you need to answer questions about CURRENT EVENTS, CURRENT STATE OF THE WORLD, HEALTH, MEDICINE, CLIMATE, ENTERTAINMENT, and POP CULTURE."
            ),
            Tool(
                name="Rag",
                func=self._rag,
                description="Useful when you need to look for answers in documents, PDFs, text files, or webpages Human shared, when you are explicitly ask to do so.",
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

        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", openai_api_key=openai_api_key,max_tokens=128, temperature=0.1)

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
        return AgentExecutor(agent=agent, tools=tools, verbose=verbose, remember_intermediate_steps=False, max_iterations=3)

    # This is the main function that will generate the response of the conversation agent
    def __call__(self, user_input:str)-> str:
        final_answer = ""
        try:
            citations_to_append = ""
            unique_citations = set()

            # Retreive the chat interactions of the user from DynamoDB
            chat_history = self.dynamodb.messages()
            last_few_chat_interactions = chat_history[-6:]
            pruned_messages = self._prune_long_messages(last_few_chat_interactions)

            response = self.agent_executor.invoke({"input": user_input, "history": pruned_messages})

            # Append the new interactions to dynamoDB
            self.dynamodb.add_message(HumanMessage(content=user_input))
            self.dynamodb.add_message(AIMessage(content=response["output"]))

            for item in self.citations:
                unique_citations.add(item)
            for i, item in enumerate(unique_citations):
                citations_to_append += f"{i+1}. {item}\n"

            final_answer = f"""{response["output"]}\n\n{citations_to_append}"""
            # print(final_answer)
            return final_answer
        except Exception as e:
            logging.error(f"An error occurred in response call: {e}")
            

    def _rag(self, query:str) -> str:
        try:
            send_message(
                get_text_message_input(self.senders_wa_id, f"_Retrieval Augmented Generation_ about *{query}*...."), 
                self.whatsapp_version, 
                self.whatsapp_access_token, 
                self.whatsapp_phone_number_id
            )
        except Exception as e:
            logging.error(f"An error occurred while sending status update message of rag tool: {e}")

        try:
            sentence_query_engine = build_sentence_window_query_engine(
                self.senders_wa_id, 
                self.cohere_api_key, 
                self.openai_api_key, 
                self.qdrant_url, 
                self.qdrant_api_key, 
                self.qdrant_collection_name
            )
            window_response = sentence_query_engine.query(query)

            for node in window_response.source_nodes:
                if len(self.citations) < 2:
                    self.citations.append(node.metadata.get("source", "_blank"))
            return str(window_response.response)
        except Exception as e:
            logging.error(f"An error occurred in the rag tool: {e}")
            return "_Failed the Rag._"
            

    def _search(self, query:str) -> str:
        try:
            send_message(
                get_text_message_input(self.senders_wa_id, f"_Searching about_ *{query}*...."),
                self.whatsapp_version, 
                self.whatsapp_access_token, 
                self.whatsapp_phone_number_id
            )
        except Exception as e:
            logging.error(f"An error occurred while sending status update message of search tool: {e}")

        try:
            result_str = ""
            docs = DDGWithVectorSearchWrappper().quick_search(query, page_result_count=4)
            for doc in docs:
                result_str += "\n"+doc.page_content+"\n"
                # if len(self.citations) < 2:
                #     self.citations.append(shorten_url(doc.metadata.get("source", "")))
            self.dynamodb.add_message(SystemMessage(content=f"These contexts might help you:\n\n{result_str}"))
            return result_str
        except Exception as e:
            logging.error(f"An error occurred in the Search tool: {e}")
            return "_Failed the search._"
    
    def _retrieve(self, query: str):
        docs = []
        try:
            send_message(
                get_text_message_input(self.senders_wa_id, f"_Retrieving resources about_ *{query}*...."), 
                self.whatsapp_version, 
                self.whatsapp_access_token, 
                self.whatsapp_phone_number_id
            )
        except Exception as e:
            logging.error(f"An error occurred whike sending status update message of retrieve tool: {e}")
        try:
            node_retriever = build_index_retriever(
                self.senders_wa_id,
                self.cohere_api_key, 
                self.openai_api_key, 
                self.qdrant_url, 
                self.qdrant_api_key, 
                self.qdrant_collection_name
            )
            nodes = node_retriever.retrieve(str_or_query_bundle=query)
            print(nodes)
            final_media_ids = merge_nodes_to_source(nodes)
            print(final_media_ids)
            if len(final_media_ids)>0:
                for each_id in final_media_ids:
                    if each_id != "_blank":
                        check_urls = detect_and_extract_urls(each_id)
                        if len(check_urls) > 0:
                            try:
                                send_message(
                                    get_text_message_input(self.senders_wa_id, each_id, preview_url=True),
                                    self.whatsapp_version, 
                                    self.whatsapp_access_token, 
                                    self.whatsapp_phone_number_id
                                )
                            except Exception as e:
                                logging.error("An error occurred while sending the url: {e}")
                        else:
                            try:
                                send_message(
                                    get_media_message_input(self.senders_wa_id, each_id),
                                    self.whatsapp_version, 
                                    self.whatsapp_access_token, 
                                    self.whatsapp_phone_number_id
                                )
                            except Exception as e:
                                logging.error("An error occurred while sending the media file: {e}")                        
                return "_Retrieved successfully_"
            else:
                return "_No relevant resources found._"
        except Exception as e:
            logging.error(f"An error occurred in the retrieve tool: {e}")
            return "_Failed the retrieval_"
    def _prune_long_messages(self, messages):
        curr_buffer_length = self.llm.get_num_tokens_from_messages(messages)
        if curr_buffer_length > self.max_token_length:
            while curr_buffer_length > self.max_token_length:
                messages.pop(0)
                curr_buffer_length = self.llm.get_num_tokens_from_messages(messages)
        return messages

            

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
