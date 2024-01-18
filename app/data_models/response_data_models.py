from pydantic import BaseModel, Field
from enum import Enum

class Status(str, Enum):
	SUCCESS = 'success'
	FAILURE = 'failure'

class EmbeddingResponse(BaseModel):
    """The Response for the Embedding endpoint."""

    status: Status = Field(Status.SUCCESS, title="Status", description="The status of the request.")
