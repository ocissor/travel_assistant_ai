import streamlit as st
import requests
import uuid
import sys
sys.path.append("D:/travel_assistant_ai/app")
from database import collection  # Import your MongoDB collection

API_URL = "http://127.0.0.1:8000/chat"  # FastAPI endpoint

st.set_page_config(page_title="✈️ Travel Assistant")

st.title("🌍 AI Travel Planner")
st.markdown("Plan your dream trip with the help of AI agents.")

# Text input for conversation
user_input = st.text_input("Your message:", key = "user_input", placeholder="Plan a trip to Tokyo next week")
def store_state_in_mongo(thread_id: str, state: dict):
    document = {
        "thread_id": thread_id,
        "state": state
    }
    result = collection.insert_one(document)
    print(f"✅ State stored with MongoDB _id: {result.inserted_id}") 

def show_messages(data):
    message_list = data['response']['planner']['messages']
    for message in message_list:
        if message['type'] == 'human':
            st.markdown(f"👤: {message['content']}")
        elif message['type'] == 'ai':
            st.markdown(f"🤖: {message['content']}")

# Button to send message
if st.button("Send"):
    if user_input.strip():
        with st.spinner("Getting Response..."):
            try:
                url = "http://127.0.0.1:8000/chat"
                payload = {
                    "user_input": user_input,
                    "thread_id": str(uuid.uuid4())
                }
                response = requests.post(url, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    show_messages(data)
                    # store_state_in_mongo(payload["thread_id"], data)
                    st.success("Response received!")

                else:
                    st.error("API Error" )
            except Exception as e:
                st.error(f"Request failed: {e}")


