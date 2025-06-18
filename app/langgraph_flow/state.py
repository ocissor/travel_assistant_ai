from typing import Optional, TypedDict, Annotated, Sequence, List 
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages

class TravelState(TypedDict):
    """"based on the user input have a conversation with the user about travel"""
    messages : Annotated[Sequence[BaseMessage], add_messages]
    last_message: Optional[HumanMessage] | None