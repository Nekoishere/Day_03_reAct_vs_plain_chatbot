import os
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider
from src.chatbot.chatbot import BaselineChatbot
from src.agent.agent import ReActAgent
from src.tools.football_tools import FOOTBALL_TOOLS

app = FastAPI(
    title="Football AI Agent API",
    description="REST API for the Football ReAct Agent and Baseline Chatbot",
    version="1.0.0"
)

def build_llm():
    provider = os.getenv("DEFAULT_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-4o")

    if provider == "openai":
        return OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    elif provider == "google":
        return GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Initialize LLM and Agent once at startup for efficiency
try:
    _llm = build_llm()
    baseline_bot = BaselineChatbot(_llm)
    react_agent = ReActAgent(_llm, tools=FOOTBALL_TOOLS, max_steps=6)
except Exception as e:
    print(f"Warning: Failed to initialize LLM/Agent on startup: {e}")
    baseline_bot = None
    react_agent = None


class ChatRequest(BaseModel):
    message: str
    mode: str = "react"  # 'react' or 'baseline'

class ChatResponse(BaseModel):
    answer: str
    mode_used: str


llm_lock = threading.Lock()

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        with llm_lock:
            if request.mode == "baseline":
                if not baseline_bot:
                    raise HTTPException(status_code=500, detail="Baseline bot not initialized properly")
                answer = baseline_bot.chat(request.message)
                return ChatResponse(answer=answer, mode_used="baseline")
                
            elif request.mode == "react":
                if not react_agent:
                    raise HTTPException(status_code=500, detail="ReAct agent not initialized properly")
                answer = react_agent.run(request.message)
                return ChatResponse(answer=answer, mode_used="react")
                
            else:
                raise HTTPException(status_code=400, detail="Invalid mode. Choose 'react' or 'baseline'.")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "provider": os.getenv("DEFAULT_PROVIDER", "openai")}

if __name__ == "__main__":
    import uvicorn
    # Make it runnable standardly
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
