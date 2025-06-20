from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from typing import List
import sys
sys.path.append("D:/travel_assistant_ai/app")
from langgraph_flow.state import TravelState
from langgraph.graph import END
import requests
from typing import Sequence
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
import os
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
def get_flights(origin:str, destination:str, max_price: int = 200):
    """Based on the user input, return a list of flights from current location to destination."""

    print(f"Fetching flights from {origin} to {destination}...")

    access_token = get_amadeus_access_token(os.getenv("AMADEUS_API_KEY"), os.getenv("AMADEUS_SECRET_KEY"))

    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    origin_code = get_iata_codes(access_token,origin)
    destination_code = get_iata_codes(access_token,destination)

    params = {
        "originLocationCode": origin_code,
        "destinationLocationCode": destination_code,
        "departureDate": "2025-06-20",
        "adults": 1,
        "max": 1
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error:", response.status_code, response.text)
        return "Error fetching flights. Please try again later."

    #return "foud some flights, please check your preferred flight booking website for more details."

# 1. Define Pydantic model for structured output
class TravelLocations(BaseModel):
    origin: str = Field(default=None, description="Origin city or country")
    destination: str = Field(default=None, description="Destination city or country")

# 2. Create the output parser
parser = PydanticOutputParser(pydantic_object=TravelLocations)

@tool
def extract_destination(message: Sequence[BaseMessage]) -> TravelLocations:
    """Extract origin and destination from the user's messages as a structured object."""

    # 3. System prompt with instructions including format instructions from parser
    system_prompt = SystemMessage(
        content=(
            "You are a travel planner agent. Extract the origin and destination from the user's messages. "
            "Respond ONLY with a JSON object matching the schema below.\n\n"
            f"{parser.get_format_instructions()}"
        )
    )

    # 4. Prepare messages for the model: system prompt + conversation messages
    all_messages = [system_prompt] + list(message)

    # 5. Initialize your chat model (replace with your actual model and API key)
    analyse_model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001", api_key=os.getenv("GEMINI_API_KEY"))

    # 6. Invoke the model
    response = analyse_model.invoke(all_messages)

    # 7. Parse the response content into the Pydantic model
    try:
        travel_locations = parser.parse(response.content)
    except Exception as e:
        print(f"Failed to parse model output: {e}")
        # Return empty or default values on failure
        travel_locations = TravelLocations(origin=None, destination=None)
    print(f"Extracted travel locations: {travel_locations}")
    return travel_locations

tools = [get_flights]
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-001",api_key=os.getenv("GEMINI_API_KEY")).bind_tools(tools)

def Planner_Agent(state: TravelState) -> TravelState:
    """Planner Agent to recommend travel destinations based on mood."""
    # Initialize the Google Generative AI chat model
    system_prompt = SystemMessage(
        content=(
            "You are a travel planner agent. You can recommend travel destinations based on the user's conversation. "\
            "If the user asks for flight information, use the 'get_flights' tool to provide flight options. Also if the user has finalized their travel plans, "\
            "use the 'extract_destination' tool to extract origin and destination from the conversation. "
        )
    )

    if not state["messages"]:
        #user did not send any input
        user_input = input("I'm ready to help you with your travel plans, whats going on your mind?: \n")
        user_message = HumanMessage(content=user_input)

    else:
        if len(state["messages"]) == 1:
            #It is the first message and is the human message
            # user_input = state["messages"][0].content
            print(f"\n👤 USER: {state['messages'][0].content}")
            # user_message = HumanMessage(content=user_input)
            user_message = state["messages"][0]
        else:
            user_input = input("\nTell me more about your travel plans: ")
            print(f"\n👤 USER: {user_input}")
            user_message = HumanMessage(content=user_input)

    # state["last_message"] = user_message
    
    all_messages = [system_prompt] + list(state["messages"]) + [user_message]

    response = model.invoke(all_messages)
    print(response.tool_calls)
    print(f"🤖 BOT: {response.content}")

    state["messages"] = list(state["messages"]) + [user_message, response]
    
    print(f"origin: {state.get('origin')}, destination: {state.get('destination')}")
    return state

def Get_Flight_Node(state: TravelState) -> TravelState:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_call = last_message.tool_calls[0]
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        if tool_name == "get_flights":
            origin = tool_args.get("origin")
            destination = tool_args.get("destination")
            max_price = tool_args.get("max_price", 200)
            flight_info = get_flights.invoke({"origin": origin, "destination": destination, "max_price": max_price})
            tool_msg = ToolMessage(
                content=flight_info,
                name=tool_name,
                tool_call_id=tool_call["id"],
            )
            state["messages"].append(tool_msg)
            state["origin"] = origin
            state["destination"] = destination

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
    
