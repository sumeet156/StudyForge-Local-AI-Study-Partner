import math
import os
import re
from collections import Counter

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
MAX_NOTES_LENGTH = 30_000
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "what", "when", "where", "which", "who", "why", "with", "you",
}

app = FastAPI(title="StudyForge local study API")


class StudyRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=MAX_NOTES_LENGTH)
    topic: str = Field(min_length=1, max_length=200)


class StudyContent(BaseModel):
    explanation: str
    example: str
    question: str
    answer: str


class StudyGuide(StudyContent):
    sources: list[str]


def tokenize(text: str) -> list[str]:
    return [
        word.lower()
        for word in re.findall(r"[A-Za-z0-9]+", text)
        if len(word) > 1 and word.lower() not in STOP_WORDS
    ]


def split_notes(notes: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", notes.strip())
    passages: list[str] = []
    current = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + len(sentence) + 1 > 650:
            passages.append(current)
            current = ""
        current = f"{current} {sentence}".strip()

    if current:
        passages.append(current)
    return passages


def retrieve_passages(notes: str, topic: str) -> list[str]:
    passages = split_notes(notes)
    query_terms = set(tokenize(topic))
    if not query_terms:
        return []

    document_frequency = Counter(
        term
        for passage in passages
        for term in set(tokenize(passage))
    )
    ranked: list[tuple[float, int, str]] = []

    for index, passage in enumerate(passages):
        terms = tokenize(passage)
        counts = Counter(terms)
        score = sum(
            counts[term] * math.log(1 + len(passages) / document_frequency[term])
            for term in query_terms
            if counts[term]
        )
        if score:
            ranked.append((score, index, passage))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [passage for _, _, passage in ranked[:5]]


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            response = await client.get(f"{OLLAMA_URL}/api/tags")
            response.raise_for_status()
            installed_models = response.json().get("models", [])
    except (httpx.HTTPError, ValueError):
        return {"available": False, "model": OLLAMA_MODEL}

    model_available = any(
        model.get("name") == OLLAMA_MODEL
        or model.get("name", "").startswith(f"{OLLAMA_MODEL}:")
        for model in installed_models
    )
    return {"available": model_available, "model": OLLAMA_MODEL}


@app.post("/api/study", response_model=StudyGuide)
async def create_study_guide(request: StudyRequest) -> StudyGuide:
    sources = retrieve_passages(request.notes, request.topic)
    if not sources:
        raise HTTPException(
            status_code=422,
            detail="I couldn't find that topic in these notes. Try a phrase or keyword that appears in them.",
        )

    schema = StudyContent.model_json_schema()
    system_prompt = (
        "You are StudyForge, a patient study partner. Use only the supplied note excerpts. "
        "Do not add outside facts. If the excerpts do not fully explain the requested topic, "
        "say what is missing in the explanation instead of guessing. Explain in warm, plain "
        "language for a student. Give one concrete analogy or example, one short question "
        "that checks understanding, and a concise sample answer. Keep each field focused. "
        "Return valid JSON matching the requested schema.\n\n"
    )
    user_prompt = (
        f"TOPIC: {request.topic}\n\n"
        "NOTE EXCERPTS:\n"
        + "\n".join(f"[Note {index + 1}] {source}" for index, source in enumerate(sources))
    )

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "stream": False,
                    "format": schema,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "options": {"temperature": 0.2},
                },
            )
            response.raise_for_status()
            content = response.json()["message"]["content"]
            guide = StudyContent.model_validate_json(content)
    except httpx.ConnectError as error:
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Start Ollama and make sure the configured model is installed.",
        ) from error
    except httpx.TimeoutException as error:
        raise HTTPException(
            status_code=504,
            detail="The local model took too long to respond. Try again or use a smaller model.",
        ) from error
    except httpx.HTTPStatusError as error:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned an error ({error.response.status_code}). Check that {OLLAMA_MODEL} is installed.",
        ) from error
    except (httpx.HTTPError, KeyError, ValueError) as error:
        raise HTTPException(
            status_code=502,
            detail="The local model returned an invalid response. Please try again.",
        ) from error

    return StudyGuide(**guide.model_dump(), sources=sources)
