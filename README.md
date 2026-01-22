# Prop Trader MVP

MVP aplikacji do analizy historii transakcji prop tradera, liczenia metryk performance/risk, wykrywania zachowań (overtrading, revenge trading) oraz generowania tygodniowego raportu w języku polskim przy użyciu LLM (bez sygnałów i bez predykcji rynku).

## Architektura (MVP)

**Ekrany (2–3 kluczowe widoki):**
1. **Upload i ustawienia** – użytkownik wgrywa CSV, wybiera okres (7/30/90 dni) i limity prop firm (max daily DD, max total DD, account size).
2. **Dashboard** – metryki core, equity curve, podsumowanie sesji, tabela naruszeń i przycisk „Generuj raport AI”.
3. **Raport** – wygenerowany raport tygodniowy w formacie Markdown + możliwość pobrania.

**Komponenty:**
- **Frontend (Streamlit /app):** prosty UI do uploadu CSV i prezentacji wyników.
- **Backend (FastAPI /backend):** walidacja CSV, obliczenia metryk, wykrywanie zachowań, generacja raportu LLM.
- **SQLite + SQLAlchemy:** zapis wygenerowanych raportów.
- **LLM provider-agnostic:** endpoint z `LLM_ENDPOINT` i kluczem `LLM_API_KEY`/`OPENAI_API_KEY`.

**Przepływ danych:**
CSV → walidacja/mapping → metryki + zachowania → (opcjonalnie) naruszenia limitów → raport LLM → zapis w SQLite.

## Struktura repo

```
/ backend
  /app
    main.py
    db.py
    models.py
    schemas.py
    /services
  /tests
/app
  app.py
/data
  sample_trades.csv
```

## Wymagania

- Python 3.11
- Pip

## Uruchomienie lokalne

### Backend (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend (Streamlit)
```bash
cd app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### Konfiguracja LLM (opcjonalnie)
Ustaw zmienne środowiskowe:
```bash
export LLM_API_KEY="..."   # lub OPENAI_API_KEY
export LLM_ENDPOINT="https://api.openai.com/v1/chat/completions"
export LLM_MODEL="gpt-4o-mini"
```

## Format CSV
Minimalny zestaw kolumn (obsługiwane aliasy w kodzie):
- `open_time`, `close_time`
- `symbol`
- `side` (`buy`/`sell`)
- `volume`
- `entry_price`, `exit_price`
- `sl`, `tp` (opcjonalne)
- `profit` (lub `pips`, jeśli brak `profit`)
- `commission`, `swap` (opcjonalne)

Przykładowy plik: `data/sample_trades.csv`.

## Testy
```bash
cd backend
pytest
```

## Zasady
- Brak sygnałów tradingowych i predykcji rynku.
- Analiza wyłącznie danych historycznych.
- Wyniki oparte o liczby i metryki ryzyka.
