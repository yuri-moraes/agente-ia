import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from pinecone import Pinecone
from pinecone.db_data.models import QueryResponse, ScoredVector
from pinecone.exceptions import NotFoundException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from typing import List, cast
from pydantic import SecretStr 
import traceback
from fastapi.middleware.cors import CORSMiddleware

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

origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

def retrieve_documents(query: str) -> str:
    """
    Gera a incorporação (embedding) da query e busca documentos relevantes no Pinecone.
    Retorna os textos dos documentos concatenados.
    """

    query_embedding = embeddings_model.embed_query(query)

    query_return_value = index.query(
        vector=query_embedding,
        top_k=3,
        include_metadata=True
    )

    context_texts: List[str] = []

    if isinstance(query_return_value, QueryResponse):
        results: QueryResponse = query_return_value

        try:
            typed_matches = cast(List[ScoredVector], results.matches)

            if typed_matches:
                for match in typed_matches:
                    current_match_metadata = match.metadata 

                    if current_match_metadata and isinstance(current_match_metadata, dict) and 'text' in current_match_metadata:
                        text_content = current_match_metadata.get('text')
                        if isinstance(text_content, str):
                            context_texts.append(text_content)
        except AttributeError as e_attr:
            print(f"Alerta: Erro de atributo ao acessar 'results.matches' ou 'match.metadata'. Detalhes: {e_attr}")
        except Exception as e_process:
            print(f"Alerta: Erro inesperado ao processar os matches: {e_process}")

    else:
        print(f"Alerta: index.query() retornou um tipo inesperado: {type(query_return_value)}. Conteúdo: {query_return_value}")

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
class ChatRequest(BaseModel):
    query:str

@app.post("/chat")
async def chat_with_agente(request: ChatRequest):
    """
    Endpoint para conversar com o agente de IA.
    Recebe uma pergunta e retorna a resposta gerada.
    """
    try:
        response = rag_chain.invoke(request.query)
        return {"answer": response}
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )