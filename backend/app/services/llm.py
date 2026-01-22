from __future__ import annotations

import json
import os
from typing import Any, Dict

import httpx


class LLMClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
        self.endpoint = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    def generate_report(self, payload: Dict[str, Any]) -> str:
        if not self.api_key:
            return self._fallback_report(payload)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Jesteś analitykiem ryzyka dla prop traderów. "
                        "Nie dajesz sygnałów tradingowych ani predykcji rynku. "
                        "Odpowiadasz po polsku w formacie raportu tygodniowego."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            "temperature": 0.2,
        }
        with httpx.Client(timeout=30) as client:
            response = client.post(self.endpoint, json=body, headers=headers)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _fallback_report(self, payload: Dict[str, Any]) -> str:
        return (
            "# Raport tygodniowy (fallback)\n\n"
            "Brak skonfigurowanego klucza LLM_API_KEY/OPENAI_API_KEY. "
            "Poniżej dane wejściowe do raportu:\n\n"
            f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```\n"
        )
