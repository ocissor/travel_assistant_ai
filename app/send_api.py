import requests
import uuid
import sys
sys.path.append("D:/travel_assistant_ai/app")
from database import collection  # Import your MongoDB collection
import pickle
import json
from datetime import datetime
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()
thread_id = str(uuid.uuid4())
API_URL = "http://127.0.0.1:8000/chat"

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

def send_post_request_to_planner_agent(user_message: str):
    payload = {
        "user_input": user_message,
        "thread_id": thread_id,
        "interrupt_called": False,
    }

    while True:
        interrupt_found = False
        for step in stream_graph(payload):
            #print("STEP:", step)
            print("\n")
            if '__interrupt__' not in step:
                key = list(step.keys())[0]
                messages = step[key].get('messages',[])
                if messages[-1].type == 'tool':
                    print(messages[-1].name)
            if '__interrupt__' in step:
                prompt = step['__interrupt__'][0].value
                user_reply = input(prompt + " ")
                payload = {
                    "user_input": user_reply,
                    "thread_id": thread_id,
                    "interrupt_called": True,
                }
                interrupt_found = True
                break  # Exit for loop to restart streaming with resumed input

        if not interrupt_found:
            print("Conversation step complete.")
            break  # Exit while loop, conversation finished

# Start conversation
send_post_request_to_planner_agent("Get me hotels in Paris")

     
