import streamlit as st
import cohere
import os

co = cohere.Client(os.getenv("COHERE_API_KEY"))

st.title("My Chatbot 🤖")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 👇 initialize input state
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

def send_message():
    user_input = st.session_state.user_input

    if user_input:
        response = co.chat(
            message=user_input,
            model="command-r7b-12-2024"
        )

        reply = response.text

        st.session_state.chat_history.append(("You", user_input))
        st.session_state.chat_history.append(("Bot", reply))

        # 👇 clear input after sending
        st.session_state.user_input = ""

# 👇 bind input box to session state
st.text_input("You:", key="user_input")

# 👇 button to trigger send
st.button("Send", on_click=send_message)

# display chat
for sender, msg in st.session_state.chat_history:
    st.write(f"**{sender}:** {msg}")