from typing import List, cast
from pinecone import Pinecone
from pinecone.db_data.models import QueryResponse, ScoredVector
from pinecone.exceptions import NotFoundException
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr
from core.config import settings

try:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)

    embeddings_model = OpenAIEmbeddings(api_key=settings.secret_key, model="text-embedding-ada-002")

    index = pc.Index(settings.PINECONE_INDEX_NAME)
    
    index.describe_index_stats()
    print(f"Conectado ao índice Pinecone '{settings.PINECONE_INDEX_NAME}'.")
except NotFoundException:
    raise RuntimeError(f"O índice {settings.PINECONE_INDEX_NAME} não foi encontrado.")
except Exception as e:
    raise RuntimeError(f"Erro ao inicializar serviços: {e}")


def retrieve_documents(query: str) -> str:
    """
    Gera a incorporação (embedding) da query e busca documentos relevantes no Pinecone.
    Retorna os textos dos documentos concatenados.
    
    Args:
        query: A pergunta do usuário.

    Returns:
        Uma string contendo o contexto encontrado, com documentos separados por duas quebras de linha.
    """
    try:
        query_embedding = embeddings_model.embed_query(query)

        query_return_value = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )

        context_texts: List[str] = []
        
        if isinstance(query_return_value, QueryResponse):
            typed_matches = cast(List[ScoredVector], query_return_value.matches)
            for match in typed_matches:
                if match.metadata and 'text' in match.metadata:
                    context_texts.append(str(match.metadata['text']))
        
        return "\n\n".join(context_texts)
    
    except Exception as e:
        print(f"Erro ao buscar documentos no Pinecone: {e}")
        return ""