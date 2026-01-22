from __future__ import annotations

from typing import Any, Dict


def build_report_payload(
    metrics: Dict[str, Any],
    behaviors: Dict[str, Any],
    violations: Dict[str, Any],
    limits: Dict[str, Any] | None,
) -> Dict[str, Any]:
    return {
        "metrics": metrics,
        "behaviors": behaviors,
        "violations": violations,
        "limits": limits or {},
        "format": {
            "sections": [
                "Status bezpieczeństwa konta (LOW/MODERATE/HIGH) + uzasadnienie liczbami",
                "Co działa (2-3 punkty)",
                "Co szkodzi (2-3 punkty) + wskazanie danych",
                "Dyscyplina i naruszenia reguł (score 0-100)",
                "5 zaleceń actionable (co zrobić + po co + jak zmierzyć)",
                "Jednozdaniowe ostrzeżenie: jeśli nic nie zmienisz...",
            ]
        },
        "constraints": [
            "Nie generuj sygnałów tradingowych.",
            "Nie przewiduj rynku.",
            "Wnioski muszą być liczbowe i oparte o dane historyczne.",
        ],
    }
