# streamlit_app.py

import streamlit as st

from app import get_chat, llm_turn, roll_to_future, speak_time
from voice.stt import transcribe_audio
from voice.tts import speak_text
from backend_logics.scheduler import (
    book_appointment,
    cancel_appointment,
    human_readable_slots,
    next_available,
)

# Streamlit Page Setup 
st.set_page_config(page_title="Confido AI Voice UI", layout="wide")

# Session State Defaults 
defaults = {
    "chat": None,
    "history": [],
    "current_booking": None,
    "call_active": False,
    "listening": False,
}
for key, val in defaults.items():
    st.session_state.setdefault(key, val)

# Utility Functions
def add_message(role, txt):
    if isinstance(txt, str) and txt.strip():
        st.session_state.history.append((role, txt))
        

# Voice Interaction Loop 
def run_voice_loop():
    chat = st.session_state.chat
    current_booking = st.session_state.current_booking

    greet = (
        chat.last.text
        if getattr(chat, "last", None)
        else "Hello, thank you for calling Confido Health. How may I help you today?"
    )
    add_message("assistant", greet)
    speak_text(greet)

    while st.session_state.call_active:
        with st.spinner("🎧 Listening…"):
            user_input = transcribe_audio(show_prompt=False)

        if not user_input:
            continue

        add_message("user", user_input)

        if any(w in user_input.lower() for w in ("bye", "goodbye", "exit", "that's it")):
            goodbye_msg = "Good-bye."
            add_message("assistant", goodbye_msg)
            speak_text(goodbye_msg)
            st.session_state.call_active = False
            break

        with st.spinner("💭 Thinking…"):
            data, question = llm_turn(chat, user_input)

        if question:
            add_message("assistant", question)
            speak_text(question)
            continue

        intent = data.get("intent")

        # Carry forward date from existing booking if rescheduling
        if intent in ("schedule", "reschedule") and not data.get("date") and current_booking:
            data["date"] = current_booking["date"]

        # Intent Handling 
        if intent == "schedule":
            name, date_, time_ = (
                data["name"],
                roll_to_future(data["date"]),
                data["time"],
            )
            if not all([name, date_, time_]):
                err = "I still need the name, date and time to book."
                add_message("assistant", err)
                speak_text(err)
                continue

            result = book_appointment(date_, time_, name)
            add_message("assistant", result)
            speak_text(result)
            if "confirmed" in result:
                st.session_state.current_booking = {"name": name, "date": date_, "time": time_}
                speak_text("Is there anything else I can help you with?")

        elif intent == "reschedule":
            if not current_booking:
                msg = "I don't have an appointment on file. What would you like to schedule?"
                add_message("assistant", msg)
                speak_text(msg)
                continue

            new_date = roll_to_future(data.get("date") or current_booking["date"])
            new_time = data.get("time")

            if not new_time:
                q = "What time would you like for the new appointment?"
                add_message("assistant", q)
                speak_text(q)
                continue

            cancel_appointment(**current_booking)
            result = book_appointment(new_date, new_time, current_booking["name"])
            add_message("assistant", result)
            speak_text(result)

            if "confirmed" in result:
                st.session_state.current_booking.update({"date": new_date, "time": new_time})
                speak_text("Anything else I can help you with?")

        elif intent == "cancel":
            if current_booking:
                msg = cancel_appointment(**current_booking)
                add_message("assistant", msg)
                speak_text(msg + " Good-bye.")
            else:
                msg = "I don't see an existing appointment to cancel."
                add_message("assistant", msg)
                speak_text(msg)
            st.session_state.call_active = False

        elif intent == "query_slots":
            req_date = roll_to_future(data.get("date"))
            if not req_date:
                q = "Which date would you like to check?"
                add_message("assistant", q)
                speak_text(q)
                continue

            slots = human_readable_slots(req_date)
            out = (
                f"Unfortunately there are no open times on {req_date}."
                if slots == "no remaining times"
                else f"The available times on {req_date} are: {slots}."
            )
            add_message("assistant", out)
            speak_text(out)

        else:
            fallback = "I can help with scheduling, rescheduling, cancelling, or checking availability."
            add_message("assistant", fallback)
            speak_text(fallback)


st.markdown("<h1 style='text-align: center;'>Confido AI Voice Assistant</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Click <strong>Start Call</strong> to begin</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([2, 1, 2])

with col2:
    if st.session_state.call_active:
        st.markdown("**Status: Live**")
        st.info("Listening…" if st.session_state.listening else "Thinking…")
        if st.button("End Call"):
            st.session_state.call_active = False
    else:
        if st.button("Start Call"):
            st.session_state.call_active = True
            st.session_state.listening = False
            st.session_state.chat = get_chat()
            run_voice_loop()
