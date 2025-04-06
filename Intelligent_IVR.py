from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import json
import os
import random
import whisper
import pyttsx3
import speech_recognition as sr
import tempfile

whisper_model = whisper.load_model("base")

os.environ["OPENAI_API_KEY"] = "your-api-key"

# Dummy account database
accounts = {
    "1234": {"balance": "₹15,000", "loan_status": "Active"},
    "5578": {"balance": "₹8,500", "loan_status": "Closed"},
    "9999": {"balance": "₹2,000", "loan_status": "Pending"},
}

def listen_with_local_whisper() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        audio = recognizer.listen(source)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
        tmp_file.write(audio.get_wav_data())
        result = whisper_model.transcribe(tmp_file.name)
    os.remove(tmp_file.name)
    return result["text"].strip()

def speak_text(text: str):
    print(f"🤖 {text}")
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()


# Tools
def authenticate_user(last4):
    return last4 in accounts

def check_balance(last4):
    return accounts.get(last4, {}).get("balance", "Account not found")

def loan_status(last4):
    return accounts.get(last4, {}).get("loan_status", "Account not found")

def greet_user():
    greetings = [
        "Hey there! How can I help you today?",
        "Hi! What can I do for you?",
        "Hello! How may I assist you?",
        "Good to hear from you. How can I help?",
        "Hi! Hope you're doing well. What would you like to know?"
    ]
    return random.choice(greetings)

tools = {
    "greet_user": greet_user,
    "check_balance": check_balance,
    "loan_status": loan_status,
    "authenticate_user": authenticate_user
}

# SYSTEM PROMPT
SYSTEM_PROMPT = """
You are a friendly human-like AI IVR assistant. You will follow a structured approach using START, PLAN, ACTION, OBSERVATION, and OUTPUT.

💬 Behavior Flow:
1. If user says "Hi", "Hello", etc., greet them using the greet_user() tool.
2. If user asks for account-related info like check_balance or loan_status, authenticate them first using the last 4 digits of their account number.
3. Once the user is authenticated, they can use check_balance or loan_status freely without re-authenticating.
4. Talk naturally, like a real assistant would, using casual language when appropriate.

🛠 Available Tools:
- function greet_user(): str  
Returns a friendly greeting like “Hi there! How can I help you today?”

- function authenticate_user(account_last4: str): str  
Checks if user has a valid bank account. Returns “Authenticated” or “Authentication failed”.

- function check_balance(account_last4: str): str  
Returns the account balance using the last 4 digits.

- function loan_status(account_last4: str): str  
Returns the loan status using the last 4 digits.

🧠 Example:
START  
{ "type": "user", "user": "Hi" }  
{ "type": "plan", "plan": "User greeted. I will greet back." }  
{ "type": "action", "function": "greet_user", "input": "" }  
{ "type": "observation", "observation": "Hey there! What can I do for you today?" }  
{ "type": "output", "output": "Hey there! What can I do for you today?" }

START  
{ "type": "user", "user": "I want to check my balance. My account number is 1234" }  
{ "type": "plan", "plan": "User is asking for balance. First I will authenticate the user." }  
{ "type": "action", "function": "authenticate_user", "input": "1234" }  
{ "type": "observation", "observation": "Authenticated" }  
{ "type": "plan", "plan": "User is authenticated. Now I will call check_balance" }  
{ "type": "action", "function": "check_balance", "input": "1234" }  
{ "type": "observation", "observation": "₹15,000" }  
{ "type": "output", "output": "Your account balance is ₹15,000" }

START  
{ "type": "user", "user": "Can you also tell me my loan status?" }  
{ "type": "plan", "plan": "User is already authenticated. I will call loan_status directly" }  
{ "type": "action", "function": "loan_status", "input": "1234" }  
{ "type": "observation", "observation": "Active" }  
{ "type": "output", "output": "Your loan status is Active" }

"""

# LangChain Setup
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

messages = [SystemMessage(content=SYSTEM_PROMPT)]

while True:
    query = listen_with_local_whisper()
    print(f"[You said]: {query}")
    user_input = {"type": "user", "user": query}
    messages.append(HumanMessage(content=json.dumps(user_input)))

    while True:
        response = llm.invoke(messages)
        content = response.content
        print(f"[AI]: {content}")
        messages.append(AIMessage(content=content))

        try:
            lines = content.strip().splitlines()
            for line in reversed(lines):  # Check from last to first
                try:
                    result = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                print("No valid JSON found in the response.")
                break
        except Exception as e:
            print("Error parsing response:", e)
            break

        if result["type"] == "output":
            speak_text(result["output"])
            break
        elif result["type"] == "action":
            func = result["function"]
            input_data = result["input"]
            if func == "authenticate_user":
                obs = "Authenticated" if authenticate_user(input_data) else "Authentication failed"
            else:
                obs = tools[func](input_data)
            obs_msg = {"type": "observation", "observation": obs}
            messages.append(HumanMessage(content=json.dumps(obs_msg)))
