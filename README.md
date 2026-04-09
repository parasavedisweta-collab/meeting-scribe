# Meeting Scribe — AI Underwriting Copilot

A real-time AI assistant for loan underwriters. It listens to live conversations between underwriter and borrower, transcribes speech, identifies speakers (i.e. who is underwriter vs who is borrower), and suggests the next best question based on underwriting methodology.

## Features

- **Live transcription** — speech-to-text using faster-whisper (runs locally, no cloud STT costs)
- **Speaker diarization** — automatically tags Underwriter vs Borrower turns
- **AI Copilot** — suggests next questions following income assessment → red flag sequence
- **Interactive chat** — underwriter can ask the AI anything mid-call (e.g. "what is the FOIR?", "should I approve this?") and get instant answers in context
- **Question checklist** — tracks which topics have been covered in real time
- **Dual LLM support** — toggle between Gemini 2.5 Flash and GPT-4o-mini
- **Demo scenarios** — pre-loaded borrower profiles (Vikram Malhotra, Priya Mehta) for testing

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + WebSocket |
| Speech-to-Text | faster-whisper (base.en, int8, CPU) |
| Speaker Diarization | SpeechBrain ECAPA-TDNN |
| AI Copilot | Gemini 2.5 Flash / GPT-4o-mini |
| Frontend | Vanilla JS + Tailwind CSS |

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/parasavedisweta-collab/meeting-scribe.git
cd meeting-scribe
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add API keys

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here
```

- **Gemini**: Get a key at [aistudio.google.com](https://aistudio.google.com)
- **OpenAI**: Get a key at [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

You only need one — the UI has a toggle to switch between them.

### 4. Run

```bash
python server.py
```

Open **http://localhost:8001** in your browser.

## Usage

1. Select a borrower scenario from the left panel
2. Click **Record** to start listening
3. Have the underwriter-borrower conversation — the transcript appears live
4. AI suggestions appear in the right panel after each segment, guiding the underwriter on what to ask next
5. **Chat with the AI** — type any question in the chat panel mid-call (e.g. *"What is this borrower's FOIR?"*, *"Should I ask for more documents?"*) and get instant context-aware answers
6. The checklist on the right tracks which income and red flag topics have been covered
7. Use the **Gemini / ChatGPT** toggle in the nav to switch LLM providers at any time

## Project Structure

```
meeting-scribe/
├── server.py          # FastAPI backend — WebSocket, STT, diarization, LLM
├── scenarios.py       # Demo borrower profiles
├── static/
│   └── index.html     # Frontend (single-page app)
├── requirements.txt
├── .gitignore
└── .env               # API keys (not committed)
```

## Notes

- First run will download the SpeechBrain model (~100MB) automatically
- Runs entirely on CPU — no GPU required
- `.env` is gitignored — never commit your API keys
