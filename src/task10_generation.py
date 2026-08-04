"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"

Gợi ý LLM: OpenRouter có nhiều model gắn hậu tố ":free" không tính phí — xem
https://openrouter.ai/models?max_price=0 — phù hợp nếu chưa có credit trả phí.
Base URL: "https://openrouter.ai/api/v1", dùng chung interface với OpenAI SDK.
"""

import os
from dotenv import load_dotenv
from openai import RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

load_dotenv()

from .task9_retrieval_pipeline import retrieve

# Retry rieng cho loi 429 (TPM/RPM rate limit) — backoff exponential 4-60s, toi
# da 5 lan thu, KHONG retry cac loi khac (401/500...) de fail nhanh, de debug.
_rate_limit_retry = retry(
    retry=retry_if_exception_type(RateLimitError),
    wait=wait_random_exponential(min=4, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
)


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3

# max_tokens: Gioi han do dai output — tranh OpenRouter mac dinh xin toi 16384
# token/request (gay loi 402 "insufficient credits" du cau tra loi thuc te chi
# can vai tram token). 1000 du cho 1 doan van citation, khong lang phi quota.
MAX_TOKENS = 1000

# Chot boi Role 1: doi tu OpenRouter (het credit, loi 402) sang goi thang OpenAI
# API bang OPENAI_API_KEY da co san. Model id khong con tien to provider ("openai/").
LLM_MODEL = "gpt-4o-mini"


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý trả lời câu hỏi về dịch vụ và chính sách đại học
(học phí, học bổng, ký túc xá, thư viện, đăng ký học phần).

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin từ context được cung cấp — KHÔNG bịa đặt
2. Mỗi khẳng định phải có trích dẫn ngay sau, ví dụ: [Tuition Fees, 2026]
3. Nếu context không đủ thông tin để trả lời câu hỏi → trả lời đúng nguyên văn:
   "Tôi không thể xác minh thông tin này từ nguồn hiện có"
4. Nếu câu hỏi KHÔNG liên quan đến dịch vụ/chính sách đại học (ví dụ: kiến thức
   phổ thông, chuyện phiếm, chủ đề hoàn toàn khác) — kể cả khi context có chứa vài
   đoạn văn bản nào đó — vẫn từ chối lịch sự, KHÔNG dùng context đó để trả lời:
   "Câu hỏi này nằm ngoài phạm vi hỗ trợ của tôi (dịch vụ và chính sách đại học).
   Bạn có câu hỏi nào về học phí, học bổng, ký túc xá, thư viện hay đăng ký học
   phần không?"
5. Trả lời bằng tiếng Việt, có cấu trúc rõ ràng theo đoạn văn
6. Không suy luận hay mở rộng ngoài những gì được nêu trong context
7. Nếu có lịch sử hội thoại trước đó, dùng nó để hiểu ngữ cảnh câu hỏi hiện tại
   (câu hỏi nối tiếp, đại từ thay thế...) nhưng vẫn chỉ trả lời dựa trên context
   tài liệu được cung cấp cho câu hỏi hiện tại"""

GREETING_RESPONSE = (
    "Xin chào! Tôi là trợ lý hỏi đáp về dịch vụ và chính sách đại học "
    "(học phí, học bổng, ký túc xá, thư viện, đăng ký học phần). "
    "Tôi có thể giúp gì cho bạn?"
)

_GREETING_PATTERNS = (
    "hi", "hello", "hey", "yo",
    "chao", "chào", "alo",
)


def _is_greeting(query: str) -> bool:
    """
    Nhận diện tin nhắn CHỈ là lời chào (khong kem cau hoi thuc su), de tra loi
    nhanh khong can chay qua toan bo retrieval pipeline.
    """
    normalized = query.strip().lower().strip("!?.,")
    if not normalized:
        return False
    words = normalized.replace(",", " ").split()
    if len(words) > 5:
        return False
    return any(word in _GREETING_PATTERNS for word in words)


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return chunks

    front = chunks[::2]   # index 0, 2, 4 -> dat o dau
    back = chunks[1::2]   # index 1, 3    -> dat o cuoi (reversed)
    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string.
    """
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get("metadata", {}).get("source", f"Source {i}")
        doc_type = chunk.get("metadata", {}).get("type", "unknown")
        context_parts.append(
            f"[Document {i} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk['content']}\n"
        )
    return "\n---\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def _format_history(conversation_history: list[dict] | None, max_turns: int = 3) -> str:
    """
    Format N cap hoi-dap gan nhat thanh text de LLM hieu ngu canh cau hoi noi
    tiep (vd "con ky tuc xa thi sao?" sau khi da hoi ve hoc phi).

    Args:
        conversation_history: List of {'role': 'user'|'assistant', 'content': str},
            thu tu cu -> moi (nhu client gui len).
        max_turns: So cap hoi-dap gan nhat giu lai (mac dinh 3 = 6 message).

    Returns:
        Text block "Previous conversation:\n..." hoac "" neu khong co history.
    """
    if not conversation_history:
        return ""

    recent = conversation_history[-(max_turns * 2):]
    lines = []
    for turn in recent:
        role = "User" if turn.get("role") == "user" else "Assistant"
        lines.append(f"{role}: {turn.get('content', '')}")
    return "Previous conversation:\n" + "\n".join(lines) + "\n\n---\n\n"


def generate_with_citation(
    query: str, top_k: int = TOP_K, conversation_history: list[dict] | None = None
) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        0. Neu query chi la loi chao -> tra loi nhanh, khong chay retrieval
        1. Retrieve relevant chunks
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (history + system + context + query)
        5. Call LLM
        6. Return answer + sources

    Args:
        query: Câu hỏi của user
        top_k: So chunks lay ve
        conversation_history: 3 cap hoi-dap gan nhat (tuy chon), de tra loi cau
            hoi noi tiep dung ngu canh

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    # Step 0: Fast-path cho loi chao — khong can chay qua retrieval pipeline
    if _is_greeting(query):
        return {"answer": GREETING_RESPONSE, "sources": [], "retrieval_source": "none"}

    # Step 1: Retrieve
    chunks = retrieve(query, top_k=top_k)

    # Step 2: Reorder
    reordered = reorder_for_llm(chunks) if chunks else []

    # Step 3: Format context
    context = format_context(reordered) if reordered else "(Khong tim thay tai lieu lien quan)"

    # Step 4: Build prompt (co the kem 3 cap hoi-dap gan nhat)
    history_block = _format_history(conversation_history)
    user_message = f"""{history_block}Context:\n{context}\n\n---\n\nQuestion: {query}"""

    # Step 5: Call LLM (OpenAI truc tiep)
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    @_rate_limit_retry
    def _call():
        return client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=TEMPERATURE,
            top_p=TOP_P,
            max_tokens=MAX_TOKENS,
        )

    response = _call()

    answer = response.choices[0].message.content

    # Step 6: Return
    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": chunks[0].get("source", "hybrid") if chunks else "none"
    }


if __name__ == "__main__":
    test_queries = [
        "Học phí tại RMIT Vietnam là bao nhiêu?",
        "Làm sao để đặt phòng học nhóm ở thư viện?",
        "Sinh viên quốc tế có những học bổng nào?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
