from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import TravelState
from agents.mood_recommender import Planner_Agent, should_exit, get_flights, use_get_flights_tool

graph = StateGraph(TravelState)

graph.add_node("planner",Planner_Agent)
graph.add_node("flight_tool", ToolNode(tools=[get_flights]))

graph.add_edge(START, "planner")

graph.add_conditional_edges(
    "planner",
    use_get_flights_tool,
    {
        "use_tool": "flight_tool",
        "continue": "planner"
    }
)

graph.add_conditional_edges(
    "planner",
    should_exit,
    {
        "exit": END,
        "continue": "planner"
    }
)

graph.add_edge("flight_tool", "planner")

app = graph.compile()

input = {"messages": [], "last_message": None}
output = app.invoke(input)
for message in output["messages"]:
    if isinstance(message, HumanMessage):
        print(f"👤 USER: {message.content}")
    elif isinstance(message, AIMessage):
        print(f"🤖 BOT: {message.content}")
