from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import ItinearyState
from langgraph.graph import END
import requests
from fpdf import FPDF
import os
import smtplib
import json
from dotenv import load_dotenv
load_dotenv()

def get_iata_codes(access_token:str, city: str):
    """Fetch IATA codes for a given city using the Amadeus API."""
    url = "https://test.api.amadeus.com/v1/reference-data/locations"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    params = {
        "keyword": city,
        "subType": "CITY",
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        output = response.json()
        return output['data'][0]['iataCode'] 
    else:
        print("Error:", response.status_code, response.text)
        return "Could not find IATA code for the given city. Please try again with a different city."
    
def get_amadeus_access_token(client_id: str, client_secret: str) -> str:
    url = "https://test.api.amadeus.com/v1/security/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }

    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()  # Raises error if status code != 200
    access_token = response.json().get("access_token")
    return access_token

#based on the location and destination, date and time we will get the flights
@tool
def build_itineary(origin:str, destination:str):
    """Build a travel itinerary based on the origin and destination."""
    system_prompt = SystemMessage(
        content=f"You are a travel itinerary builder agent. Your task is to create a detailed travel itinerary based on the {origin} and {destination}." 
    )
    input_message = HumanMessage(content=f"Please provide the itinerary details for travel from {origin} to {destination}.")
    all_messages = [system_prompt] + [input_message]
    itineary_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001",api_key=os.getenv("GEMINI_API_KEY"))
    response = itineary_model.invoke(all_messages)
    return response.content

@tool
def save_itineary_to_pdf(itineary_text: str, pdf_path: str):
    """Save the itinerary text to a PDF file."""

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("DejaVu", "", r"fonts\dejavu-sans-ttf-2.37\ttf\DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10, itineary_text)
    
    pdf.output(pdf_path)
    print(f"Itinerary saved to {pdf_path}")
    return f"Itinerary saved to {pdf_path}"

@tool
def send_itineary_to_email(itineary_text: str, user_email: str):
    """Send the itinerary text to the user's email."""
    # This is a placeholder function. In a real application, you would integrate with an email service.
    print(f"Sending itinerary to {user_email}...")
    return f"Itinerary sent to {user_email}"

tools = [build_itineary, save_itineary_to_pdf, send_itineary_to_email]
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001",api_key=os.getenv("GEMINI_API_KEY")).bind_tools(tools)

def Itineary_builder_Agent(state: ItinearyState) -> ItinearyState:
    """Itineary Agent to build the travel itinerary based on user preferences."""
    system_prompt = SystemMessage(
        content = "You are a travel itinerary builder agent. Your task is to create a detailed travel itinerary based on the user's preferences and requirements. " \
        "You will use the provided tools to gather necessary information and build the itinerary. You will also save the itinerary to a PDF file and send it to the user's email address if requested. "
    )
    if not state['messages']:
        #input_message = input("Please provide your travel details (origin, destination, dates, etc.) your email address : ")
        input_message = f"I want to travel from {state['origin']} to {state['destination']} build my itineary"
        user_message = HumanMessage(content=input_message)
    else:
        input_message = input("Please provide additional travel preferences or confirm the existing ones: ")
        user_message = HumanMessage(content=input_message)
    
    all_messages = [system_prompt] + list(state['messages']) + [user_message]
    response = model.invoke(all_messages)
    print(response.tool_calls)
    state['messages'] = list(state['messages']) + [user_message, response]

    return state

def ItinerayToolNode(state: ItinearyState) -> ItinearyState:
    """Node to handle itinerary building and saving."""
    last_message = state['messages'][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f" tool call info is : {last_message.tool_calls}")
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call['name']
        tool_args = tool_call['args']

        if tool_name == "build_itineary":
            origin = tool_args.get("origin")
            destination = tool_args.get("destination")
            itineary_text = build_itineary.invoke({"origin": origin, "destination": destination})
            state['itineary_text'] = itineary_text
            tool_msg = ToolMessage(
                content=json.dumps(itineary_text),
                name=tool_name,
                tool_call_id=tool_call["id"],
            )
            state["messages"].append(tool_msg)
            print(state['itineary_text'])
            
        elif tool_name == "save_itineary_to_pdf":
            itineary_text = state.get('itineary_text', "")
            pdf_path = tool_args.get("pdf_path", "itinerary.pdf")
            tool_output = save_itineary_to_pdf.invoke({"itineary_text": itineary_text, "pdf_path": pdf_path})
            state['pdf_path'] = pdf_path 
            tool_msg = ToolMessage(
                content=tool_output,
                name=tool_name,
                tool_call_id=tool_call["id"],
            )
            state["messages"].append(tool_msg)

        elif tool_name == "send_itineary_to_email":
            itineary_text = state.get('itineary_text', "")
            user_email = tool_args.get("user_email")
            send_itineary_to_email.invoke({itineary_text: itineary_text, "user_email": user_email})
            tool_msg = ToolMessage(
                content=f"Itinerary sent to {user_email}",
                name=tool_name,
                tool_call_id=tool_call["id"],
            )
            state["messages"].append(tool_msg)

    return state

def get_last_human_message(state: ItinearyState) -> HumanMessage:
    """Retrieve the last human message from the state."""
    for message in reversed(state['messages']):
        if isinstance(message, HumanMessage):
            return message
    return None

def should_exit(state: ItinearyState) -> bool:
    last_human_message = get_last_human_message(state)
    if last_human_message and "exit" in last_human_message.content.lower():
        return True
    return False

def routing_function(state: ItinearyState):
    """Determine the next step based on the last message."""
    if should_exit(state):
        return END
    last_message = state['messages'][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "use_tool"
    else:
        return "back_to_itineary_builder"
