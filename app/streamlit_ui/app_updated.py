import streamlit as st
import requests
import uuid
import sys
import json
import pickle
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.messages import SystemMessage,HumanMessage, AIMessage
import time
sys.path.append("D:/travel_assistant_ai/app")
from database import collection  # Optional if you use MongoDB

load_dotenv()

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash" ,api_key=os.getenv("GEMINI_API_KEY"), temperature = 0.3)

API_URL = "http://127.0.0.1:8000/chat"

# Set up Streamlit page
st.set_page_config(page_title="✈️ Travel Assistant")
st.title("🌍 AI Travel Planner")
st.markdown("Plan your dream trip with the help of AI agents.")


# ----- Session State Initialization -----
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = []

if "awaiting_interrupt" not in st.session_state:
    st.session_state.awaiting_interrupt = False

if "interrupt_prompt" not in st.session_state:
    st.session_state.interrupt_prompt = ""

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if 'previous_convs' not in st.session_state:
    st.session_state.previous_convs = []

if 'thread_id_mapping' not in st.session_state:
    st.session_state.thread_id_mapping = {} 

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Chatbot"

PAGES = {
    "Chatbot":"Chatbot",
    'Get clothing recommendations': "find clothes for your trip",
    'Get Weather Info': 'Weather Info',
    'Build Itinerary': 'Build Itinerary'
}

with st.sidebar:
    for key in PAGES.keys():
        if st.button(PAGES[key],use_container_width=True):
            st.session_state.current_page = key

page = st.session_state.current_page
if page == 'Get clothing recommendations':
    st.write("Get clothing recommendations")
if page == 'Get Weather Info':
    st.write("Weather page")  
if page == 'Build Itinerary':
    st.write("Build Itinerary")

st.session_state.thread_id_mapping[st.session_state.thread_id] = {
                        "ui_messages":st.session_state.ui_messages,
                        "awaiting_interrupt": st.session_state.awaiting_interrupt,
                        "interrupt_prompt": st.session_state.interrupt_prompt,
                        "conversation_history":st.session_state.conversation_history
                    } 


st.sidebar.title("Previous Chats")

if st.sidebar.button("new chat",use_container_width=True):
    # Step 1: Read and use existing conversation history

    messages = [msg for msg in st.session_state.conversation_history if msg.content and msg.content.strip() != ""]
    
    if len(messages) == 0:
        # Step 2: Clear state AFTER using it
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.ui_messages = []
        st.session_state.awaiting_interrupt = False
        st.session_state.interrupt_prompt = ""
        st.session_state.conversation_history = []

        # for prevs_msg in st.session_state.previous_convs:
        #     st.sidebar.button(prevs_msg[0])

    else:

        system_prompt = SystemMessage(content="You are a helpful assistant specialized in summarizing conversations. "
        "Your ONLY task is to generate a concise title for the given conversation history. "
        "The title should be brief, and accurately reflect the main topic. "
        "It must not be empty. Your response must contain ONLY the title, with no additional text, "
        "preamble, conversational filler, or punctuation other than what is part of the title itself. "
        "Do not number the title or include quotation marks around it.")

        all_messages = [system_prompt] + [HumanMessage(content="Generate a title for this conversation.")] + messages 
        
        response = model.invoke(all_messages)
        
        if response.content == "":
            if messages[0].content and messages[0].content.strip() != "":
                response.content = messages[0].content
        
        # st.sidebar.button(response.content)
        st.session_state.previous_convs.append((response.content,st.session_state.thread_id))
        # Step 2: Clear state AFTER using it
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.ui_messages = []
        st.session_state.awaiting_interrupt = False
        st.session_state.interrupt_prompt = ""
        st.session_state.conversation_history = []


if len(st.session_state.previous_convs) != 0:
    for i, prevs_msg in enumerate(st.session_state.previous_convs):
        if st.sidebar.button(prevs_msg[0],key=f"load_chat_{i}"):
            thread_id = prevs_msg[1]
            st.session_state.thread_id = thread_id
            st.session_state.ui_messages = st.session_state.thread_id_mapping[thread_id]['ui_messages']
            st.session_state.awaiting_interrupt = st.session_state.thread_id_mapping[thread_id]['awaiting_interrupt']
            st.session_state.interrupt_prompt = st.session_state.thread_id_mapping[thread_id]['interrupt_prompt']
            st.session_state.conversation_history = st.session_state.thread_id_mapping[thread_id]['conversation_history']

def format_flight_offer(offer: dict) -> str:
    lines = []
    lines.append("✈️  **Flight Offer**")
    lines.append(f"🆔 Offer ID: {offer.get('id')}")
    lines.append(f"💺 Seats available: {offer.get('numberOfBookableSeats')}")
    lines.append("")

    # Flight segments
    for itinerary in offer.get("itineraries", []):
        lines.append(f"🕒 Duration: {itinerary.get('duration', 'N/A')}")
        lines.append("📍 Route:")

        for segment in itinerary.get("segments", []):
            dep = segment["departure"]
            arr = segment["arrival"]
            dep_time = datetime.fromisoformat(dep["at"]).strftime("%d %b %Y, %I:%M %p")
            arr_time = datetime.fromisoformat(arr["at"]).strftime("%d %b %Y, %I:%M %p")
            lines.append(f"  → {dep['iataCode']} ({dep_time}) ➡ {arr['iataCode']} ({arr_time})")
            lines.append(f"    Flight: {segment['carrierCode']} {segment['number']} | Aircraft: {segment['aircraft']['code']}")
            lines.append(f"    Duration: {segment.get('duration')} | Stops: {segment.get('numberOfStops')}")
        lines.append("")

    # Price
    price = offer.get("price", {})
    lines.append(f"💰 Total Price: {price.get('grandTotal')} {price.get('currency')}")
    lines.append(f"   Base: {price.get('base')} + Taxes/Fees")

    # Baggage & Cabin Info
    traveler = offer.get("travelerPricings", [{}])[0]
    fare_details = traveler.get("fareDetailsBySegment", [{}])[0]
    bag_info = fare_details.get("includedCheckedBags", {})
    cabin_info = fare_details.get("includedCabinBags", {})

    lines.append("🧳 Baggage Allowance:")
    lines.append(f"   - Checked Bag: {bag_info.get('weight', 0)} {bag_info.get('weightUnit', 'KG')}")
    lines.append(f"   - Cabin Bag: {cabin_info.get('weight', 0)} {cabin_info.get('weightUnit', 'KG')}")
    
    # Optional: list amenities
    amenities = fare_details.get("amenities", [])
    if amenities:
        lines.append("🎁 Amenities:")
        for a in amenities:
            charge = " (Chargeable)" if a.get("isChargeable") else ""
            lines.append(f"   - {a.get('description')}{charge}")

    return "\n".join(lines)


def collect_all_flight_info(flight_info_json):
    flight_info = []
    for i in range(len(flight_info_json['data'])):
        flight_info.append(format_flight_offer(flight_info_json['data'][i]))
    return flight_info

# ----- Streaming Helper -----
def stream_graph(payload):
    response = requests.post(API_URL, json=payload, stream=True)
    buffer = b""
    for chunk in response.iter_content(chunk_size=None):
        buffer += chunk
        try:
            step = pickle.loads(buffer)
            buffer = b""
            yield step
        except (pickle.UnpicklingError, EOFError):
            continue

def get_sorted_hotel_strings_by_distance(hotels):
    # Sort hotels by distance value
    sorted_hotels = sorted(hotels, key=lambda h: h.get("distance", {}).get("value", float("inf")))

    hotel_strings = []

    for hotel in sorted_hotels:
        name = hotel.get("name", "N/A")
        rating = hotel.get("rating", "N/A")
        distance = hotel.get("distance", {}).get("value", "N/A")
        distance_unit = hotel.get("distance", {}).get("unit", "KM")
        address = hotel.get("address", {})
        address_lines = ", ".join(address.get("lines", []))
        city = address.get("cityName", "")
        postal = address.get("postalCode", "")
        country = address.get("countryCode", "")

        full_address = f"{address_lines}, {postal} {city}, {country}"
        hotel_string = f"{name} | ⭐ {rating} | 📍 {full_address} | 🚶 {distance} {distance_unit}"

        hotel_strings.append(hotel_string)

    return hotel_strings

# ----- Display Chat History -----
for msg in st.session_state.ui_messages:
    role = "user" if msg["type"] == "human" else "assistant"
    st.chat_message(role).markdown(msg["content"])

# ----- Handle Interrupt Prompt (if any) -----
if st.session_state.awaiting_interrupt:
    
    if 'interrupt_input' not in st.session_state or not st.session_state['interrupt_input']:
    
        st.chat_message("assistant").markdown(st.session_state.interrupt_prompt)
        st.session_state.ui_messages.append({"type":"ai", "content":st.session_state.interrupt_prompt})


    if 'interrupt_input' in st.session_state and st.session_state['interrupt_input']:
        user_response = st.session_state['interrupt_input']

        st.session_state.ui_messages.append({"type": "human", "content": user_response})
        st.chat_message('user').markdown(user_response)

        payload = {
            "user_input": user_response,
            "thread_id": st.session_state.thread_id,
            "interrupt_called": True
        }
        st.session_state.awaiting_interrupt = False
        st.session_state.interrupt_prompt = ""
        st.session_state['interrupt_input'] = ""

        with st.spinner("Resuming after interrupt..."):
            try:
                for step in stream_graph(payload):
                    
                    if "__interrupt__" in step:
                        st.session_state.interrupt_prompt = step["__interrupt__"][0].value
                        st.session_state.awaiting_interrupt = True
                        st.rerun()

                    key = list(step.keys())[0]
                    messages = step[key].get("messages", [])
                    for msg in reversed(messages):
                        if msg.type == "ai":
                            if msg.content and msg.content.strip()!="":
                                st.chat_message("assistant").markdown(msg.content)
                                st.session_state.ui_messages.append({"type": "ai", "content": msg.content})
                                st.session_state.conversation_history.append(AIMessage(content = msg.content))
                                break
                        elif msg.type == "tool" and msg.name == 'get_hotels_list':
                            if msg.content and msg.content.strip()!="":
                                #st.json(json.loads(msg.content))
                                #st.session_state.ui_messages.append({"type": "ai", "content": json.loads(msg.content)})
                                hotels_list = get_sorted_hotel_strings_by_distance(json.loads(msg.content))
                                for hotel in hotels_list:
                                    st.chat_message('assistant').markdown(hotel)
                                    st.session_state.ui_messages.append({"type":"ai","content":hotel})
                                    st.session_state.conversation_history.append(AIMessage(content = hotel))
                                break
                        elif msg.type == 'tool' and msg.name == 'get_flights':
                            if msg.content and msg.content.strip()!="":
                                flights_data = collect_all_flight_info(json.loads(msg.content))
                                for flight_data in flights_data:
                                    st.chat_message('assistant').markdown(flight_data)
                                    st.session_state.ui_messages.append({"type":"ai","content":flight_data})
                                    st.session_state.conversation_history.append(AIMessage(content = flight_data))
                                break

            except Exception as e:
                st.error(f"Request failed: {e}")

    else:
        st.text_input("Your response to the above question:", key="interrupt_input")
        
# ----- Main Input Box -----
if prompt := st.chat_input("Where do you want to go?"):

    if prompt:
        # User message input
        st.chat_message("user").markdown(prompt)
        st.session_state.ui_messages.append({"type": "human", "content": prompt})
        st.session_state.conversation_history.append(HumanMessage(content = prompt))
        payload = {
            "user_input": prompt,
            "thread_id": st.session_state.thread_id,
            "interrupt_called": False
        }

    with st.spinner("The Agent is Thinking..."):
        try:
            for step in stream_graph(payload):
                
                if "__interrupt__" in step:
                    # Show interrupt message, then stop stream to wait for user
                    st.session_state.interrupt_prompt = step["__interrupt__"][0].value
                    st.session_state.awaiting_interrupt = True
                    st.rerun()

                key = list(step.keys())[0]
                messages = step[key].get("messages", [])
                for msg in reversed(messages):
                    if msg.type == "ai":
                        if msg.content and msg.content.strip() != "":
                            st.chat_message("assistant").markdown(msg.content)
                            st.session_state.ui_messages.append({
                                "type": "ai",
                                "content": msg.content
                            })
                            st.session_state.conversation_history.append(AIMessage(content = msg.content))
                            break
                    elif msg.type == "tool" and msg.name == 'get_hotels_list':
                            if msg.content and msg.content.strip()!="":
                                #st.json(json.loads(msg.content))
                                #st.session_state.ui_messages.append({"type": "ai", "content": json.loads(msg.content)})
                                hotels_list = get_sorted_hotel_strings_by_distance(json.loads(msg.content))
                                for hotel in hotels_list:
                                    st.chat_message('assistant').markdown(hotel)
                                    st.session_state.ui_messages.append({"type":"ai","content":hotel})
                                    st.session_state.conversation_history.append(AIMessage(content = hotel))
                                break
                    elif msg.type == 'tool' and msg.name == 'get_flights':
                            if msg.content and msg.content.strip()!="":
                                flights_data = collect_all_flight_info(json.loads(msg.content))
                                for flight_data in flights_data:
                                    st.chat_message('assistant').markdown(flight_data)
                                    st.session_state.ui_messages.append({"type":"ai","content":flight_data})
                                    st.session_state.conversation_history.append(AIMessage(content = flight_data))
                                break

        except Exception as e:
            st.error(f"Request failed: {e}")


