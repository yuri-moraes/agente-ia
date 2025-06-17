from typing import Sequence, Dict, Any, TypedDict
from typing_extensions import Annotated
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, add_messages
from langgraph.checkpoint.memory import MemorySaver
from core.config import settings
from services.pinecone_service import retrieve_documents

class ChatState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    context: str
    current_query: str

llm = ChatOpenAI(api_key=settings.secret_key, model=settings.LLM_MODEL)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Você é um assistente prestativo para o SmartDevice X1 com memória completa das conversas.

    Use as seguintes informações de contexto para responder às perguntas do usuário: 
    {context}

    INSTRUÇÕES IMPORTANTES:
    1. SEMPRE consulte o histórico completo da conversa antes de responder.
    2. Se o usuário perguntar sobre algo que já foi discutido, refira-se especificamente à conversa anterior.
    3. Mantenha consistência com todas as respostas anteriores.
    4. Se a pergunta não puder ser respondida com base no contexto fornecido, diga 'Desculpe, não consigo encontrar essa informação no manual do SmartDevice X1.'
    5. Seja conversacional e demonstre que você lembra das interações anteriores."""),
        MessagesPlaceholder(variable_name="messages"),
    ])

rag_chain = prompt_template | llm | StrOutputParser()

def call_rag_model(state: ChatState) -> Dict[str, Any]:
    last_message = state["messages"][-1]
    current_query = str(last_message.content)
    
    context = retrieve_documents(current_query)
    
    response = rag_chain.invoke({
        "context": context,
        "messages": state["messages"]
    })
    
    return {
        "messages": [AIMessage(content=response)],
        "context": context,
        "current_query": current_query
    }

def get_chat_app():
    """
    Função que constrói e compila o aplicativo de chat LangGraph.
    Isso encapsula a criação do workflow.
    """
    workflow = StateGraph(state_schema=ChatState)
    workflow.add_node("rag_model", call_rag_model)
    workflow.add_edge(START, "rag_model")
    
    memory = MemorySaver()
    
    return workflow.compile(checkpointer=memory)

chat_app = get_chat_app()