from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import TravelState
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
        content = "You are a travel planner agent. Recommend travel destinations based on the user's conversation"
    )

    if not state["messages"]:
        user_input = input("I'm ready to help you with your travel plans, whats going on your mind?: \n")
        user_message = HumanMessage(content=user_input)

    else:
        user_input = input("\nTell me more about your travel plans: ")
        print(f"\n👤 USER: {user_input}")
        user_message = HumanMessage(content=user_input)

    state["last_message"] = user_message
    
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]

    response = model.invoke(all_messages)
    print(response.tool_calls)
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        # Find the tool by name
        tool = next(t for t in tools if t.name == tool_call["name"])
        tool_msg = tool.invoke(tool_call)
        print(f"tool_msg is {tool_msg}")
        # Append user message, model response, and tool message
        state["messages"] = list(state["messages"]) + [user_message, response, tool_msg]
    else:
        # No tool call, just append user message and model response
        state["messages"] = list(state["messages"]) + [user_message, response]
    
    return state

def should_exit(state: TravelState):
    last_message = state.get("last_message")
    if last_message and "exit" in last_message.content.lower():
        return "exit"
    else:
        return "continue"
    
def use_get_flights_tool(state: TravelState):
    messages = state.get("messages")
    if messages:
        last_message = messages[-1]
        if last_message.tool_calls:
            return "use_tool"
        else:
            return "continue"