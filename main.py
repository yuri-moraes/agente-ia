import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings 
from pinecone import Pinecone, PodSpec, NotFoundError

load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_LEY = os.getenv("PINECOIN_API_KEY")
PINECONE_ENVIROMENT = os.getenv("PYNECONE_ENVIROMENT")

if not OPEN_AI_API_KEY or not PINECONE_API_LEY or not PINECONE_ENVIROMENT:
    raise ValueError("Configure corretamente suas variáveis de ambiente")

pc = Pinecone(api_key=PINECONE_API_LEY, enviroment=PINECONE_ENVIROMENT)

INDEX_NAME = "smartdevide-manul"
EMBEDDING_DIMENSION = 1536

try:
    pc.describe_index(INDEX_NAME)
    print(f"Índice {INDEX_NAME} já existe.")
except NotFoundError:
    print(f"Criando novo índice no Pinecone: {INDEX_NAME}...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric="cosine",
        spec=PodSpec(environment=PINECONE_ENVIROMENT)
    )
    print(f"Índice {INDEX_NAME} criado com sucesso!")


index = pc.Index(INDEX_NAME)