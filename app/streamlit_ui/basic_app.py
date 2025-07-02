import streamlit as st

user_input = st.text_input("Enter your message:")

if user_input:
    st.write("You entered:", user_input)
