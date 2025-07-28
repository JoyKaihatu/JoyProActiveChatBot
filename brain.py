import google.generativeai as genai
import os

from flask import Flask, request, jsonify
from flask_cors import CORS  # To allow requests from TypeScript app

app = Flask(__name__)
CORS(app)  # Allow all origins; in production, restrict this


# Authenticate with your API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Choose the model
model = genai.GenerativeModel("gemini-1.5-flash")

# Store history per user/session (in memory)
chat_histories = {}

@app.route('/receive-text', methods=['POST'])
def receive_text():
    data = request.get_json()
    text = data.get('text')
    print(f"Received text: {text}")
    return jsonify({'message': f'Text received: {text}'}), 200



def chat_with_user(user_id: str, user_message: str) -> str:
    # Load prior history or start new
    history = chat_histories.get(user_id, [])

    # Start chat session with history
    chat = model.start_chat(history=history)

    # Send user message
    response = chat.send_message(user_message)

    # Get text reply
    reply = response.text

    # Update history
    updated_history = history + [
        {"role": "user", "parts": [{"text": user_message}]},
        {"role": "model", "parts": [{"text": reply}]}
    ]

    # Save back to memory
    chat_histories[user_id] = updated_history

    return reply

# if __name__ == "__main__":
#     user_id = "user123"
#     user_message = "Hello, how are you?"
    
#     # Simulate a chat
#     while True:
#         user_message = input(f"User ({user_id}): ")
#         if user_message.lower() in ["exit", "quit"]:
#             print("Exiting chat.")
#             break
#         reply = chat_with_user(user_id, user_message)
#         print(f"Bot reply: {reply}")

if __name__ == '__main__':
    app.run(port=5000)
