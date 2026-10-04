import os

from sqlmodel import SQLModel, create_engine
from sqlmodel.pool import StaticPool

from . import models  # noqa: F401  (registers tables)


def make_engine(url: str | None = None):
    url = url or os.getenv("CAIRN_DB_URL", "sqlite:///./cairn.db")
    if url == "sqlite://":  # in-memory for tests: share one connection
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url, connect_args={"check_same_thread": False})


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)
