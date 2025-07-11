import streamlit as st
import importlib

# Set page config
st.set_page_config(
    page_title="🌍 Travel Assistant",
    page_icon="✈️",
    layout="wide"
)

# Page mapping: Display name ➝ Module file (without .py)
PAGES = {
    "🏠 Home": "home",
    "💬 Chatbot": "chatbot",
    "🗺️ Itinerary Builder": "itinerary",
    "🌦️ Weather Info": "weather",
    "👕 Clothing Recommendations": "clothing"
}

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "🏠 Home"


# Sidebar UI
with st.sidebar:
    st.title("🧭 Travel Assistant")
    st.markdown("---")
    
    # Navigation buttons
    for page_name in PAGES:
        if st.button(page_name, use_container_width=True):
            st.session_state.current_page = page_name

    # Footer or credit
    st.markdown("---")
# # Main content
# st.markdown(f"# {st.session_state.current_page}")

if st.session_state.current_page == "🏠 Home":
    st.title("🌍 Travel Assistant")
    st.markdown("Welcome to your **AI-powered travel companion**. Whether you're planning a quick weekend getaway or a full itinerary across the globe, we've got you covered!")
    st.markdown("Please select a feature from the sidebar to get started.")
# Load and run selected page module
else:
    module_name = PAGES[st.session_state.current_page]
    page_module = importlib.import_module(module_name)
    page_module.app()  # Calls the `app()` function in that file
