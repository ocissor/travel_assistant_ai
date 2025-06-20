from typing_extensions import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph_flow.state import TravelState, ItinearyState, ParentState
from langgraph_flow.graph import app_planner
from langgraph_flow.itineary_builder_graph import app_itinerary


planner_graph = app_planner
itinerary_graph = app_itinerary

# Wrapper node to call planner subgraph
def call_planner_subgraph(state: ParentState) -> ParentState:
    output = planner_graph.invoke(state.get("planner_state", {"messages": []}))
    return {
        "planner_state": output,
        "itinerary_state": state.get("itinerary_state", {"messages": []}),
    }

# Wrapper node to call itinerary subgraph
def call_itinerary_subgraph(state: ParentState) -> ParentState:
    itinerary_input = state.get("itinerary_state", {"messages": []})

    planner_dest = state["planner_state"].get("destination")
    planner_origin = state["planner_state"].get("origin")
    if planner_dest:
        itinerary_input["destination"] = planner_dest
    if planner_origin:
        itinerary_input["origin"] = planner_origin

    output = itinerary_graph.invoke(itinerary_input)
    return {
        "planner_state": state["planner_state"],
        "itinerary_state": output,
    }

def check_planner_done(planner_state: TravelState) -> bool:
    # Example: check last human message for "done" or "exit"
    messages = planner_state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg, HumanMessage):
            if "done" in msg.content.lower() or "exit" in msg.content.lower():
                return True
    return False

def check_itinerary_done(itinerary_state: ItinearyState) -> bool:
    messages = itinerary_state.get("messages", [])
    for msg in reversed(messages):
        if hasattr(msg, "content") and isinstance(msg, HumanMessage):
            if "done" in msg.content.lower() or "exit" in msg.content.lower():
                return True
    return False

# Parent graph routing function
def parent_routing(state: ParentState):
    if check_planner_done(state["planner_state"]) and not check_itinerary_done(state["itinerary_state"]):
        return "itinerary_builder"
    if check_itinerary_done(state["itinerary_state"]) and check_planner_done(state["planner_state"]):
        return END
    return "planner"
