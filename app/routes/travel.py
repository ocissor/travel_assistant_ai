from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
import sys 
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.graph import app_planner  # import your compiled LangGraph graph
import uuid 

app = FastAPI()

class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str]

@app.get("/")
async def chat_endpoint():

    return {"response": "Welcome to the Travel Assistant AI! How can I help you today?"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Append user message to state
    if request.thread_id is None:
        request.thread_id = str(uuid.uuid4())
    
    # Invoke the graph asynchronously with current state
    if request.user_input.strip() == "":
        input = {"messages": []}
    else:
        input = {"messages": [request.user_input]}

    config = {"configurable": {"thread_id": request.thread_id}}
    result = await app_planner.ainvoke(input, config=config)

    return {"response": result}

# Run with: uvicorn your_fastapi_file:app --reload
