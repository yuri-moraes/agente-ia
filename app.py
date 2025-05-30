import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone
from pinecone.exceptions import NotFoundException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from typing import List, Dict
from pydantic import SecretStr 

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY or not PINECONE_API_KEY:
    raise ValueError("Por favor, configure OPENAI_API_KEY, PINECONE_API_KEY no seu arquivo .env")

pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "smartdevice-manual"
EMBEDDING_DIMENSION = 1536

try:
    pc.describe_index(INDEX_NAME)
    print(f"Conectado ao índice Pinecone '{INDEX_NAME}'.")
except NotFoundException:
    raise RuntimeError(f"O índice {INDEX_NAME} não foi encontrado. Por favor execute 'ingest_data.py' primeiro para criá-lo e popular")

index = pc.Index(INDEX_NAME)

secret_key = SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
embeddings_model = OpenAIEmbeddings(api_key=secret_key, model="text-embedding-ada-002")

llm = ChatOpenAI(api_key=secret_key, model="gpt-4o")