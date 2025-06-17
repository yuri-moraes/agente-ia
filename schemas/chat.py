from pydantic import BaseModel

class ChatRequest(BaseModel):
    """
    Modelo para a requisição do endpoint de chat.
    Define que cada requisição deve ter um 'query' (string) e um 'session_id' (string).
    """
    query: str
    session_id: str