import os
from dotenv import load_dotenv
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAiEmbeddings
from pinecone import Pinecone, Index, PodSpec

load_dotenv()

OPEN_AI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_LEY = os.getenv("PINECOIN_API_KEY")
PINECONE_ENVIROMENT = os.getenv("PYNECONE_ENVIROMENT")