import json as jsonlib
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend import main


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


class FakeAsyncClient:
    payload: dict[str, object] = {}
    last_request: dict[str, object] = {}
    installed_models: list[dict[str, str]] = []

    def __init__(self, **_: object) -> None:
        pass

    async def __aenter__(self) -> "FakeAsyncClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        return None

    async def get(self, _: str) -> FakeResponse:
        return FakeResponse({"models": self.installed_models})

    async def post(self, _: str, *, json: dict[str, object]) -> FakeResponse:
        type(self).last_request = json
        return FakeResponse({"message": {"content": jsonlib.dumps(self.payload)}})


class StudyForgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(main.app)
        FakeAsyncClient.installed_models = [{"name": main.OLLAMA_MODEL}]
        FakeAsyncClient.payload = {
            "explanation": "Plants use sunlight to make stored energy.",
            "example": "Think of a leaf as a tiny solar-powered kitchen.",
            "question": "What does the Calvin cycle use to make glucose?",
            "answer": "It uses carbon dioxide, ATP, and NADPH.",
            "sources": ["This model-provided source must not be trusted."],
        }

    def test_retrieves_relevant_notes(self) -> None:
        notes = (
            "Chlorophyll absorbs sunlight. "
            "The Calvin cycle uses carbon dioxide, ATP, and NADPH to make glucose."
        )

        passages = main.retrieve_passages(notes, "Calvin cycle glucose")

        self.assertEqual(len(passages), 1)
        self.assertIn("Calvin cycle", passages[0])

    def test_unmatched_topic_returns_actionable_error(self) -> None:
        response = self.client.post(
            "/api/study",
            json={"notes": "Chlorophyll absorbs sunlight.", "topic": "volcanoes"},
        )

        self.assertEqual(response.status_code, 422)
        self.assertIn("couldn't find that topic", response.json()["detail"])

    def test_guide_uses_local_model_and_actual_source_passages(self) -> None:
        with patch.object(main.httpx, "AsyncClient", FakeAsyncClient):
            response = self.client.post(
                "/api/study",
                json={
                    "notes": "The Calvin cycle uses carbon dioxide, ATP, and NADPH to make glucose.",
                    "topic": "Calvin cycle glucose",
                },
            )

        self.assertEqual(response.status_code, 200)
        guide = response.json()
        self.assertEqual(guide["explanation"], FakeAsyncClient.payload["explanation"])
        self.assertEqual(len(guide["sources"]), 1)
        self.assertIn("Calvin cycle", guide["sources"][0])
        self.assertNotIn("model-provided source", guide["sources"][0])
        self.assertEqual(
            FakeAsyncClient.last_request["messages"][0]["role"],
            "system",
        )
        self.assertEqual(FakeAsyncClient.last_request["model"], "gemma3:4b")

    def test_health_reports_gemma_model_installed(self) -> None:
        with patch.object(main.httpx, "AsyncClient", FakeAsyncClient):
            response = self.client.get("/api/health")

        self.assertEqual(
            response.json(),
            {"available": True, "model": "gemma3:4b"},
        )

    def test_health_reports_gemma_model_missing(self) -> None:
        FakeAsyncClient.installed_models = [{"name": "qwen2.5:3b"}]

        with patch.object(main.httpx, "AsyncClient", FakeAsyncClient):
            response = self.client.get("/api/health")

        self.assertEqual(
            response.json(),
            {"available": False, "model": "gemma3:4b"},
        )

if __name__ == "__main__":
    unittest.main()
