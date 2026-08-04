"""
RAG Evaluation Pipeline.

Sử dụng DeepEval / RAGAS / TruLens để đánh giá chất lượng RAG pipeline.
Chọn 1 framework và implement đầy đủ.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md

Lưu ý rate limit nếu dùng model OpenRouter ":free": RAGAS/DeepEval gọi LLM RẤT NHIỀU LẦN
(không phải 1 lần/câu hỏi mà nhiều lần/metric/câu hỏi). Model free của OpenRouter giới hạn
50 request/ngày CHO CẢ TÀI KHOẢN (không phải theo model hay theo API key — đổi model free
khác hay tạo key mới KHÔNG reset quota). Nếu chạy full 15+ câu hỏi mà bị rate limit giữa
chừng, thử giảm xuống subset 5 câu để chạy kịp trong buổi, hoặc nạp $10 credit để mở khóa
1000 request/ngày.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# RAGAS Judge LLM/Embeddings (OpenRouter — không cần OPENAI_API_KEY riêng)
# =============================================================================

def build_ragas_judge():
    """
    RAGAS mặc định dùng OpenAI (ChatOpenAI + OpenAIEmbeddings) làm "judge" để
    chấm điểm — nhưng .env của nhóm chỉ có OPENROUTER_API_KEY, không có
    OPENAI_API_KEY. Nên phải tự trỏ ChatOpenAI sang OpenRouter base_url, và
    dùng lại embedding model local (BAAI/bge-m3, đã cài cho Task 4/5) thay vì
    OpenAIEmbeddings để không phụ thuộc thêm API trả phí.

    Returns:
        (llm, embeddings) — đã wrap theo interface ragas cần cho evaluate().
    """
    from langchain_openai import ChatOpenAI
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    judge_model = os.getenv("RAGAS_JUDGE_MODEL") or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

    chat = ChatOpenAI(
        model=judge_model,
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.0,
    )
    hf_embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

    return LangchainLLMWrapper(chat), LangchainEmbeddingsWrapper(hf_embeddings)


# =============================================================================
# Option 1: DeepEval
# =============================================================================

def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng DeepEval.

    pip install deepeval
    """
    # TODO: Implement
    #
    # from deepeval import evaluate
    # from deepeval.metrics import (
    #     FaithfulnessMetric,
    #     AnswerRelevancyMetric,
    #     ContextualRecallMetric,
    #     ContextualPrecisionMetric,
    # )
    # from deepeval.test_case import LLMTestCase
    #
    # test_cases = []
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     test_case = LLMTestCase(
    #         input=item["question"],
    #         actual_output=result["answer"],
    #         expected_output=item["expected_answer"],
    #         retrieval_context=[c["content"] for c in result["sources"]],
    #     )
    #     test_cases.append(test_case)
    #
    # metrics = [
    #     FaithfulnessMetric(threshold=0.7),
    #     AnswerRelevancyMetric(threshold=0.7),
    #     ContextualRecallMetric(threshold=0.7),
    #     ContextualPrecisionMetric(threshold=0.7),
    # ]
    #
    # results = evaluate(test_cases, metrics)
    # return results
    raise NotImplementedError("Implement evaluate_with_deepeval")


# =============================================================================
# Option 2: RAGAS
# =============================================================================

def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict]):
    """
    Evaluate RAG pipeline sử dụng RAGAS.

    pip install ragas

    Args:
        rag_pipeline: module/object có hàm generate_with_citation(question) -> dict
            {'answer': str, 'sources': list[{'content': str, ...}]}
        golden_dataset: list of {'question', 'expected_answer', 'expected_context'}

    Returns:
        pandas.DataFrame — 1 dòng/câu hỏi, cột = 4 metrics + question/answer/contexts.
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    )
    from datasets import Dataset

    eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    for item in golden_dataset:
        result = rag_pipeline.generate_with_citation(item["question"])
        eval_data["question"].append(item["question"])
        eval_data["answer"].append(result["answer"])
        eval_data["contexts"].append([c["content"] for c in result["sources"]])
        eval_data["ground_truth"].append(item["expected_answer"])

    dataset = Dataset.from_dict(eval_data)
    judge_llm, judge_embeddings = build_ragas_judge()
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )
    return result.to_pandas()


# =============================================================================
# Option 3: TruLens
# =============================================================================

def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng TruLens.

    pip install trulens
    """
    # TODO: Implement
    #
    # from trulens.apps.custom import TruCustomApp
    # from trulens.core import Feedback
    # from trulens.providers.openai import OpenAI as TruOpenAI
    #
    # provider = TruOpenAI()
    #
    # f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
    # f_relevance = Feedback(provider.relevance).on_input_output()
    # f_context_relevance = Feedback(provider.context_relevance).on_input()
    #
    # tru_rag = TruCustomApp(
    #     rag_pipeline,
    #     app_name="UniversityServices_RAG",
    #     feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
    # )
    #
    # with tru_rag as recording:
    #     for item in golden_dataset:
    #         rag_pipeline.generate_with_citation(item["question"])
    #
    # # Dashboard: from trulens.dashboard import run_dashboard; run_dashboard()
    raise NotImplementedError("Implement evaluate_with_trulens")


# =============================================================================
# A/B Comparison
# =============================================================================

def _generate_for_config(query: str, top_k: int, use_reranking: bool) -> dict:
    """
    Chạy generation cho 1 config cụ thể, tái dùng prompt/LLM call logic của
    Task 10 (SYSTEM_PROMPT, reorder_for_llm, format_context, create_llm_client...)
    nhưng cho phép bật/tắt reranking ở tầng retrieval — generate_with_citation()
    gốc không expose tham số này nên A/B so sánh reranking phải gọi retrieve()
    trực tiếp rồi lắp lại phần format/LLM giống Task 10.

    Lưu ý: retrieve() có thể raise nếu PAGEINDEX_API_KEY chưa cấu hình và câu hỏi
    kích hoạt fallback (score cosine < threshold) — bắt lỗi ở đây giống cách
    generate_with_citation() làm, để A/B eval không crash giữa chừng vì 1-2 câu
    ngoài domain trong golden_dataset.json.
    """
    from src.task9_retrieval_pipeline import retrieve
    from src.task10_generation import (
        SYSTEM_PROMPT, TEMPERATURE, TOP_P,
        reorder_for_llm, format_context, create_llm_client,
        CANNOT_VERIFY_MESSAGE,
    )

    try:
        chunks = retrieve(query, top_k=top_k, use_reranking=use_reranking)
    except Exception as exc:
        return {"answer": f"{CANNOT_VERIFY_MESSAGE} Lỗi retrieval: {exc}", "sources": []}

    reordered = reorder_for_llm(chunks) if chunks else []
    context = format_context(reordered) if reordered else ""

    if not context:
        return {"answer": CANNOT_VERIFY_MESSAGE, "sources": chunks}

    client, model, _provider = create_llm_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\n---\n\nQuestion: {query}"},
        ],
        temperature=TEMPERATURE,
        top_p=TOP_P,
    )
    answer = (response.choices[0].message.content or "").strip() or CANNOT_VERIFY_MESSAGE
    return {"answer": answer, "sources": chunks}


def compare_configs(golden_dataset: list[dict]) -> dict:
    """
    So sánh A/B giữa 2 configs:
        - Config A: hybrid search (semantic + BM25 + RRF) + reranking (mặc định Task 9)
        - Config B: dense-only, không reranking (use_reranking=False)

    Returns:
        {'hybrid_rerank': pandas.DataFrame, 'dense_only': pandas.DataFrame}
        Mỗi DataFrame có cùng format với evaluate_with_ragas().
    """
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness, answer_relevancy, context_recall, context_precision,
    )
    from datasets import Dataset

    configs = {
        "hybrid_rerank": True,
        "dense_only": False,
    }

    judge_llm, judge_embeddings = build_ragas_judge()

    results = {}
    for config_name, use_reranking in configs.items():
        eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
        for item in golden_dataset:
            result = _generate_for_config(item["question"], top_k=5, use_reranking=use_reranking)
            eval_data["question"].append(item["question"])
            eval_data["answer"].append(result["answer"])
            eval_data["contexts"].append([c["content"] for c in result["sources"]] or [""])
            eval_data["ground_truth"].append(item["expected_answer"])

        dataset = Dataset.from_dict(eval_data)
        scored = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
            llm=judge_llm,
            embeddings=judge_embeddings,
        )
        results[config_name] = scored.to_pandas()

    return results


# =============================================================================
# Export Results
# =============================================================================

METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]


def _avg(df, metric: str) -> float:
    return float(df[metric].mean()) if metric in df else float("nan")


def export_results(results, comparison: dict) -> None:
    """
    Export evaluation results ra results.md.

    Args:
        results: DataFrame từ evaluate_with_ragas() (pipeline mặc định — dùng để
            tính Worst Performers).
        comparison: dict {'hybrid_rerank': DataFrame, 'dense_only': DataFrame}
            từ compare_configs().
    """
    df_a = comparison.get("hybrid_rerank", results)
    df_b = comparison.get("dense_only")

    content = "# RAG Evaluation Results\n\n"
    content += "## Framework sử dụng\n\nRAGAS (`pip install ragas`)\n\n---\n\n"

    content += "## Overall Scores\n\n"
    content += "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |\n"
    content += "|--------|---------------------------|----------------------|---|\n"
    avg_a_list, avg_b_list = [], []
    for metric in METRICS:
        a = _avg(df_a, metric)
        b = _avg(df_b, metric) if df_b is not None else float("nan")
        avg_a_list.append(a)
        avg_b_list.append(b)
        delta = a - b if df_b is not None else float("nan")
        content += f"| {metric} | {a:.3f} | {b:.3f} | {delta:+.3f} |\n"
    overall_a = sum(avg_a_list) / len(avg_a_list)
    overall_b = sum(avg_b_list) / len(avg_b_list) if df_b is not None else float("nan")
    content += f"| **Average** | **{overall_a:.3f}** | **{overall_b:.3f}** | **{overall_a - overall_b:+.3f}** |\n"

    content += "\n---\n\n## A/B Comparison Analysis\n\n"
    content += "**Config A (hybrid_rerank):** semantic search + BM25 merge bằng RRF (k=60) + rerank.\n\n"
    content += "**Config B (dense_only):** chỉ semantic search (dense retrieval), không BM25, không rerank.\n\n"
    winner = "Config A" if overall_a >= overall_b else "Config B"
    content += f"**Kết luận:** {winner} có average score cao hơn ({max(overall_a, overall_b):.3f} vs {min(overall_a, overall_b):.3f}). "
    content += "Điền phân tích chi tiết sau khi chạy với data thật (vì sao rerank/hybrid giúp hay không giúp).\n\n"

    content += "---\n\n## Worst Performers (Bottom 3)\n\n"
    content += "| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |\n"
    content += "|---|----------|-------------|-----------|--------|---------------|------------|\n"
    if "faithfulness" in df_a and "answer_relevancy" in df_a:
        df_sorted = df_a.copy()
        df_sorted["_avg"] = df_sorted[METRICS].mean(axis=1)
        worst = df_sorted.sort_values("_avg").head(3)
        for i, (_, row) in enumerate(worst.iterrows(), 1):
            q = str(row.get("question", ""))[:60]
            content += (
                f"| {i} | {q} | {row.get('faithfulness', 0):.3f} | "
                f"{row.get('answer_relevancy', 0):.3f} | {row.get('context_recall', 0):.3f} | | |\n"
            )
    else:
        content += "| 1 | | | | | | |\n| 2 | | | | | | |\n| 3 | | | | | | |\n"

    content += "\n---\n\n## Recommendations\n\n"
    content += "### Cải tiến 1\n**Action:** Điền sau khi phân tích worst performers.\n**Expected impact:**\n\n"
    content += "### Cải tiến 2\n**Action:**\n**Expected impact:**\n\n"
    content += "### Cải tiến 3\n**Action:**\n**Expected impact:**\n"

    RESULTS_PATH.write_text(content, encoding="utf-8")
    print(f"✓ Exported: {RESULTS_PATH}")


if __name__ == "__main__":
    from src import task10_generation as pipeline

    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    # EVAL_SAMPLE_SIZE: cho phép chạy subset khi bị rate-limit (xem cảnh báo đầu
    # file) mà không phải sửa golden_dataset.json — mặc định chạy full dataset.
    sample_size = os.getenv("EVAL_SAMPLE_SIZE")
    if sample_size:
        golden_dataset = golden_dataset[: int(sample_size)]
        print(f"EVAL_SAMPLE_SIZE set -> chỉ chạy {len(golden_dataset)} câu (rate-limit safety)")

    results_df = evaluate_with_ragas(pipeline, golden_dataset)
    comparison_dfs = compare_configs(golden_dataset)
    export_results(results_df, comparison_dfs)
