"""
Task 10 — Generation có Citation.

Pipeline:
    1. Retrieve các chunk liên quan
    2. Sắp xếp lại để giảm "lost in the middle"
    3. Format context kèm nguồn
    4. Gọi LLM
    5. Trả lời có citation
    6. Từ chối xác minh nếu evidence không đủ

Hỗ trợ:
    - OpenRouter
    - OpenAI

Cài đặt:
    pip install openai python-dotenv
"""

import os
from pathlib import Path

from dotenv import load_dotenv

from .task9_retrieval_pipeline import retrieve


PROJECT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_DIR / ".env")


# =============================================================================
# CONFIGURATION
# =============================================================================

# 5 chunk thường đủ evidence mà không làm context quá dài.
TOP_K = 5

# Giữ mức đa dạng vừa phải nhưng vẫn ưu tiên câu trả lời có căn cứ.
TOP_P = 0.9

# Temperature thấp vì RAG cần chính xác, ít sáng tạo.
TEMPERATURE = 0.2

# Model dùng khi gọi qua OpenRouter.
OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openai/gpt-4o-mini",
)

# Model dùng khi gọi trực tiếp OpenAI.
OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-4o-mini",
)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

CANNOT_VERIFY_MESSAGE = (
    "Tôi không thể xác minh thông tin này từ nguồn hiện có."
)


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """
Bạn là trợ lý trả lời câu hỏi về dịch vụ và chính sách đại học,
bao gồm học phí, học bổng, ký túc xá, thư viện và đăng ký học phần.

Quy tắc bắt buộc:

1. Chỉ sử dụng thông tin xuất hiện trong CONTEXT.
2. Không sử dụng kiến thức bên ngoài và không bịa thông tin.
3. Mỗi khẳng định quan trọng phải có citation ngay sau nội dung.
4. Citation phải dùng đúng tên nguồn, ví dụ:
   [tuition-fees-rmit.md]
5. Chỉ sử dụng những nguồn được liệt kê trong CONTEXT.
6. Nếu CONTEXT không có đủ evidence, chỉ trả lời:
   "Tôi không thể xác minh thông tin này từ nguồn hiện có."
7. Trả lời bằng tiếng Việt, rõ ràng và ngắn gọn.
8. Không nói rằng bạn đã đọc tài liệu nếu thông tin không có trong CONTEXT.
""".strip()


# =============================================================================
# DOCUMENT REORDERING
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunk để giảm hiệu ứng "lost in the middle".

    Input theo score:
        [1, 2, 3, 4, 5]

    Output:
        [1, 3, 5, 4, 2]

    Chunk tốt nhất nằm đầu prompt và chunk tốt thứ hai nằm cuối prompt.
    """
    if not chunks:
        return []

    if len(chunks) <= 2:
        return list(chunks)

    front = chunks[::2]
    back = chunks[1::2]

    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format các chunk thành context có nhãn nguồn để LLM citation.
    """
    if not chunks:
        return ""

    context_parts = []

    for index, chunk in enumerate(chunks, start=1):
        metadata = chunk.get("metadata") or {}

        source = str(
            metadata.get("source")
            or metadata.get("source_path")
            or f"source-{index}"
        ).strip()

        doc_type = str(
            metadata.get("type")
            or metadata.get("doc_type")
            or "unknown"
        ).strip()

        chunk_index = metadata.get(
            "chunk_index",
            "unknown",
        )

        score = chunk.get("score")
        content = str(
            chunk.get("content") or ""
        ).strip()

        if not content:
            continue

        if isinstance(score, (int, float)):
            score_text = f"{score:.4f}"
        else:
            score_text = "N/A"

        context_parts.append(
            f"[DOCUMENT {index}]\n"
            f"Source: {source}\n"
            f"Type: {doc_type}\n"
            f"Chunk: {chunk_index}\n"
            f"Retrieval score: {score_text}\n"
            f"Citation label: [{source}]\n\n"
            f"{content}"
        )

    return "\n\n---\n\n".join(context_parts)


# =============================================================================
# CLIENT CONFIGURATION
# =============================================================================

def create_llm_client():
    """
    Tạo OpenAI-compatible client.

    Ưu tiên:
        1. OPENROUTER_API_KEY
        2. OPENAI_API_KEY

    Returns:
        (client, model, provider)
    """
    from openai import OpenAI

    openrouter_key = os.getenv("OPENROUTER_API_KEY")

    if openrouter_key:
        client = OpenAI(
            api_key=openrouter_key,
            base_url=OPENROUTER_BASE_URL,
        )

        return (
            client,
            OPENROUTER_MODEL,
            "openrouter",
        )

    openai_key = os.getenv("OPENAI_API_KEY")

    if openai_key:
        client = OpenAI(
            api_key=openai_key,
        )

        return (
            client,
            OPENAI_MODEL,
            "openai",
        )

    raise RuntimeError(
        "Chưa cấu hình OPENROUTER_API_KEY "
        "hoặc OPENAI_API_KEY trong file .env"
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_retrieval_source(chunks: list[dict]) -> str:
    """
    Xác định nguồn retrieval của danh sách kết quả.
    """
    if not chunks:
        return "none"

    sources = {
        str(chunk.get("source", "hybrid"))
        for chunk in chunks
    }

    if len(sources) == 1:
        return next(iter(sources))

    return "mixed"


def build_source_list(chunks: list[dict]) -> list[dict]:
    """
    Tạo danh sách nguồn gọn, không chứa embedding.
    """
    sources = []

    for chunk in chunks:
        metadata = dict(
            chunk.get("metadata") or {}
        )

        sources.append(
            {
                "content": str(
                    chunk.get("content") or ""
                ),
                "score": float(
                    chunk.get("score") or 0.0
                ),
                "metadata": metadata,
                "source": chunk.get(
                    "source",
                    "hybrid",
                ),
            }
        )

    return sources


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(
    query: str,
    top_k: int = TOP_K,
) -> dict:
    """
    End-to-end RAG generation có citation.

    Returns:
        {
            "answer": str,
            "sources": list[dict],
            "retrieval_source": str
        }
    """
    query = str(query or "").strip()

    if not query:
        return {
            "answer": CANNOT_VERIFY_MESSAGE,
            "sources": [],
            "retrieval_source": "none",
        }

    if top_k <= 0:
        raise ValueError("top_k phải lớn hơn 0")

    # Bước 1: Retrieve evidence.
    try:
        chunks = retrieve(
            query,
            top_k=top_k,
        )
    except Exception as exc:
        return {
            "answer": (
                f"{CANNOT_VERIFY_MESSAGE} "
                f"Lỗi retrieval: {exc}"
            ),
            "sources": [],
            "retrieval_source": "error",
        }

    if not chunks:
        return {
            "answer": CANNOT_VERIFY_MESSAGE,
            "sources": [],
            "retrieval_source": "none",
        }

    # Chỉ giữ đúng số lượng người dùng yêu cầu.
    chunks = chunks[:top_k]

    # Bước 2: Reorder để giảm lost in the middle.
    reordered_chunks = reorder_for_llm(chunks)

    # Bước 3: Format context có citation label.
    context = format_context(reordered_chunks)

    if not context:
        return {
            "answer": CANNOT_VERIFY_MESSAGE,
            "sources": build_source_list(chunks),
            "retrieval_source": get_retrieval_source(
                chunks
            ),
        }

    user_message = (
        "Hãy trả lời câu hỏi dựa hoàn toàn vào CONTEXT.\n\n"
        "CONTEXT:\n"
        f"{context}\n\n"
        "===== END CONTEXT =====\n\n"
        f"CÂU HỎI:\n{query}\n\n"
        "Yêu cầu: Mỗi thông tin quan trọng phải có citation "
        "dùng đúng Citation label trong context."
    )

    # Bước 4: Khởi tạo client.
    try:
        client, model, provider = create_llm_client()
    except RuntimeError as exc:
        return {
            "answer": (
                f"{CANNOT_VERIFY_MESSAGE} "
                f"{exc}"
            ),
            "sources": build_source_list(chunks),
            "retrieval_source": get_retrieval_source(
                chunks
            ),
        }

    # Bước 5: Gọi LLM.
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
        )

        answer = (
            response.choices[0].message.content
            or ""
        ).strip()

        if not answer:
            answer = CANNOT_VERIFY_MESSAGE

    except Exception as exc:
        answer = (
            f"{CANNOT_VERIFY_MESSAGE} "
            f"Lỗi gọi {provider}: {exc}"
        )

    # Bước 6: Trả về answer và evidence.
    return {
        "answer": answer,
        "sources": build_source_list(chunks),
        "retrieval_source": get_retrieval_source(
            chunks
        ),
    }


# =============================================================================
# DEMO
# =============================================================================

def main():
    test_queries = [
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Làm sao để đặt phòng học nhóm ở thư viện?",
        "Sinh viên quốc tế có những học bổng nào?",
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"Q: {query}")
        print("=" * 70)

        result = generate_with_citation(query)

        print(f"\nA: {result['answer']}")
        print(
            f"\nSources: {len(result['sources'])} chunks"
            f" | via {result['retrieval_source']}"
        )


if __name__ == "__main__":
    main()