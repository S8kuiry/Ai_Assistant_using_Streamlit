import os
os.environ["PYTHONPATH"] = os.getcwd()

import streamlit as st
import threading
from datetime import datetime
import requests

try:
    import speech_recognition as sr
    import pyttsx3
except ModuleNotFoundError:
    sr = None
    pyttsx3 = None

# ------------------ API Setup ------------------
import google.generativeai as genai
from google.generativeai import GenerativeModel

genai.configure(api_key="AIzaSyC6yIW-kR0l2IAyRSyX2E2rDn-QMNxPEuU")
model = GenerativeModel("gemini-1.5-flash")

# ------------------ Session State Setup ------------------
for key in ["reply", "query", "trigger_mic", "weather"]:
    st.session_state.setdefault(key, "" if key != "trigger_mic" else False)

# ------------------ Streamlit UI ------------------
st.set_page_config(page_title="AI Assistant", layout="centered", initial_sidebar_state="collapsed")
st.markdown("<h1 style='text-align:center;'>AI Assistant 🤖</h1>", unsafe_allow_html=True)

# ------------------ Text-to-Speech ------------------
if sr and pyttsx3:
    recognizer = sr.Recognizer()
    tts = pyttsx3.init()
    tts.setProperty('rate', 160)

    def speak(text):
        def run_tts():
            try:
                tts.say(text)
                tts.runAndWait()
            except RuntimeError:
                pass
        threading.Thread(target=run_tts).start()
else:
    def speak(text):
        st.warning("Text-to-speech is not available in this environment.")

# ------------------ Microphone Input ------------------
def mic():
    if not sr:
        st.error("Speech recognition is not available in this environment.")
        return
    with sr.Microphone() as source:
        st.toast("🎤 Speak now...", icon="🎧")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source)
            text = recognizer.recognize_google(audio)
            st.session_state.query = text
        except sr.UnknownValueError:
            st.warning("⚠️ Could not understand audio.")
        except sr.RequestError:
            st.error("❌ Could not connect to the speech recognition service.")

# ------------------ Weather Function ------------------
def fetch_weather_data(city_name):
    API_KEY = "0456d8a801108e2570a6200cad6c4b5a"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200:
            temp_c = round(data["main"]["temp"] - 273.15, 2)
            return {
                "City": data["name"],
                "Weather": data["weather"][0]["main"],
                "Temperature": f"{temp_c}°C",
                "Wind Speed": f"{data['wind']['speed']} km/h",
                "Humidity": f"{data['main']['humidity']}%"
            }
        else:
            st.sidebar.error(f"⚠️ {data.get('message', 'Unable to fetch weather data')}")
    except requests.exceptions.RequestException:
        st.sidebar.error("❌ Weather fetch error.")
    return None

# ------------------ Command Logic ------------------
def commands(query):
    text = query.lower()
    if text in ["hello", "hi", "hello there"]:
        response = "Hi, I am an LLM model. I am here to help you as per your needs."
    elif text in ["news", "latest news"]:
        response = "Opening [Google News](https://news.google.com)"
        st.markdown("[🗞️ Click here for Latest News](https://news.google.com)", unsafe_allow_html=True)
    elif text in ["time", "what is the time"]:
        response = datetime.now().strftime("Current Time is : %H:%M:%S")
    elif text in ["date", "today's date"]:
        response = datetime.now().strftime("Today's Date is : %d/%B/%Y")
    elif text in ["date and time"]:
        response = datetime.now().strftime("Current Time: %H:%M:%S || Date: %d/%B/%Y")
    elif text.startswith("open"):
        site = text.split("open", 1)[1].strip().replace(" ", "")
        response = f"Opening [Site](https://{site}.com)"
        st.markdown(f"[🔗 Click here to visit {site}](https://{site}.com)", unsafe_allow_html=True)
    elif text.startswith("play"):
        song = text.split("play", 1)[1].strip().replace(" ", "+")
        url = f"https://www.youtube.com/results?search_query={song}"
        response = f"Searching YouTube for: {song.replace('+', ' ')}"
        st.markdown(f"[▶️ Watch on YouTube]({url})", unsafe_allow_html=True)
    elif text.startswith("search for"):
        search = text.split("search for", 1)[1].strip().replace(" ", "+")
        url = f"https://www.google.com/search?q={search}"
        response = f"Searching Google for: {search.replace('+', ' ')}"
        st.markdown(f"[🔍 Search on Google]({url})", unsafe_allow_html=True)
    else:
        response = model.generate_content(text).text

    st.session_state.reply = response
    speak(response)

# ------------------ Voice Trigger Button ------------------
if sr:
    if st.button("🎤 Start Microphone", use_container_width=True):
        st.session_state.trigger_mic = True

    if st.session_state.trigger_mic:
        mic()
        st.session_state.trigger_mic = False
else:
    st.warning("🎙️ Voice input not available. Install 'speech_recognition' to enable microphone support.")

# ------------------ Query Form ------------------
with st.form(key="form"):
    st.header("Response :")
    ques = st.text_input("Enter Your Queries..", value=st.session_state.query)
    submit_btn = st.form_submit_button("🚀 Submit")

    if submit_btn and ques.strip():
        st.session_state.query = ques
        with st.spinner("⏳ Generating response..."):
            commands(st.session_state.query)
        st.session_state.query = ""

    with st.expander("Here is your answer...", expanded=True):
        st.code(st.session_state.reply, language="markdown")

# ------------------ Sidebar with Clock and Weather ------------------
now = datetime.now()
current_time = now.strftime("%H:%M:%S %p")
current_date = now.strftime("%d/%B/%Y")

with st.sidebar:
    st.markdown(f"""
        <div style='width: 100%; border-radius: 10px; display: flex; color:black;
        align-items: center; justify-content: center; background-color: white;
        z-index: 1; margin: auto; padding: 2px; margin-top: 20px;'>
            <h1 style='text-align: center; margin: 0;'>⏳ Welcome, User!</h1>
        </div>
    """, unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:left;font-size:25px;'>📅 {current_date}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align:left;margin-bottom:20px;font-size:25px;'>⏰ {current_time}</h1>", unsafe_allow_html=True)

    weather_city = st.text_input("Enter City : ", value=st.session_state.weather or "Kolkata")
    st.session_state.weather = weather_city
    weather_data = fetch_weather_data(weather_city)
    if weather_data:
        st.markdown("### 🌦️ Weather Info:")
        for key, value in weather_data.items():
            st.markdown(f"**{key}**: {value}")
