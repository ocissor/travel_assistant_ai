from typing import Optional, TypedDict, Annotated, Sequence, List 
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages

class TravelState(TypedDict):
    """"based on the user input have a conversation with the user about travel"""
    messages : Annotated[Sequence[BaseMessage], add_messages]
    origin: Optional[str]
    destination: Optional[str]

class ItinearyState(TypedDict):
    origin : Optional[str]
    destination: Optional[str]
    pdf_path: Optional[str]
    itinerary_text: Optional[str]
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_email: Optional[Annotated[str, "It has to be a valid email address"]]
    additional_info: Optional[str]
    feedback : Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    style: Optional[str]
    itinerary_button_presses: Optional[int]  # Number of times the itinerary button has been pressed

# Define the combined parent state schema
class ParentState(TypedDict):
    planner_state: TravelState
    itinerary_state: ItinearyState