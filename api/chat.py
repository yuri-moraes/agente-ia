import traceback
from fastapi import APIRouter, HTTPException
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage

from schemas.chat import ChatRequest
from services.rag_service import chat_app, ChatState

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
)

@router.post("/")
async def chat_with_agent(request: ChatRequest):
    """
    Endpoint para conversar com o agente de IA com histórico.
    """
    try:
        config: RunnableConfig = {"configurable": {"thread_id": request.session_id}}
        
        input_state: ChatState = {
            "messages": [HumanMessage(content=request.query)],
            "context": "",
            "current_query": request.query
        }
        
        output = chat_app.invoke(input_state, config)
        
        messages = output.get("messages", [])
        response_content = messages[-1].content if messages else "Erro: Nenhuma resposta gerada"
        
        return {
            "answer": response_content,
            "context_found": bool(output.get("context", "")),
            "session_id": request.session_id
        }
        
    except Exception as e:
        print(f"Erro ao processar a requisição: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Endpoint para recuperar o histórico de uma conversa.
    """
    try:
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        state_snapshot = chat_app.get_state(config)
        
        if not state_snapshot or not state_snapshot.values:
            return {"session_id": session_id, "messages": [], "total_messages": 0}

        messages = state_snapshot.values.get("messages", [])
        formatted_messages = [
            {"content": msg.content, "type": "ai" if isinstance(msg, AIMessage) else "human"}
            for msg in messages
        ]
        
        return {
            "session_id": session_id,
            "messages": formatted_messages,
            "total_messages": len(formatted_messages)
        }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar histórico: {str(e)}")

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Endpoint para limpar o histórico de uma conversa.
    """
    try:
        config: RunnableConfig = {"configurable": {"thread_id": session_id}}
        chat_app.update_state(config, {"messages": []})
        return {"message": f"Histórico da sessão {session_id} foi limpo com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao limpar histórico: {str(e)}")