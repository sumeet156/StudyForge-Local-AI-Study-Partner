# StudyForge

StudyForge is a local-first AI study partner. Paste in class notes, name a topic that feels confusing, and get a short study guide with a plain-language explanation, an example, a quick-check question, a sample answer, and the note passages used to make the guide.

The project was built for the Hacktoberfest 2026 “Build for a Friend” theme: make a practical study aid that can help someone learn from their own class notes.

## Youtube live Demo

[![Watch the StudyForge demo](https://img.youtube.com/vi/lGkjBS4V6fE/hqdefault.jpg)](https://www.youtube.com/watch?v=lGkjBS4V6fE)

## What it does

1. Accepts up to 30,000 characters of notes and a topic or question of up to 200 characters.
2. Splits the notes into passages and ranks them against the topic using local keyword scoring.
3. Selects up to five matching passages and sends those excerpts to a locally running Ollama model.
4. Asks the model to return a focused guide grounded in those excerpts.
5. Shows the explanation, example, quick check, sample answer, and source passages in the browser.

If the topic has no matching keywords in the notes, StudyForge asks you to try wording that appears in the notes rather than generating a guide from unrelated material.

## How the local AI approach works

- **Gemma 3 4B** is the default open-weight model. **Ollama** runs the model locally and provides its local API.
- The browser talks to the StudyForge API, and the API talks to Ollama on the same computer. The Vite development server proxies `/api` requests to the backend.
- StudyForge does not use a hosted AI endpoint, accounts, or analytics. It does not save notes to a database; notes are held in the page while it is open.
- Only the passages selected for a request are sent to Ollama, not the full notes document.
- After you have downloaded the model, generation can run without an internet connection. Internet access is needed for initial software, dependency, and model downloads.
- The model can still make mistakes. Check the displayed source passages and compare important information with your course materials.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- Node.js 20.19+ or 22.12+ (required by the current Vite setup)
- npm
- [Ollama](https://ollama.com/)
- Enough memory and disk space for the model you choose; model performance depends on your computer

## Setup and run

Run all commands from the StudyForge project directory. Keep Ollama running while using the app.

### 1. Install and download the model

Install Ollama, then open a terminal and download the default model:

```powershell
ollama pull gemma3:4b
```

You can confirm it is installed with:

```powershell
ollama list
```

On Windows and macOS, Ollama normally runs as a background application. If it is not running, start the Ollama application before continuing. On Linux, start the Ollama service using the installation instructions for your system.

### 2. Set up and start the backend

**Windows PowerShell**

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell blocks activation of the virtual environment, either use the Python executable directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS or Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Leave this terminal open. The API listens on `http://127.0.0.1:8000`.

### 3. Set up and start the frontend

Open a second terminal in the project directory:

```bash
npm install
npm run dev
```

Open the local URL printed by Vite, normally `http://localhost:5173`. If that port is already in use, Vite may print a different port; use the URL it provides.

### 4. Use StudyForge

1. Click **Try sample notes**, or paste your own notes into **Your notes**.
2. Enter a focused question or topic in **The bit you want to understand**. For example: `How does the Calvin cycle make glucose?`
3. Click **Help me understand** and wait for the local model to respond. The first request can take longer while the model loads.
4. Read the explanation and example, try answering the quick-check question, then select **Reveal a sample answer** if you want to compare.
5. Expand **See the notes behind this guide** to review the passages selected from your notes.

### Demo notes

Paste the following notes and ask, **“How do the light-dependent reactions help the Calvin cycle make sugar?”**

```text
Photosynthesis is the process plants use to convert light energy into chemical energy stored in glucose. It mainly takes place in chloroplasts, which contain chlorophyll. Plants take in carbon dioxide from the air and water through their roots. Oxygen is released as a by-product.

Photosynthesis has two main stages. The light-dependent reactions happen in the thylakoid membranes. Chlorophyll absorbs sunlight, and that energy is used to split water molecules. This releases oxygen and produces ATP and NADPH, which carry energy.

The Calvin cycle happens in the stroma of the chloroplast. It uses carbon dioxide, ATP, and NADPH to build sugar molecules. The Calvin cycle does not directly require light, but it depends on ATP and NADPH produced by the light-dependent reactions.

Photosynthesis stores energy in glucose. Cellular respiration is a separate process in which cells break down glucose to release usable energy.
```

## Choose a different Ollama model

The default model is set in `backend/main.py` to `gemma3:4b`. To use Qwen 2.5 3B instead, download it and set `OLLAMA_MODEL` in the backend terminal **before starting or restarting the API**.

**Windows PowerShell**

```powershell
ollama pull qwen2.5:3b
$env:OLLAMA_MODEL = "qwen2.5:3b"
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**macOS or Linux**

```bash
ollama pull qwen2.5:3b
export OLLAMA_MODEL=qwen2.5:3b
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Environment variables apply only to the current terminal session. To change back to the default, close that terminal and start the backend in a new one without setting `OLLAMA_MODEL`. The API expects Ollama at `http://127.0.0.1:11434` by default; set `OLLAMA_URL` before starting the API if your Ollama server uses a different address.

## Verify the installation

### Check local AI availability

With Ollama and the backend running, open:

```text
http://127.0.0.1:8000/api/health
```

The response includes the configured model and whether Ollama reports it as available, for example:

```json
{"available":true,"model":"gemma3:4b"}
```

You can also open the interactive API documentation at `http://127.0.0.1:8000/docs`.

### Run backend tests

From the project directory:

**Windows PowerShell**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py"
```

**macOS or Linux** (with the virtual environment activated)

```bash
python -m unittest discover -s backend -p "test_*.py"
```

The backend tests cover note retrieval and API behavior. They do not require you to generate a model response for every test.

### Build the frontend

```bash
npm run build
```

This runs the TypeScript check and creates a production build in `dist/`. To preview that build locally, run `npm run preview` and open the URL Vite prints.

## Troubleshooting

### “Local AI not connected” or the health check says `available: false`

- Confirm Ollama is running.
- Run `ollama list` and make sure the configured model is installed. The default is `gemma3:4b`.
- Check that the API is running on port `8000`.
- If you changed the model or `OLLAMA_URL`, restart the backend in the same terminal where those environment variables are set.

### “Ollama is not running”

Start the Ollama application or service, then submit the question again. The API and the model runner are separate processes; starting the frontend and backend alone does not start Ollama.

### The model takes a long time or times out

The first request can take longer because Ollama may need to load the model into memory. Wait for it to finish and retry. If it repeatedly times out, close other memory-intensive applications or try a smaller model supported by your computer.

### “I couldn't find that topic in these notes”

StudyForge retrieves passages using keyword overlap. Rephrase the topic with words that appear in your notes, or check that the notes were pasted into the notes field. It cannot retrieve useful passages if the topic has no matching terms.

### The frontend cannot reach the API

- Keep both the backend and frontend terminals running.
- Confirm the backend is listening at `http://127.0.0.1:8000`.
- Open the Vite URL printed by `npm run dev`; requests under `/api` are proxied to the backend.
- If port `8000` is already occupied, stop the other service or update the proxy in `vite.config.ts` to match the backend port.

## Project structure

```text
StudyForge/
├── backend/
│   ├── main.py             # FastAPI endpoints, note retrieval, Ollama integration
│   ├── requirements.txt    # Python dependencies
│   └── test_main.py        # Backend tests
├── src/
│   ├── App.tsx             # Study form and generated-guide UI
│   ├── main.tsx            # React entry point
│   └── style.css           # App styles
├── index.html
├── package.json            # Frontend scripts and dependencies
├── vite.config.ts          # Vite configuration and API proxy
└── README.md
```

## API overview

- `GET /api/health` — reports whether the configured Ollama model is available.
- `POST /api/study` — accepts JSON with `notes` and `topic`; returns `explanation`, `example`, `question`, `answer`, and `sources`.
- `GET /docs` — FastAPI's interactive API documentation.

## Privacy, model, and limitations

StudyForge is designed to run on your own computer: the frontend sends requests to its local backend, which sends the selected note excerpts to your local Ollama server. The project does not include a cloud AI service or persistent note storage. Avoid treating AI-generated study material as authoritative; verify it against your original notes and trusted course sources.

Gemma is an open-weight model, and Ollama is the local model runner. Review [Gemma's terms](https://ai.google.dev/gemma/terms) before redistributing model weights. StudyForge does not package model weights.
