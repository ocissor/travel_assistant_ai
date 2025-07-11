from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import ItinearyState
from agents.itineary_builder_agent import Itineary_builder_Agent, routing_function, ItinerayToolNode
from langgraph.checkpoint.memory import InMemorySaver


graph = StateGraph(ItinearyState)

graph.add_node("Itineary_planner",Itineary_builder_Agent)
graph.add_node("Itineary_tool", ItinerayToolNode)

graph.add_edge(START, "Itineary_planner")

graph.add_conditional_edges(
    "Itineary_planner",
    routing_function,
    {
        "use_tool": "Itineary_tool",
        END: END
    }
)

graph.add_edge("Itineary_tool", END)

checkpointer = InMemorySaver()
app_itinerary = graph.compile(checkpointer=checkpointer)

# Save Mermaid PNG to a file
png_bytes = app_itinerary.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png_bytes)


config = {"configurable": {"thread_id": "1"}}
# input = {"messages": []}
# output = app_itinerary.invoke(input)

