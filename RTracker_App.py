import streamlit as st
from collections import Counter
import json
import openai
import os

# ✅ HARDCODED OpenAI API KEY (enter ONCE, never again)
OPENAI_KEY = "YOUR_OPENAI_KEY_HERE"
client = openai.OpenAI(api_key=OPENAI_KEY)

# --- CONFIG ---
st.set_page_config(page_title="Beta App", layout="centered")

# --- PIN Login ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if not st.session_state.authenticated:
    st.title("🔐 Beta App")
    st.text_input("Enter PIN", type="password", key="pin_input")
    if st.session_state.get("pin_input") == "2579":
        st.session_state.authenticated = True
    else:
        st.stop()

# --- TITLE ---
st.title("🎯 Beta App")

# --- Init Session ---
for key in ["numbers", "wrong_predictions", "last_prediction", "ai_prediction"]:
    if key not in st.session_state:
        st.session_state[key] = []

# --- Load Local History ---
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

# --- AI Prediction ---
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
        return [int(n.strip()) for n in reply.split(",") if n.strip().isdigit()]
    except Exception as e:
        st.warning("⚠️ AI prediction failed, using backup.")
        return predict_by_frequency(numbers, st.session_state["wrong_predictions"])

# --- Submit Numbers ---
def handle_submission():
    raw_input = st.session_state.get("input_box", "")
    entries = [int(n.strip()) for n in raw_input.split(",") if n.strip().isdigit()]
    if entries:
        st.session_state["numbers"].extend(entries)
        st.session_state["last_prediction"] = predict_by_frequency(
            st.session_state["numbers"], st.session_state["wrong_predictions"]
        )
        st.session_state["ai_prediction"] = predict_by_ai(st.session_state["numbers"])
        save_data()
        st.session_state["input_box"] = ""

# --- Input Box ---
st.subheader("🎲 Enter Numbers (e.g. 5 or 12,14,36)")
st.text_input("Enter here", key="input_box", on_change=handle_submission)
st.button("Submit", on_click=handle_submission)

# --- Predictions Display ---
if st.session_state["last_prediction"]:
    st.subheader("📈 Frequency Prediction")
    st.success(", ".join(map(str, st.session_state["last_prediction"])))

if st.session_state["ai_prediction"]:
    st.subheader("🤖 AI Predicted")
    st.success(", ".join(map(str, st.session_state["ai_prediction"])))

# --- Wrong Flag ---
st.subheader("❌ Prediction was wrong?")
if st.button("Mark as Wrong"):
    st.session_state["wrong_predictions"].extend(
        st.session_state["last_prediction"] + st.session_state["ai_prediction"]
    )
    save_data()
    st.warning("Marked as incorrect.")

# --- Correction Input ---
with st.form("correct_form"):
    st.text_input("✅ Enter correct number(s)", key="correct_entry")
    if st.form_submit_button("Submit Correction"):
        correction = st.session_state.get("correct_entry", "")
        numbers = [int(n.strip()) for n in correction.split(",") if n.strip().isdigit()]
        if numbers:
            st.session_state["numbers"].extend(numbers)
            st.session_state["last_prediction"] = predict_by_frequency(
                st.session_state["numbers"], st.session_state["wrong_predictions"]
            )
            st.session_state["ai_prediction"] = predict_by_ai(st.session_state["numbers"])
            save_data()
            st.success("Correction added.")
            st.experimental_rerun()

# --- History Table ---
if st.session_state["numbers"]:
    st.subheader("📊 History & Frequency")
    count = Counter(st.session_state["numbers"])
    table = sorted(count.items(), key=lambda x: (-x[1], x[0]))
    st.table({
        "Number": [num for num, _ in table],
        "Played": [freq for _, freq in table]
    })

# --- Reset Button ---
if st.button("🔁 Reset All Data"):
    st.session_state["numbers"].clear()
    st.session_state["wrong_predictions"].clear()
    st.session_state["last_prediction"].clear()
    st.session_state["ai_prediction"].clear()
    save_data()
    st.success("All data cleared.")
