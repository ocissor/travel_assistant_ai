import streamlit as st
import requests
import uuid
import sys
import json
import pickle
from datetime import datetime

sys.path.append("D:/travel_assistant_ai/app")
from database import collection  # Optional if you use MongoDB

API_URL = "http://127.0.0.1:8000/chat"

# Set up Streamlit page
st.set_page_config(page_title="✈️ Travel Assistant")
st.title("🌍 AI Travel Planner")
st.markdown("Plan your dream trip with the help of AI agents.")

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


# ----- Session State Initialization -----
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "ui_messages" not in st.session_state:
    st.session_state.ui_messages = []

if "awaiting_interrupt" not in st.session_state:
    st.session_state.awaiting_interrupt = False

if "interrupt_prompt" not in st.session_state:
    st.session_state.interrupt_prompt = ""


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
                                break
                        elif msg.type == "tool" and msg.name == 'get_hotels_list':
                            if msg.content and msg.content.strip()!="":
                                #st.json(json.loads(msg.content))
                                #st.session_state.ui_messages.append({"type": "ai", "content": json.loads(msg.content)})
                                hotels_list = get_sorted_hotel_strings_by_distance(json.loads(msg.content))
                                for hotel in hotels_list:
                                    st.chat_message('assistant').markdown(hotel)
                                    st.session_state.ui_messages.append({"type":"ai","content":hotel})
                                break
                        elif msg.type == 'tool' and msg.name == 'get_flights':
                            if msg.content and msg.content.strip()!="":
                                flights_data = collect_all_flight_info(json.loads(msg.content))
                                for flight_data in flights_data:
                                    st.chat_message('assistant').markdown(flight_data)
                                    st.session_state.ui_messages.append({"type":"ai","content":flight_data})
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
                            break
                    elif msg.type == "tool" and msg.name == 'get_hotels_list':
                            if msg.content and msg.content.strip()!="":
                                #st.json(json.loads(msg.content))
                                #st.session_state.ui_messages.append({"type": "ai", "content": json.loads(msg.content)})
                                hotels_list = get_sorted_hotel_strings_by_distance(json.loads(msg.content))
                                for hotel in hotels_list:
                                    st.chat_message('assistant').markdown(hotel)
                                    st.session_state.ui_messages.append({"type":"ai","content":hotel})
                                break
                    elif msg.type == 'tool' and msg.name == 'get_flights':
                            if msg.content and msg.content.strip()!="":
                                flights_data = collect_all_flight_info(json.loads(msg.content))
                                for flight_data in flights_data:
                                    st.chat_message('assistant').markdown(flight_data)
                                    st.session_state.ui_messages.append({"type":"ai","content":flight_data})
                                break

        except Exception as e:
            st.error(f"Request failed: {e}")
