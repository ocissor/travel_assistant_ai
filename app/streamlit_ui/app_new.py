import streamlit as st
import requests
import uuid
import sys
sys.path.append("D:/travel_assistant_ai/app")
from database import collection
import pickle
from datetime import datetime
import json

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

API_URL = "http://127.0.0.1:8000/chat"

# Set up Streamlit page
st.set_page_config(page_title="✈️ Travel Assistant")
st.title("🌍 AI Travel Planner")
st.markdown("Plan your dream trip with the help of AI agents.")

# Session state for UI only (not full history)
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = []  # [{type: "human"/"ai", content: "..."}]

if "interrupt_called" not in st.session_state:
    st.session_state.interrupt_called = False

if "user_interrupt_input" not in st.session_state:
    st.session_state.user_interrupt_input = ""

# Show conversation so far
for msg in st.session_state.ui_messages:
    if msg["type"] == "human":
        st.chat_message("user").markdown(msg["content"])
    elif msg["type"] == "ai":
        st.chat_message("assistant").markdown(msg["content"])

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

# Chat input box at bottom
if prompt := st.chat_input("Where do you want to go?"):
    # Show and store user message
    st.chat_message("user").markdown(prompt)
    st.session_state.ui_messages.append({"type": "human", "content": prompt})

    # Send to FastAPI backend with current thread_id
    with st.spinner("The Agent is Thinking..."):
        try:
            payload = {
                "user_input": prompt,
                "thread_id": st.session_state.thread_id,
            }
            response = requests.post(API_URL, json=payload,stream=True)
            buffer = b""
            for chunk in response.iter_content(chunk_size=None):
                buffer += chunk
                try:
                    step = pickle.loads(buffer)
                    buffer = b""
                    key = list(step.keys())[0]
                    messages = step[key].get('messages',[])
                    for msg in reversed(messages):
                        if msg.type == 'ai':
                            if msg.content and msg.content.strip() != "":
                                st.chat_message('assistant').markdown(msg.content)
                                st.session_state.ui_messages.append({'type':'ai', 'content':msg.content})
                                break
                        elif msg.type == 'tool':
                            if msg.content and msg.content.strip()!="":
                                flights_info = collect_all_flight_info(json.loads(msg.content))
                                for i in range(len(flights_info)):
                                    st.chat_message('assistant').markdown(flights_info[i])
                                    st.session_state.ui_messages.append({'type':'ai', 'content':flights_info[i]})
                                break
                    
                except (pickle.UnpicklingError, EOFError):
                    continue

        except Exception as e:
            st.error(f"Request failed: {e}")
