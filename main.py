import os
import pyttsx3
import speech_recognition as sr
from google.cloud import dialogflow_v2 as dialogflow

# Set up credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Yuvraj\OneDrive\Desktop\langGraph\DialogFlow\intelligent-ivr-jiud-fdd92f56d16f.json"

# Dialogflow config
project_id = "intelligent-ivr-jiud"
session_id = "user-session-1"
language_code = "en"

# Initialize text-to-speech engine
engine = pyttsx3.init()

# Dialogflow intent detection function
def detect_intent_text(project_id, session_id, text, language_code='en'):
    session_client = dialogflow.SessionsClient()
    session = session_client.session_path(project_id, session_id)

    text_input = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return response.query_result

# Function to convert text to speech
def speak(text):
    engine.say(text)
    engine.runAndWait()

# Function to listen to user's voice input
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\n🎤 Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {text}")
        return text
    except sr.UnknownValueError:
        print("😕 Could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"❌ Could not request results; {e}")
        return None

# Main loop
print("🤖 Start talking to your Dialogflow agent (say 'exit' to quit)...\n")
while True:
    user_input = listen()
    if not user_input:
        continue
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("👋 Goodbye!")
        speak("Goodbye!")
        break

    result = detect_intent_text(project_id, session_id, user_input, language_code)
    print(f"🤖 Dialogflow Response: {result.fulfillment_text}")
    speak(result.fulfillment_text)
