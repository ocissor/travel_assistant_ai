from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import TravelState
from agents.planner_agent import Planner_Agent, should_exit, routing_function, Get_Flight_Node
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

graph = StateGraph(TravelState)

graph.add_node("planner",Planner_Agent)
graph.add_node("flight_tool", Get_Flight_Node)

graph.add_edge(START, "planner")

graph.add_conditional_edges(
    "planner",
    routing_function,
    {
        "use_tool": "flight_tool",
        END: END,
    }
)

graph.add_edge("flight_tool", END)

checkpointer = InMemorySaver()
app_planner = graph.compile(checkpointer=checkpointer)

# Save Mermaid PNG to a file
png_bytes = app_planner.get_graph().draw_mermaid_png()
with open("graph.png", "wb") as f:
    f.write(png_bytes)

config = {"configurable": {"thread_id": "1"}}
# input = {"messages": ["Hi i am planning to visit beaches in india, can you help me with that?"]}
# # for step in app_planner.stream(input, config=config):
# #     print(step)
# output = app_planner.invoke(input,config=config)
# print(output['__interrupt__'])
# resume_command = Command(resume="Tell me more about goa")
# result = app_planner.invoke(resume_command, config=config)
# print("RESULT AFTER INTERRUPT \n")
# print('\n')
# print(result)
#input = {"messages": ["Get me hotels in Paris!"]}
#output = app_planner.invoke(input,config=config)
#print(output)
# for message in output["messages"]:
#     if isinstance(message, HumanMessage):
#         print(f"👤 USER: {message.content}")
#     elif isinstance(message, AIMessage):
#         print(f"🤖 BOT: {message.content}")


