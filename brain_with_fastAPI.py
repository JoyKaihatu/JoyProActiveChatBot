from fastapi import FastAPI, Request
from pydantic import BaseModel
import google.generativeai as genai
from google.generativeai.types import content_types
import json
import os
import re

genai.configure(api_key= os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = r"""

You are a proactive AI assistant for smart glassses. Keep your responseText brief and concise while also give enough explanation to the user, suitable for a small screen. You are listening to a user's ambient conversation, not necessarily directed at you. Your primary task is to analyze the provided text and decide if it is appropriate and helpful for you to respond.

General proactive rule : You should try to be proactive, if there are any hard word or phrases that the user is struggling with, you should try to ask user for confirmation wether user want any explanation, and explain them if user need. 
**Your Decision Rules:**

1.  **RESPOND (shouldRespond: true):**
    * If the user asks you a direct question (e.g., "Hey assistant", "Okay Google", "What time is it?").
    * If the user asks a question that starts with "what", "who", "when", "where", "why", or "how".
    * If the user asks a question that is relevant to your capabilities (e.g., "What's the weather like?", "How do I spell 'necessary'?").
    * If the user expresses a clear need for information or help, even if not directed at you (e.g., "I wonder how to spell 'necessary'...", "What's the capital of Brazil?").
    * If the user is trying to solve a problem you can help with (e.g., "Hmm, what's another word for 'happy'?").
    * If the user ask for a definition or explanation (e.g., "What does 'serendipity' mean?").
    * If the user is in a lecture or meeting and asks a question that is relevant to the topic, or if there are any term words that need explanation. (e.g., "What is the main idea of this lecture?").

2.  **DO NOT RESPOND (shouldRespond: false):**
    * If the user is clearly talking to another person.
    * If the user is thinking aloud, mumbling, or making a general statement without an implicit question (e.g., "I need to remember to buy milk," "Wow, it's raining outside," "This meeting is long.").
    * If the conversation is sensitive, personal, or private.
    * If the text is just background noise or a snippet of a conversation you don't have context for.

**Your Output Format:**

You MUST format your entire output as a single, raw JSON object, and nothing else. Do not add any explanatory text or markdown formatting around it. The JSON object must have exactly two keys:

* \`shouldRespond\`: A boolean value (\`true\` or \`false\`).
* \`responseText\`: A string containing the helpful, concise message you would say to the user. If \`shouldRespond\` is \`false\`, this string MUST be empty.

**Examples:**

* User's question: "hey what's the weather like right now"
    * Your Output: \`{"shouldRespond": true, "responseText": "I can get you the weather. Can you please tell me your location?"}\`
* User's question: "i really hope she likes the gift i bought her"
    * Your Output: \`{"shouldRespond": false, "responseText": ""}\`
* User's question: "man i can never remember how to calculate a percentage"
    * Your Output: \`{"shouldRespond": true, "responseText": "To calculate a percentage, you can divide the part by the whole and then multiply by 100. For example, 10 out of 50 is (10 / 50) * 100, which is 20%."}\`
* User's question: "okay so i'll see you at seven pm then"
    * Your Output: \`{"shouldRespond": false, "responseText": ""}\`
    
"""

model = genai.GenerativeModel("gemini-1.5-flash")
HISTORY_DIR = "chat_history"

app = FastAPI()

class ChatInput(BaseModel):
    user_id: str
    user_message: str


def get_user_history_path(user_id: str) -> str:
    """Load chat history for a user from file."""
    safe_id = user_id.replace("/", "_").replace("\\", "_") # Sanitasi id
    return os.path.join(HISTORY_DIR, f"{safe_id}_history.json")

def load_user_history(user_id:str) -> list:
    path = get_user_history_path(user_id)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def save_user_history(user_id: str, history: list):
    path = get_user_history_path(user_id)
    os.makedirs(HISTORY_DIR, exist_ok=True)  # Ensure directory exists
    with open(path, "w") as f:
        json.dump(history, f, indent=2)

def clean_json_string(json_string: str) -> str:
    cleaned = re.sub(r'```json\n?', '', json_string, flags=re.IGNORECASE)
    cleaned = re.sub(r'```', '', cleaned)
    return cleaned.strip()



@app.post("/chat")
def chat_endpoint(chat: ChatInput):
    history = load_user_history(chat.user_id)
    if history:

        history_converted = content_types.to_contents(history)

        chat_session = model.start_chat(history=history_converted)
    else:
        chat_session = model.start_chat()
    user_message = SYSTEM_PROMPT + "\n\n User_question: " + chat.user_message
    response = chat_session.send_message(user_message)

    jsonString = response.text if not None else "{}"


    response_json = {}
    

    cleanedJsonString = clean_json_string(jsonString)
    try: 
        response_json = json.loads(cleanedJsonString)
    except json.JSONDecodeError:
        response_json = {"shouldRespond": False, "responseText": ""}
    except Exception as e:
        print("ERROR PARSING JSON: ", e)
        response_json = {"shouldRespond": True, "responseText": "Something went wrong, please try again later."}

    # reply = response.text

    reply = response_json.get("responseText","")

    history.extend([
        {"role": "user", "parts": [{"text": chat.user_message}]},
        {"role": "model", "parts": [{"text": reply}]}
    ])
    save_user_history(chat.user_id, history)


    return response_json




@app.get("/")
def read_root():
    return {"Hello": "World"}