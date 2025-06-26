import streamlit as st
import requests
import uuid
import sys
sys.path.append("D:/travel_assistant_ai/app")
from database import collection

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

# Show conversation so far
for msg in st.session_state.ui_messages:
    if msg["type"] == "human":
        st.chat_message("user").markdown(msg["content"])
    elif msg["type"] == "ai":
        st.chat_message("assistant").markdown(msg["content"])

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
                "thread_id": st.session_state.thread_id
            }
            response = requests.post(API_URL, json=payload)

            if response.status_code == 200:
                data = response.json()

                for msg in reversed(data["response"]["planner"]["messages"]):
                    if msg["type"] == "ai":
                        st.chat_message("assistant").markdown(msg["content"])
                        st.session_state.ui_messages.append(msg)
                        break

            else:
                st.error(f"API Error: {response.status_code}")

        except Exception as e:
            st.error(f"Request failed: {e}")
