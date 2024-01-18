from typing import List
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
    messages_to_dict,
    AIMessage,
    HumanMessage
)
import logging
from langchain_core.chat_history import BaseChatMessageHistory

class DynamoDBSessionManagement:
  def __init__(
      self,
      table_name: str,
      session_id: str,
      aws_access_key_id: str,
      aws_secret_access_key: str,
      primary_key_name: str = "SessionId",
      region_name: str = "ap-south-1"
      ):
    try:
      import boto3
    except ImportError as e:
      raise ImportError(
          "Unable to import boto3, please install with `pip install boto3`"
      ) from e
    client = boto3.resource('dynamodb', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
    self.table = client.Table(table_name)
    self.session_id = session_id
    self.key = {primary_key_name: session_id}


  def messages(self) -> List[BaseMessage]:
    """Retrieve Messages from DynamoDB"""
    response = None
    try:
      response = self.table.get_item(Key=self.key)
    except Exception as e:
      logging.error(f"Error retrieving messages from dynamoDB: {e}")
    if response and "Item" in response:
      items = response["Item"]["History"]
    else:
      items = []
    messages = messages_from_dict(items)
    return messages
  
  def add_message(self, message: BaseMessage) -> None:
     """Append the message to the record in DynamoDB"""
     messages = messages_to_dict(self.messages())
     _message = message_to_dict(message)
     messages.append(_message)
     try:
        self.table.put_item(Item={**self.key, "History": messages})
     except Exception as e:
        logging.error(f"Error adding message to DynamoDB: {e}")
  
  def clear(self) -> None:
    """Clear session memory from dynamoDB"""
    try:
      self.table.delete_item(Key=self.key)
    except Exception as e:
      logging.error(f"Error clearing session memory from dynamoDB: {e}")

    

