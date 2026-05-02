import streamlit as st
import cohere
import os

co = cohere.Client(os.getenv("COHERE_API_KEY"))

st.title("My Chatbot 🤖")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("You:")

if user_input:
    response = co.chat(
        message=user_input,
        model="command-r7b-12-2024"
    )

    reply = response.text

    st.session_state.chat_history.append(("You", user_input))
    st.session_state.chat_history.append(("Bot", reply))

for sender, msg in st.session_state.chat_history:
    st.write(f"**{sender}:** {msg}")