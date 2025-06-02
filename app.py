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

app = FastAPI()

class ChatRequest(BaseModel):
    query:str

def retrieve_documents(query: str) -> str:
    """
    Gera a incorporação (embedding) da query e busca documentos relevantes no Pinecone.
    Retorna os textos dos documentos concatenados.
    """

    query_embedding = embeddings_model.embed_query(query)

    results = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )
    context_texts = [match.metadata['text'] for match in results.matches]
    return "\n\n".join(context_texts)

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "Você é um assistente prestativo para o SmartDevice X1. Use as seguintes informações de contexto para responder às perguntas do usuário. Se a pergunta não puder ser respondida com base no contexto fornecido, diga 'Desculpe, não consigo encontrar essa informação no manual do SmartDevice X1.' Não invente respostas. Contexto: {context}"),
        ("user", "{query}"),
    ]
)

# retrieve_documents -> prompt_template -> llm -> output_parser
rag_chain = (
    {"context": retrieve_documents, "query": RunnablePassthrough()}
    | prompt_template
    | llm
    | StrOutputParser()
)