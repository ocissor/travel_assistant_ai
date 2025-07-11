import streamlit as st
import requests
import pickle
import uuid
from fastapi.responses import StreamingResponse
import sys
import os
from langchain_core.messages import SystemMessage,HumanMessage, AIMessage
import time
sys.path.append("D:/travel_assistant_ai/app")

def app():

    API_URL = "http://127.0.0.1:8000/build_itinerary"

    st.set_page_config(
    page_title="🗺️ AI Travel Itinerary Planner",
    page_icon="🌍",
    layout="wide"  # or "wide"
    )

    # st.title("🗺️ AI Travel Itinerary Planner")
    # st.markdown("welcome to the AI Travel Itinerary Planner! This tool helps you create detailed travel itineraries based on your preferences and travel plans. Simply fill out the form below to get started.")

    def display_itinerary(data: dict) -> str:
        """
        Generate a nicely formatted itinerary string from the backend data.
        No Streamlit rendering is used — returns a plain string.
        """

        if "Itineary_planner" not in data:
            return "❌ Itinerary data not found."

        itinerary = data["Itineary_planner"]

        origin = itinerary.get('origin', 'N/A')
        destination = itinerary.get('destination', 'N/A')
        start_date = itinerary.get('start_date', 'N/A')
        end_date = itinerary.get('end_date', 'N/A')
        style = itinerary.get('style', 'N/A')
        additional_info = itinerary.get('additional_info', 'None')
        itinerary_text = itinerary.get("itinerary_text", "Itinerary not available.")

        output = f"""
                    🗺️ ITINERARY OVERVIEW
                    ---------------------
                    From: {origin}
                    To: {destination}
                    Dates: {start_date} to {end_date}
                    Style: {style}
                    Additional Info: {additional_info}

                    ---------------------
                    🗓️ DETAILED ITINERARY
                    ---------------------
                    {itinerary_text}
                    """.strip()

        return output



    def stream_graph(payload):
        response = requests.post(url=API_URL, json=payload, stream=True)

        content_type = response.headers.get("content-type", "")

        # Case: error JSON returned
        if response.status_code != 200 or "application/json" in content_type:
            try:
                error_data = response.json()
                if "invalid input" in error_data:
                    st.error(error_data["invalid input"])
            except Exception:
                st.error("Unknown error occurred")
                st.code(response.text)
            return

        # Case: valid streaming response
        buffer = b""
        for chunk in response.iter_content(chunk_size=None):
            buffer += chunk
            try:
                step = pickle.loads(buffer)
                buffer = b""
                yield step
            except pickle.UnpicklingError:
                continue

    # To avoid horizontal scrolling on ultra-wide screens, we can limit the width of chat message blocks and force word wrap.
    st.markdown("""
    <h1 style='text-align: center;'>🗺️ AI Travel Itinerary Planner</h1>
    <p style='text-align: center; font-size: 1.1rem;'>
    Build your dream itinerary in seconds with AI-powered suggestions.
    </p>
    """, unsafe_allow_html=True)



    st.markdown("""
    <style>
        /* Force word wrap in chat messages */
        .chat-message {
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
            white-space: pre-wrap !important;
        }

        /* Constrain max width for chat messages */
        .element-container:has(.chat-message) {
            max-width: 100% !important;
        }

        /* Make main container responsive */
        .main {
            max-width: 1100px;
            margin: auto;
            padding-left: 2rem;
            padding-right: 2rem;
        }

        /* Allow horizontal scrollbar only when necessary */
        .block-container {
            overflow-x: auto;
                }
            </style>
        """, unsafe_allow_html=True)


    col1, col2 = st.columns(2)


    if 'prev_origin' not in st.session_state:
        st.session_state.prev_origin = ""

    if 'prev_destination' not in st.session_state:
        st.session_state.prev_destination = ""

    if 'prev_dates' not in st.session_state:
        st.session_state.prev_dates = None

    if 'prev_style' not in st.session_state:
        st.session_state.prev_style = ""

    if 'prev_additional_info' not in st.session_state:
        st.session_state.prev_additional_info = "" 

    if 'itinerary_button_presses' not in st.session_state:
        st.session_state.itinerary_button_presses = 0

    if 'itinerary_thread_id' not in st.session_state:
        st.session_state.itinerary_thread_id = str(uuid.uuid4())

    if 'itinerary_ui_messages' not in st.session_state:
        st.session_state.itinerary_ui_messages = []

    if 'itinerary_text' not in st.session_state:
        st.session_state.itinerary_text = ""

    if 'is_generating' not in st.session_state:
        st.session_state.is_generating = False

    if 'incorporating_feedback' not in st.session_state:
        st.session_state.incorporating_feedback = False

    if 'trigger_generation' not in st.session_state:
        st.session_state.trigger_generation = False
    
    if 'take_feedback' not in st.session_state:
        st.session_state.take_feedback = True
        
    if 'current_feedback' not in st.session_state:
        st.session_state.current_feedback = ""

    with col1:
        origin = st.text_input("Where are you coming from?")
        destination = st.text_input("Where are you going?")
        dates = st.date_input("Select your trip dates", [])

    with col2:
        style = st.selectbox("Travel Style", ["Relaxing", "Adventure", "Cultural"])
        additional_info = st.text_input(
            "Add other information you want in your itinerary or travel plans...",
            key="additional_info"
        )


    if st.session_state.prev_origin != origin or st.session_state.prev_destination != destination or \
        st.session_state.prev_dates != dates or st.session_state.prev_style != style or st.session_state.prev_additional_info != additional_info:

        st.session_state.itinerary_button_presses = 0
        st.session_state.prev_origin = origin
        st.session_state.prev_destination = destination
        st.session_state.prev_dates = dates
        st.session_state.prev_style = style 
        st.session_state.prev_additional_info = additional_info


    # Display previous messages in the chat UI
    if st.session_state.itinerary_ui_messages:
        for msg in st.session_state.itinerary_ui_messages:
            if msg['type'] == 'human':
                st.chat_message("user").markdown(msg['content'])
            elif msg['type'] == 'ai':
                st.chat_message("assistant").markdown(msg['content'])

        
    if feedback := st.chat_input("Would you like to make changes in your itinerary or travel plans?",key="itinerary_chat",
                                disabled = not st.session_state.take_feedback):

        if feedback: 
            st.session_state.take_feedback = False
            st.session_state.incorporating_feedback = True
            st.session_state.current_feedback = feedback
            st.rerun()

    if st.session_state.incorporating_feedback:

        st.session_state.incorporating_feedback = False

        if st.session_state.itinerary_button_presses == 0:
            st.warning("Please generate an itinerary first before providing feedback.")

        elif st.session_state.itinerary_button_presses > 0:
            if st.session_state.current_feedback.strip() != "":
                st.session_state.itinerary_ui_messages.append({'type':'human', 'content': st.session_state.current_feedback})
                st.chat_message("user").markdown(st.session_state.current_feedback)
                with st.spinner("incorporating feedback..."):
                
                    payload = {
                        "origin": origin,
                        "destination": destination,
                        "dates": [d.isoformat() for d in dates] if isinstance(dates, tuple) else dates.isoformat(),
                        "style": style,
                        "feedback": st.session_state.current_feedback,
                        "additional_info": None,
                        "thread_id": st.session_state.itinerary_thread_id,
                        'itinerary_button_presses': st.session_state.itinerary_button_presses,
                        'itinerary_text': st.session_state.itinerary_text
                    }

                    for step in stream_graph(payload):
                    
                        key = list(step.keys())[0]
                        if key == "Itineary_planner":
                            st.session_state.itinerary_text = step[key].get("itineary_text", "")
                            st.chat_message("assistant").markdown(display_itinerary(step))
                            for msg in reversed(step[key].get("messages", [])):
                                if msg.type == 'ai' and msg.content and msg.content.strip() != "":
                                    st.session_state.itinerary_ui_messages.append({'type':'ai', 'content': display_itinerary(step)})
                                    break
                    st.session_state.itinerary_button_presses += 1
                    
                    st.session_state.take_feedback = True
                    st.session_state.current_feedback = ""
    

    if st.button("Generate Itinerary", disabled=st.session_state.is_generating):

        st.session_state.is_generating = True
        st.session_state.trigger_generation = True
        st.rerun()

    if st.session_state.trigger_generation:

        st.session_state.trigger_generation = False

        if additional_info:
            msg = f"Building itinerary based on these details - for travel from {origin} to {destination}. " \
                f"the dates mentioned by user are from {dates[0].isoformat()} to {dates[-1].isoformat()}, style of travel is {style}, and the additional information is {additional_info} " \
                f"Make the itinerary as detailed as possible."
        else:
            msg = f"Building itinerary based on these details - for travel from {origin} to {destination}. " \
                f"the dates mentioned by user are from {dates[0].isoformat()} to {dates[-1].isoformat()}, style of travel is {style}. " \
                f"Make the itinerary as detailed as possible."
        
        st.chat_message("user").markdown(msg)
        st.session_state.itinerary_ui_messages.append({'type':'human', 'content': msg})

        with st.spinner("Generating itinerary..."):

            payload = {
                "origin": origin,
                "destination": destination,
                "dates": [d.isoformat() for d in dates] if isinstance(dates, tuple) else dates.isoformat(),
                "style": style,
                "feedback": None,
                "additional_info": additional_info,
                "thread_id": st.session_state.itinerary_thread_id,
                'itinerary_button_presses': st.session_state.itinerary_button_presses,
                'itinerary_text': None
            }

            for step in stream_graph(payload):
                
                key = list(step.keys())[0]
                if key == "Itineary_planner":
                    st.session_state.itinerary_text = step[key].get("itineary_text", "")
                    st.chat_message("assistant").markdown(display_itinerary(step))
                    for msg in reversed(step[key].get("messages", [])):
                        if msg.type == 'ai' and msg.content and msg.content.strip() != "":
                            st.session_state.itinerary_ui_messages.append({'type':'ai', 'content': display_itinerary(step)})
                            break

            st.session_state.itinerary_button_presses += 1

            st.session_state.is_generating = False

        st.rerun()
    