# StudyForge

StudyForge turns a confusing topic in your class notes into a short, grounded study guide: a plain-language explanation, an example, and a quick check for understanding.

## Run locally

Requirements: Node.js 20.19+ (or 22.12+) and Python 3.10+.

1. Install [Ollama](https://ollama.com/) and download Gemma 3 4B, the default open-weight model:

   ```powershell
   ollama pull gemma3:4b
   ```

2. In a terminal, start the API from the project directory:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r backend\requirements.txt
   uvicorn backend.main:app --reload --port 8000
   ```

3. In a second terminal, start the web app:

   ```powershell
   npm install
   npm run dev
   ```

4. Open the local URL printed by Vite (usually `http://localhost:5173`).

StudyForge sends the selected note passages only to Ollama on your own computer. It does not have accounts, analytics, or a hosted AI endpoint. After you have downloaded Gemma, Ollama can generate responses offline. Gemma is an open-weight model; Ollama is the local runner. Review [Gemma's terms](https://ai.google.dev/gemma/terms) if you plan to redistribute model weights.

Run the backend checks with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py"
```

To use the smaller Qwen 2.5 3B alternative, download it and set `OLLAMA_MODEL` before starting the API:

```powershell
ollama pull qwen2.5:3b
$env:OLLAMA_MODEL = "qwen2.5:3b"
uvicorn backend.main:app --reload --port 8000
```
