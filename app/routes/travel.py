from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.messages import HumanMessage
import sys 
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.graph import app_planner  # import your compiled LangGraph 
from langgraph_flow.itineary_builder_graph import app_itinerary  # import your compiled LangGraph for itinerary building
import uuid 
import pickle
from fastapi.responses import StreamingResponse
from langgraph.types import Command

conversation_histories = {}

app = FastAPI()

class ChatRequest(BaseModel):
    user_input: str
    thread_id: Optional[str] = None
    interrupt_called: Optional[bool] = Field(default=False, description="Check if interrupt is called")

class ItineraryRequest(BaseModel):
    thread_id: Optional[str] = None
    origin: Optional[str] = None
    destination: Optional[str] = None
    style: Optional[str] = None
    dates: Optional[list[str]] = None
    additional_info: Optional[str] = None
    feedback: Optional[str] = None
    itinerary_button_presses: Optional[int] = Field(default=0, description="Number of times the itinerary button has been pressed")
    itinerary_text: Optional[str] = None

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
   
    if request.interrupt_called:
        print("inside interrupt if condition")
        input = Command(resume = request.user_input)
    else:
        user_message = HumanMessage(content = request.user_input.strip())
        previous_messages.append(user_message)
        input = {"messages": previous_messages}

    config = {"configurable": {"thread_id": request.thread_id}}

    async def stream_graph():
        async for step in app_planner.astream(input,config=config):
            # Serialize Python object to bytes
            if '__interrupt__' not in step:
                key = list(step.keys())[0]
                conversation_histories[request.thread_id] = list(step[key].get('messages',[]))
                # print('\n')
                # print("last message is :", conversation_histories[request.thread_id])
                # print('\n')
                # print(len(conversation_histories[request.thread_id]))
                # print(conversation_histories[request.thread_id])
            
            yield pickle.dumps(step)
    

    return StreamingResponse(stream_graph(), media_type="application/octet-stream")


@app.post('/build_itinerary')
def build_itinerary(itinerary_request: ItineraryRequest):
    """
    Endpoint to build an itinerary based on user input.
    """
    print("inside build_itinerary endpoint")
    if itinerary_request.thread_id is None:
        itinerary_request.thread_id = str(uuid.uuid4())
    
    origin = itinerary_request.origin.strip() if itinerary_request.origin else None
    destination = itinerary_request.destination.strip() if itinerary_request.destination else None
    start_date = itinerary_request.dates[0].strip() if itinerary_request.dates[0] else None
    end_date = itinerary_request.dates[1].strip() if itinerary_request.dates[1] else None
    style = itinerary_request.style.strip() if itinerary_request.style else None
    additional_info = itinerary_request.additional_info.strip() if itinerary_request.additional_info else None
    feedback = itinerary_request.feedback.strip() if itinerary_request.feedback else None
    itinerary_button_presses = itinerary_request.itinerary_button_presses
    itinerary_text = itinerary_request.itinerary_text.strip() if itinerary_request.itinerary_text else None

    if origin is None or destination is None or start_date is None or end_date is None or style is None:
        return {'invalid input': "Please provide both origin and destination."}
    
    if itinerary_request.thread_id not in conversation_histories.keys():
        conversation_histories[itinerary_request.thread_id] = []

    previous_messages = conversation_histories.get(itinerary_request.thread_id)
    
    input = {

            "messages": previous_messages, "origin": origin, 
            "destination": destination, "start_date": start_date, "end_date": end_date,
            "style": style, "additional_info": additional_info,
            "feedback": feedback, 'itinerary_button_presses': itinerary_button_presses,
            'itinerary_text': itinerary_text

            }
    
    config = {"configurable": {"thread_id": itinerary_request.thread_id}}

    async def stream_graph():
        async for step in app_itinerary.astream(input, config=config):
            conversation_histories[itinerary_request.thread_id] = list(step.get('messages', []))
            yield pickle.dumps(step)

    return StreamingResponse(stream_graph(), media_type="application/octet-stream")