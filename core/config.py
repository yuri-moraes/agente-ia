import os
from dotenv import load_dotenv
from pydantic import SecretStr

load_dotenv()

class Settings:
    """
    Classe que centraliza todas as configurações da aplicação.
    Ela lê as variáveis do ambiente e as disponibiliza como atributos.
    """
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    secret_key = SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME: str = "smartdevice-manual"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MODEL: str = "gpt-4o"

settings = Settings()

if not settings.OPENAI_API_KEY or not settings.PINECONE_API_KEY:
    raise ValueError("Por favor, configure OPENAI_API_KEY e PINECONE_API_KEY no seu arquivo .env")