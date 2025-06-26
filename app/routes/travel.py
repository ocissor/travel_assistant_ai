from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import Optional
from langchain_core.messages import HumanMessage
import sys 
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.graph import app_planner  # import your compiled LangGraph graph
import uuid 
import pickle
from fastapi.responses import StreamingResponse

conversation_histories = {}

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
    
    if request.thread_id not in conversation_histories.keys():
        conversation_histories[request.thread_id] = []

    previous_messages = conversation_histories.get(request.thread_id)
    # Invoke the graph asynchronously with current state
    if request.user_input.strip() == "":
        return {'response':"please do not send an empty message"}
        # input = {"messages": previous_messages}
   
    user_message = HumanMessage(content = request.user_input.strip())
    previous_messages.append(user_message)
    input = {"messages": previous_messages}

    config = {"configurable": {"thread_id": request.thread_id}}

    async def stream_graph():
        async for step in app_planner.astream(input,config=config):
            # Serialize Python object to bytes
            key = list(step.keys())[0]
            conversation_histories[request.thread_id] += list(step[key]['messages'])
            print(conversation_histories[request.thread_id])
            yield pickle.dumps(step)
    

    return StreamingResponse(stream_graph(), media_type="application/octet-stream")
