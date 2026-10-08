from fastapi import Request
from sqlmodel import Session


def get_graph(request: Request):
    return request.app.state.graph


def get_content(request: Request):
    return request.app.state.content


def get_llm(request: Request):
    return request.app.state.llm


def get_db(request: Request):
    with Session(request.app.state.engine) as session:
        yield session
