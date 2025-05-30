from google.cloud import texttospeech
from pydub import AudioSegment
from pydub.playback import play
import os
import tempfile

def speak_text(text: str, language_code = "en-US", gender = "NEUTRAL"):

    try:
        client = texttospeech.TextToSpeechClient()

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            ssml_gender=getattr(texttospeech.SsmlVoiceGender, gender.upper(), texttospeech.SsmlVoiceGender.NEUTRAL)
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as out:
            out.write(response.audio_content)
            file_path = out.name

        sound = AudioSegment.from_mp3(file_path)
        play(sound)

    except Exception as e:
        print(f"[TTS ERROR] {e}")
    
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
