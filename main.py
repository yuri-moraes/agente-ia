import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from pinecone import Pinecone, PodSpec
from pinecone.exceptions import NotFoundException
from pydantic import SecretStr 

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY") 
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT") 

if not OPENAI_API_KEY or not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
    raise ValueError("Configure corretamente suas variáveis de ambiente")

pc = Pinecone(api_key=PINECONE_API_KEY) 

INDEX_NAME = "smartdevice-manual"
EMBEDDING_DIMENSION = 1536

try:
    pc.describe_index(INDEX_NAME)
    print(f"Índice '{INDEX_NAME}' já existe.")
except NotFoundException: 
    print(f"Criando novo índice no Pinecone: {INDEX_NAME}...")
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBEDDING_DIMENSION,
        metric='cosine',
        spec=PodSpec(environment=PINECONE_ENVIRONMENT) 
    )
    print(f"Índice '{INDEX_NAME}' criado com sucesso.")

index = pc.Index(INDEX_NAME)

def process_pdf_to_chunks(pdf_path: str):
    """
    Lê um arquivo PDF, extrai o texto e o divide em chunks.
    """
    print(f"Lendo o arquivo PDF: {pdf_path}...") 
    reader = PdfReader(pdf_path)
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n" 

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,     
        chunk_overlap=200,  
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.create_documents([full_text])
    print(f"PDF processado. Total de chunks criados: {len(chunks)}") 
    return chunks


def embed_and_upsert_to_pinecone(chunks, index):
    """
    Gera embeddings para os chunks e os insere no Pinecone.
    """
    print("Gerando embeddings e inserindo no Pinecone...")
    secrect_key = SecretStr(OPENAI_API_KEY) if OPENAI_API_KEY else None
    embeddings_model = OpenAIEmbeddings(api_key=secrect_key, model="text-embedding-ada-002")

    batch_size = 100 
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts_to_embed = [chunk.page_content for chunk in batch]
        ids = [f"chunk-{i + j}" for j, chunk in enumerate(batch)]

        embeds = embeddings_model.embed_documents(texts_to_embed)

        to_upsert = [(ids[j], embeds[j], {"text": texts_to_embed[j]}) for j in range(len(batch))]

        index.upsert(vectors=to_upsert)
        print(f"Inseridos {len(batch)} chunks no Pinecone (total até agora: {i + len(batch)})")

    print("Processamento completo! Todos os chunks foram inseridos no Pinecone.")

if __name__ == "__main__":
    pdf_file_path = "manual_do_produto.pdf"

    if not os.path.exists(pdf_file_path):
        print(f"Erro: O arquivo '{pdf_file_path}' não foi encontrado.") 
        print("Por favor, coloque o 'manual_do_produto.pdf' na mesma pasta do 'main.py' ou forneça o caminho correto.")
    else:
        document_chunks = process_pdf_to_chunks(pdf_file_path)

        embed_and_upsert_to_pinecone(document_chunks, index)