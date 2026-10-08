from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .content import Content
from .database import init_db, make_engine
from .graph import ConceptGraph
from .llm.base import LLMClient
from .llm.factory import from_env
from .routes import quiz, sessions, transfer

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def create_app(db_url: str | None = None,
               llm_factory: Callable[[], LLMClient | None] = from_env) -> FastAPI:
    """App factory: tests pass an in-memory DB and no LLM; normal runs read CAIRN_LLM."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = make_engine(db_url)
        init_db(app.state.engine)
        # Fail fast: broken content should crash at startup, not mid-demo.
        app.state.graph = ConceptGraph.load(DATA_DIR / "graph.json")
        app.state.content = Content.load(DATA_DIR, set(app.state.graph.g.nodes))
        app.state.llm = llm_factory()
        yield

    app = FastAPI(title="Cairn", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(sessions.router)
    app.include_router(quiz.router)
    app.include_router(transfer.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
