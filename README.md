# Cairn

An AI tutor that models what a student understands as a concept graph, diagnoses the misconception behind a wrong answer, and tests transfer with problems whose answers are verified by SymPy.

Built for ForgeHacks 2026 (AI + Education track). MVP unit: Newton's laws.

## How it works

- The LLM only extracts, generates, and phrases text.
- Learner state (BKT), question selection, and answer checking are deterministic code.
- Every numeric answer in a transfer problem is verified with SymPy before a student sees it.

## Stack

Python 3.12, FastAPI, SQLModel (SQLite), NetworkX, SymPy. Frontend: Next.js, TypeScript, Tailwind, React Flow.

## Run the backend

    cd backend
    uv sync
    uv run pytest
    uv run uvicorn app.main:app --reload

## Attribution

Concept graph derived from OpenStax University Physics Volume 1, licensed CC BY 4.0.
