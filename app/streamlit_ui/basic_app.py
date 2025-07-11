import streamlit as st


st.markdown(
    """
    <style>
    /* Target buttons in the sidebar */
    section[data-testid="stSidebar"] button {
        background-color: #262730;        /* Default background */
        color: white;                     /* Default text color */
        border: none;
        border-radius: 0.5rem;
    }

    section[data-testid="stSidebar"] button:hover {
        background-color: #4a4a4a !important;  /* Custom hover color */
        color: white !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Set wide layout and title
st.set_page_config(page_title="Chatbot", layout="wide")

# Define pages
PAGES = {
    "Chatbot": "💬 Chatbot",
    "File Q&A": "📁 File Q&A",
    "Chat with search": "🔍 Chat with search",
    "Langchain Quickstart": "⚡ Langchain Quickstart",
    "Langchain PromptTemplate": "📝 Langchain PromptTemplate",
    "Chat with user feedback": "📊 Chat with user feedback"
}

# Initialize session state
if "current_page" not in st.session_state:
    st.session_state.current_page = "Chatbot"

# --- Sidebar UI (No radio buttons, only buttons) ---
with st.sidebar:
    st.markdown("## ")
    for key in PAGES.keys():
        if st.button(PAGES[key], use_container_width=True):
            st.session_state.current_page = key

# --- Main Area ---
st.title("💬 Chatbot")
st.markdown("🚀 A Streamlit chatbot powered by OpenAI")

# Render content based on selected page
page = st.session_state.current_page

if page == "Chatbot":
    st.markdown("### 🤖 How can I help you?")
    st.text_input("Your message", key="user_input")
elif page == "File Q&A":
    st.markdown("### 📁 Upload a file to start Q&A.")
elif page == "Chat with search":
    st.markdown("### 🔍 Search-enabled chatbot.")
elif page == "Langchain Quickstart":
    st.markdown("### ⚡ Quickstart with Langchain")
elif page == "Langchain PromptTemplate":
    st.markdown("### 📝 Experiment with PromptTemplates")
elif page == "Chat with user feedback":
    st.markdown("### 📊 Collect and show feedback")

