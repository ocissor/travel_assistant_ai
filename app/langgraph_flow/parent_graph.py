from langgraph.graph import StateGraph, START, END
import sys
sys.path.append("D:/travel_assistant_ai/app")
from agents.parent_agent import *

# Build the parent graph
parent_graph = StateGraph(ParentState)

parent_graph.add_node("planner", call_planner_subgraph)
parent_graph.add_node("itinerary_builder", call_itinerary_subgraph)

parent_graph.add_edge(START, "planner")

parent_graph.add_conditional_edges(
    "planner",
    parent_routing,
    {
        "planner": "planner",
        "itinerary_builder": "itinerary_builder",
        END: END,
    }
)

parent_graph.add_conditional_edges(
    "itinerary_builder",
    parent_routing,
    {
        "planner": "planner",
        "itinerary_builder": "itinerary_builder",
        END: END,
    }
)

compiled_parent_graph = parent_graph.compile()

# To invoke:
initial_state = {
    "planner_state": {"messages": []},
    "itinerary_state": {"messages": []},
}

png_bytes = compiled_parent_graph.get_graph().draw_mermaid_png()
with open("parent_graph.png", "wb") as f:
    f.write(png_bytes)
response = compiled_parent_graph.invoke(initial_state)
