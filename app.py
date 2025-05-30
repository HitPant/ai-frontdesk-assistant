# app.py – Confido Voice Assistant (context-driven, no manual slots)

import os, json, re
from datetime import datetime, date as dt
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

from backend_logics import scheduler
from voice.stt import transcribe_audio
from voice.tts import speak_text


load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
SYSTEM_PROMPT = Path("prompts/system_prompt.txt").read_text(encoding="utf-8")

def get_chat() -> genai.ChatSession:
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro-preview-05-06",
        system_instruction=SYSTEM_PROMPT,
    )
    return model.start_chat(history=[])


def speak_and_print(txt: str):
    print(f"AI: {txt}")
    speak_text(txt)

def speak_time(hhmm: str) -> str:
    try:
        return datetime.strptime(hhmm, "%H:%M").strftime("%-I:%M %p")
    except Exception:
        return hhmm



def roll_to_future(date_str: str) -> str:

    if not date_str:
        return date_str

    # detect YYYY present
    if re.match(r"\d{4}-\d{2}-\d{2}$", date_str):
        d = dt.fromisoformat(date_str)
    else:
        # parse fuzzy then replace year with 2025
        d = dateparser.parse(date_str, fuzzy=True, dayfirst=True)
        d = d.replace(year=2025)

    if d < dt.today():
        d = d.replace(year=d.year + 1)       # avoid past dates

    return d.isoformat()

def llm_turn(chat, user_text: str):
    resp = chat.send_message(user_text)
    raw = resp.text.strip()
    m = re.search(r"\{[\s\S]*?\}", raw)
    if m:
        try:
            return json.loads(m.group(0)), None
        except json.JSONDecodeError:
            pass
    return None, raw


if __name__ == "__main__":
    chat = get_chat()
    greet = chat.last.text if getattr(chat, "last", None) else \
        "Hello, thank you for calling Confido Health. How may I help you today?"
    speak_and_print(greet)

    current_booking = None   # remembers confirmed appointment

    while True:
        user_input = transcribe_audio(show_prompt=True)
        if not user_input:
            continue
        match = re.search(r"\b(\d{1,2}:\d{2})\s*(?:am|pm)?\s*works\b", user_input, re.I)
        if match:
            user_input = match.group(0)   # Gemini will parse the time token

        print(f"You said: {user_input}")

        # polite exits
        if re.search(r"\b(good\s?bye|bye|that'?s it|no thanks|exit)\b", user_input, re.I):
            speak_text("Good-bye.")
            break

        data, question = llm_turn(chat, user_input)

    
        if question:
            speak_and_print(question)
            continue

        intent = data.get("intent")

        # preserve last known date if JSON omitted it (e.g. “move to 2 PM”)
        if intent in ("schedule", "reschedule") and not data.get("date"):
            if current_booking:
                data["date"] = current_booking["date"]


        # schedule
        if intent == "schedule":
            name, date_, time_ = (
                data["name"],
                roll_to_future(data["date"]),
                data["time"],
            )
            if not all([name, date_, time_]):
                speak_text("I still need the name, date and time to book.")
                continue

            result = scheduler.book_appointment(date_, time_, name)

            if "confirmed" in result:
                speak_and_print(result.replace(time_, speak_time(time_)))
                current_booking = {"name": name, "date": date_, "time": time_}
                speak_text("Is there anything else I can help you with?")
            else:
                # convert 24-hour time in rejection
                speak_and_print(result.replace(time_, speak_time(time_)))
                alt = scheduler.human_readable_slots(date_)
                if alt != "no remaining times":
                    speak_text(f"Available times that day: {alt}.")
                nxt_d, nxt_t = scheduler.next_available()
                if nxt_d:
                    speak_text(f"The next available slot is {nxt_d} at {nxt_t}.")
                speak_text("What time would you prefer?")

        # reschedule 
        elif intent == "reschedule":
            if not current_booking:
                speak_text("I don't have an appointment on file. What would you like to schedule?")
                continue

            new_date = roll_to_future(data["date"] or current_booking["date"])
            new_time = data["time"]
            if not new_time:
                speak_text("What time would you like for the new appointment?")
                continue

            scheduler.cancel_appointment(**current_booking)
            result = scheduler.book_appointment(new_date, new_time, current_booking["name"])

            if "confirmed" in result:
                speak_and_print(result.replace(new_time, speak_time(new_time)))
                current_booking.update({"date": new_date, "time": new_time})
                speak_text("Anything else I can help you with?")
            else:
                speak_and_print(result.replace(new_time, speak_time(new_time)))

        # cancel
        elif intent == "cancel":
            if current_booking:
                msg = scheduler.cancel_appointment(**current_booking)
                speak_and_print(msg + " Good-bye.")
                break
            else:
                speak_text("I don't see an existing appointment to cancel.")

        # query_slots
        elif intent == "query_slots":
            req_date = roll_to_future(data.get("date"))
            if not req_date:
                speak_text("Which date would you like to check?")
                continue

            slots_list = scheduler.human_readable_slots(req_date)
            if slots_list == "no remaining times":
                speak_text(f"Unfortunately there are no open times on {req_date}.")
            else:
                speak_text(f"The available times on {req_date} are: {slots_list}.")


        else:
            speak_text("I can help with scheduling, rescheduling, cancelling, "
                       "or checking availability.")
