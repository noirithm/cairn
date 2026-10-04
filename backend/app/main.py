from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db, make_engine
from .graph import ConceptGraph
from .routes import sessions

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def create_app(db_url: str | None = None) -> FastAPI:
    """App factory: tests pass an in-memory DB; normal runs use the default."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = make_engine(db_url)
        init_db(app.state.engine)
        # Fail fast: a broken graph.json should crash at startup, not mid-demo.
        app.state.graph = ConceptGraph.load(DATA_DIR / "graph.json")
        yield

    app = FastAPI(title="Cairn", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(sessions.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
