# Cairn

An AI tutor that models what a student understands as a concept graph, diagnoses the misconception behind a wrong answer, and tests transfer with problems whose answers are verified by SymPy.

Built for ForgeHacks 2026 (AI + Education track). MVP unit: Newton's laws.

## What it does

1. **Concept graph.** 14 Newton's-law concepts with weighted prerequisite edges. Nodes recolor live as mastery changes.
2. **Learner model.** Bayesian Knowledge Tracing per concept. A wrong answer also lowers belief in prerequisites, weighted by edge strength.
3. **Diagnostic dialogue.** The next question is the one with the highest expected information gain over a taxonomy of 7 physics misconceptions.
4. **Misconception diagnosis.** Answer patterns are mapped to a named misconception with a targeted explanation.
5. **Transfer problems.** New-context numeric problems, each answer verified with SymPy before a student sees it, with a three-step hint ladder.
6. **Teacher view.** A class-level misconception heatmap, seeded with simulated students.

## Not an LLM wrapper

The LLM only phrases text. Everything that decides what the student sees or how they are scored is deterministic code.

| Part | Done by |
|---|---|
| Mastery tracking, prerequisite propagation | Hand-written BKT and graph code |
| Choosing the next question | Expected information gain over misconception beliefs |
| Grading answers | Server-side, from the option picked or a numeric tolerance |
| Transfer-problem answers | SymPy solve, then three independent checks before display |
| Problem wording (optional) | LLM, never given the answer; any changed number is rejected |
| Concept graph and misconception taxonomy | Built offline, committed as JSON, validated at startup |

LLM calls return JSON validated by Pydantic, with retries on schema failure. The LLM is off by default, so the demo cannot break on the network.

## How the transfer verifier works

Each template defines its governing equations in SymPy. A problem is only shown if all three checks pass:

1. Substituting the SymPy solution back satisfies every equation exactly.
2. The answer agrees with a separate plain-Python derivation.
3. The result is physically sensible (for example, a positive normal force, or static friction below its limit).

## Stack

- **Backend:** Python 3.12, FastAPI, SQLModel (SQLite), NetworkX, SymPy. BKT is hand-written.
- **LLM (optional):** provider-agnostic interface with Anthropic and Ollama adapters.
- **Frontend:** Next.js, TypeScript, Tailwind, React Flow (`@xyflow/react`), dagre.
- **Tests:** pytest.

## Quickstart

Requires Python 3.12 with [uv](https://docs.astral.sh/uv/), and Node 20+.

Backend:

    cd backend
    uv sync
    uv run pytest
    uv run uvicorn app.main:app --reload

Frontend (second terminal):

    cd frontend
    npm install
    npm run dev

Open http://localhost:3000. Use `localhost`, not `127.0.0.1`, because the backend CORS allows only `http://localhost:3000`.

On first start the backend seeds 30 simulated students for the teacher view. To rebuild them: `uv run python -m app.seed --reset`.

### Optional: LLM re-wording of transfer problems

    export CAIRN_LLM=anthropic ANTHROPIC_API_KEY=...    # or: CAIRN_LLM=ollama CAIRN_LLM_MODEL=llama3.1

### Configuration

| Variable | Default | Meaning |
|---|---|---|
| `CAIRN_LLM` | `none` | `none`, `anthropic` or `ollama` |
| `CAIRN_LLM_MODEL` | provider default | Model name |
| `ANTHROPIC_API_KEY` | | Required for `anthropic` |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server |
| `CAIRN_DB_URL` | `sqlite:///./cairn.db` | Database |
| `CAIRN_SEED_DEMO` | `1` | Seed simulated students on startup |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for the frontend |

## Demo path (about 3 minutes)

1. Open the student view and click **New student**.
2. Answer the first question (the hockey puck) with "A constant forward force that keeps it moving". Nodes flash as mastery drops on that concept and its prerequisites.
3. Answer the next question (the skydiver) with "Downward, equal to her weight". A named misconception, "Force is needed to maintain motion", is diagnosed with an explanation.
4. Open **Transfer problem**, start one, take a hint, and submit. Entering `m·g` on a normal-force problem triggers the matching misconception feedback.
5. Open **Teacher view** to see the class heatmap, including your own live row.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/sessions` | Start a student |
| GET | `/sessions/{id}/graph` | Concept graph with mastery |
| GET | `/sessions/{id}/next-question` | Next question by information gain |
| POST | `/sessions/{id}/answers` | Grade an answer, update mastery and beliefs |
| GET | `/sessions/{id}/diagnosis` | Current misconception beliefs |
| POST | `/sessions/{id}/transfer` | New verified transfer problem |
| POST | `/sessions/{id}/transfer/{pid}/hint` | Next hint |
| POST | `/sessions/{id}/transfer/{pid}/answer` | Check a numeric answer |
| GET | `/teacher/heatmap` | Class-level heatmap |
| GET | `/health` | Liveness |

## Repository layout

    data/                  graph.json, misconceptions.json, questions.json (built offline)
    backend/app/
      engine/              bkt, propagation, diagnosis, selector
      transfer/            templates, SymPy generator and verifier, LLM phrasing guard
      llm/                 provider-agnostic client and adapters
      routes/              sessions, quiz, transfer, teacher
      simulation.py        simulated students for the teacher view
    backend/tests/         pytest suite
    frontend/src/          Next.js app: graph, quiz, transfer, teacher view

## Limitations

- **Hand-set parameters.** BKT parameters, propagation damping, misconception likelihoods and the prior are set by hand, not fitted to student data.
- **Circular simulation.** Simulated students answer from the same likelihood tables the engine uses to diagnose them. Recovering their hidden misconceptions shows the pipeline works, not that the tables match real students.
- **Confusable misconceptions.** "Force is proportional to velocity" and "force is needed to maintain motion" look alike on several questions and are sometimes confused.
- **Narrow scope.** One unit. The conceptual laws (first and third) have quiz questions but no numeric transfer templates.
- **One-way propagation.** A correct answer does not raise prerequisite beliefs.
- **LLM wording.** The guard enforces that numbers are unchanged, but not that the same quantity is asked for; that is instructed, not enforced.
- **No authentication.** The teacher view is open, which is fine for a demo only.

## Attribution

The concept graph and misconceptions are derived from OpenStax University Physics Volume 1, licensed CC BY 4.0, and from the physics-education-research literature on common student misconceptions.
