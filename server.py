"""
Backend API cho client React (client/) — cau hinh co ban do Role 1 (RAG Architect)
dung san, wire vao Task 9 (retrieve) + Task 10 (generate_with_citation).

Khi Task 9/10 hoan thanh, endpoint nay tu dong tra ket qua that — khong can sua
gi them ngoai phan TODO ghi ben duoi (multi-turn conversation memory).

Chay (tu project root, khong cd vao src/):
    uvicorn server:app --reload --port 8001

Client (Vite) da proxy san /api/* -> http://localhost:8001/* (xem client/vite.config.ts).
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.task10_generation import generate_with_citation

app = FastAPI(title="University Services RAG API")

# Vite dev server mac dinh chay port 5173. Proxy /api khien CORS thuong khong can,
# nhung mo san cho truong hop test truc tiep bang curl/Postman hoac doi port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConversationTurn(BaseModel):
    role: str
    content: str


class QueryRequest(BaseModel):
    question: str
    conversation_history: list[ConversationTurn] = []


class Citation(BaseModel):
    label: str
    document_id: str
    content: str


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest) -> QueryResponse:
    # TODO (Role 4 - Vu Huy Hoang): generate_with_citation() hien chi nhan 1 cau
    # hoi don, chua dung req.conversation_history. De co multi-turn that, can noi
    # history vao prompt trong task10_generation.py (bonus tieu chi "Conversation
    # memory" trong README) roi truyen tiep xuong day.
    try:
        result = generate_with_citation(req.question)
    except NotImplementedError:
        return QueryResponse(
            answer="Pipeline Task 9/10 chua duoc implement xong, quay lai sau khi nhom hoan thanh.",
            citations=[],
            confidence=0.0,
        )

    sources = result.get("sources", [])
    citations = [
        Citation(
            label=src.get("metadata", {}).get("source", f"Source {i}"),
            document_id=src.get("metadata", {}).get("source", str(i)),
            content=src.get("content", "")[:300],
        )
        for i, src in enumerate(sources, 1)
    ]
    confidence = float(sources[0]["score"]) if sources else 0.0

    return QueryResponse(answer=result["answer"], citations=citations, confidence=confidence)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
