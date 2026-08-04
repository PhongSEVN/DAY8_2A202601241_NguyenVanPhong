"""
Backend API cho client React (client/) — cau hinh co ban do Role 1 (RAG Architect)
dung san, wire vao Task 9 (retrieve) + Task 10 (generate_with_citation).

Da wire xong: retrieval that (Task 9), generation co citation (Task 10), va
multi-turn conversation memory (3 cap hoi-dap gan nhat truyen qua
conversation_history).

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
from src.task5_semantic_search import semantic_search

app = FastAPI(title="University Services RAG API")

# Vite dev server mac dinh chay port 5173. Proxy /api khien CORS thuong khong can,
# nhung mo san cho truong hop test truc tiep bang curl/Postman hoac doi port.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],
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
    history = [{"role": t.role, "content": t.content} for t in req.conversation_history]
    try:
        result = generate_with_citation(req.question, conversation_history=history)
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
    # sources[0]["score"] sau rerank/RRF KHONG phan anh do lien quan that (RRF luon
    # ~1/(k+1)=0.016 bat ke noi dung). Dung lai diem cosine goc tu semantic_search
    # de hien thi confidence co y nghia cho nguoi dung — dung dung logic voi bay da
    # ghi trong task9_retrieval_pipeline.py.
    if result.get("retrieval_source") == "pageindex":
        confidence = 0.0  # da fallback vi hybrid search khong du tin cay
    else:
        top_dense = semantic_search(req.question, top_k=1)
        confidence = float(top_dense[0]["score"]) if top_dense else 0.0

    return QueryResponse(answer=result["answer"], citations=citations, confidence=confidence)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
