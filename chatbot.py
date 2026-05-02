import cohere
import os

co = cohere.Client(os.getenv("COHERE_API_KEY"))


chat_history = []

while True:
    user_input = input("You: ")

    response = co.chat(
        message=user_input,
        chat_history=chat_history,
        model="command-a-03-2025"   # Cohere chat model
    )

    reply = response.text
    print("Bot:", reply)

    # store conversation
    chat_history.append({"role": "USER", "message": user_input})
    chat_history.append({"role": "CHATBOT", "message": reply})