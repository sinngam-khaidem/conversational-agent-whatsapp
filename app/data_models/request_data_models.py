from pydantic import BaseModel
from typing import Optional

class PdfFileRequest(BaseModel):
	filename: str
	media_id: str
	senders_wa_id: str
	caption: Optional[str] = "No caption"
	media_type: str
	mime_type: str

class ImageFileRequest(BaseModel):
	media_id: str
	senders_wa_id: str
	caption: Optional[str] = "No caption"
	media_type: str
	mime_type: str

class TextFileRequest(BaseModel):
	filename: str
	media_id: str
	senders_wa_id: str
	caption: Optional[str] = "No caption"
	media_type: str
	mime_type: str

class UrlRequest(BaseModel):
	url_address: str
	senders_wa_id: str
	caption: Optional[str] = "No caption"

class AgentCallRequest(BaseModel):
	message_body: str
	senders_wa_id: str