from pymongo import MongoClient
import os
from dotenv import load_dotenv
import sys
sys.path.append("D:/travel_assistant_ai/app")

load_dotenv()  # if you're using a .env file

client = MongoClient(os.getenv("MONGODB_CONNECTION_STRING"))  # e.g. "mongodb://localhost:27017/"
db = client["travel_assistant_db"]
collection = db["states"]