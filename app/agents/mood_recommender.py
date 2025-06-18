from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import TravelState
from langgraph.graph import END
import os

#based on the location and destination, date and time we will get the flights
@tool
def get_flights(current_location:str, destination:str):
    """Based on the user input, return a list of flights from current location to destination."""
    print(f"Fetching flights from {current_location} to {destination}...")
    return "foud some flights, please check your preferred flight booking website for more details."

tools = [get_flights]
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001",api_key="AIzaSyBQcpKtIsVtm2ZRnTf6GTMkXF1Nuyxh6d0").bind_tools(tools)

def Planner_Agent(state: TravelState) -> TravelState:
    """Planner Agent to recommend travel destinations based on mood."""
    # Initialize the Google Generative AI chat model
    system_prompt = SystemMessage(
        content=(
            "You are a travel planner agent. You can recommend travel destinations based on the user's conversation. "
            "If the user asks for flight information, use the 'get_flights' tool to provide flight options."
        )
    )

    if not state["messages"]:
        user_input = input("I'm ready to help you with your travel plans, whats going on your mind?: \n")
        user_message = HumanMessage(content=user_input)

    else:
        user_input = input("\nTell me more about your travel plans: ")
        print(f"\n👤 USER: {user_input}")
        user_message = HumanMessage(content=user_input)

    # state["last_message"] = user_message
    
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]

    response = model.invoke(all_messages)
    
    print(f"🤖 BOT: {response.content}")

    state["messages"] = list(state["messages"]) + [user_message, response]
    
    return state

def Get_Flight_Node(state: TravelState) -> TravelState:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool = next(t for t in tools if t.name == tool_call["name"])
            tool_msg = tool.invoke(tool_call)
            print(f"Tool invoked: {tool_msg}")
            state["messages"].append(tool_msg)
    return state

def get_last_human_message(state: TravelState) -> HumanMessage | None:
    """Get the last human message from the state."""
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message
    return None
# Check if user wants to exit
def should_exit(state: TravelState) -> bool:
    last_human = get_last_human_message(state)
    if last_human and "exit" in last_human.content.lower():
        return True
    return False
    
def routing_function(state: TravelState):
    if should_exit(state):
        return END
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "use_tool"
    else:
        return "back_to_planner"