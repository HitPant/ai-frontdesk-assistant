# Ai-frontdesk-assistant


## Project Overview

A voice-enabled AI assistant designed to automate healthcare front-desk tasks such as appointment scheduling.  
This assistant leverages:

- **Generative AI (LLM)** for understanding user intent and generating natural, task-focused responses.
- **Voice AI** modules including **Speech-to-Text (STT)** and **Text-to-Speech (TTS)** to drive spoken interactions.

The solution demonstrates practical engineering skills in combining conversational AI and voice interaction for real-world healthcare automation use cases.


## Tech Stack

| Component             | Technology Used                      |
|-----------------------|--------------------------------------|
| **LLM**               | Gemini 2.5 Pro (`google.generativeai`) |
| **Speech-to-Text (STT)** | Google Speech Recognition Library     |
| **Text-to-Speech (TTS)** | Google Cloud Text-to-Speech (TTS)     |
| **User Interface (UI)**  | Streamlit                           |
| **Programming Language** | Python 3.10 (recommended for compatibility) |



## Project Structure and Components

This project is organized into modular components, each responsible for a specific functionality in the voice-enabled AI assistant pipeline.

### `streamlit_app.py`
**Purpose:**  
Streamlit-based UI to run the voice assistant in a browser.

**Key Responsibilities:**
- Uses `streamlit` for the frontend interface.
- Maintains `st.session_state` to track chat history and booking state.
- Provides a "Start Call" button to trigger the call lifecycle.


### `app.py`
**Purpose:**  
Core logic for handling conversation flow and integrating with backend services.

**Key Responsibilities:**
- Loads the system prompt from `system_prompt.txt`.
- Interfaces with Gemini 2.5 Pro using `google.generativeai`.
- The `llm_turn()` function interprets Gemini's output into actionable JSON or follow-up queries.
- Handles all four main intents: `schedule`, `reschedule`, `cancel`, and `query_slots`.
- Uses `scheduler.py` for simulated calendar interactions.


### `stt.py`
**Purpose:**  
Speech-to-text (STT) module using Google Speech Recognition.

**Key Responsibilities:**
- Captures microphone input using the `speech_recognition` library.
- Includes timeout settings and basic error handling.
- Prompts the user to repeat when speech is unclear or not captured.


### `tts.py`
**Purpose:**  
Text-to-speech (TTS) using Google Cloud Text-to-Speech.

**Key Responsibilities:**
- Uses `google.cloud.texttospeech` to synthesize assistant responses.
- Plays generated audio using `pydub`.
- Cleans up temporary audio files after playback.


**Purpose:**  
Handles backend logic for appointment scheduling.

**Key Responsibilities:**
- Functions include: `book_appointment`, `cancel_appointment`, `next_available`, and `human_readable_slots`.
- Uses a hardcoded calendar with limited slots for demo purposes.


### `system_prompt.txt`
**Purpose:**  
Defines the assistant’s role, behavior, and communication protocol.

**Key Responsibilities:**
- Enumerates the four main intents: `schedule`, `reschedule`, `cancel`, `query_slots`.
- Instructs the LLM on when to return structured JSON and when to ask clarifying questions.


## How to Run the Project

Follow these steps to set up and run the voice-enabled AI assistant locally.


### 1. Environment Setup

Ensure you are using **Python 3.10**.
#### 1.1 Clone the Repository

```bash
git clone https://github.com/HitPant/ai-frontdesk-assistant.git
cd ai-frontdesk-assistant
```

#### 1.2 Create Virtual Environment

```bash
python3.10 -m venv voice-assistant

Linux:
source voice-assistant/bin/activate
Windows:
voice-assistant\Scripts\activate
```
### 2. Requirements
```bash
pip install -r requirements.txt
```

### 3. Set API Keys

Create a `.env` file in the root directory with the following content:
```bash
GOOGLE_API_KEY=your_google_generativeai_key  
GOOGLE_APPLICATION_CREDENTIALS=path_to_google_tts_service_account.json
```

### 4. Run the App
Launch the Streamlit interface:
```bash
streamlit run streamlit_app.py
```
