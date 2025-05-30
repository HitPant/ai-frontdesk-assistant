import speech_recognition as sr
from voice.tts import speak_text

def transcribe_audio(show_prompt=True) -> str:
    r = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            if show_prompt:
                print("Speak now....")
            audio = r.listen(source, timeout=15, phrase_time_limit=20)

        return r.recognize_google(audio)

    except sr.UnknownValueError:
        speak_text("I'm sorry, I didn't catch that. Please repeat your response.")
        return ""
    except sr.RequestError as e:
        print(f"[STT ERROR] API request failed: {e}")
        return ""
    except sr.WaitTimeoutError:
        speak_text("Sorry, I didn't hear anything. Could you try again?")
        return ""
