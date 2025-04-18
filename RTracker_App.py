import streamlit as st
from collections import Counter
import json
import openai
import os

# --- Load OpenAI Key from Streamlit Secrets ---
OPENAI_KEY = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=OPENAI_KEY)

# --- Config ---
st.set_page_config(page_title="Beta App", layout="centered")

# --- Auth with PIN ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🔐 Beta App")
    st.text_input("Enter PIN", type="password", key="pin_input")
    if st.session_state.get("pin_input") == "2579":
        st.session_state.authenticated = True
    else:
        st.stop()

# --- Title ---
st.title("🎯 Beta App")

# --- Initialize Session State ---
for key in ["numbers", "wrong_predictions", "last_prediction", "ai_prediction"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- Data File ---
DATA_FILE = "data.json"
if os.path.exists(DATA_FILE) and not st.session_state["numbers"]:
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        st.session_state["numbers"] = data.get("numbers", [])
        st.session_state["wrong_predictions"] = data.get("wrong_predictions", [])

# --- Save Data ---
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "numbers": st.session_state["numbers"],
            "wrong_predictions": st.session_state["wrong_predictions"]
        }, f)

# --- Frequency-Based Prediction ---
def predict_by_frequency(numbers, wrongs):
    count = Counter(numbers)
    sorted_nums = sorted(count.items(), key=lambda x: x[1], reverse=True)
    return [num for num, _ in sorted_nums if num not in wrongs][:7]

# --- AI Prediction with GPT ---
def predict_by_ai(numbers):
    if not numbers:
        return []
    try:
        prompt = f"The past numbers are: {numbers}. Based on patterns and repetition, predict the next 5 to 7 numbers most likely to come next. Reply only with numbers separated by commas."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a pattern recognition expert."},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content.strip()
        return [int(n.strip()) for n in reply.split(",")
