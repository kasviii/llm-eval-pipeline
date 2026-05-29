import asyncio
import time
import json
import os
import uuid
import statistics
from datetime import datetime

import httpx

from app.config import get_settings
from app.models import EvalQuestion, EvalResult, EvalReport
from app.evaluators.relevancy import compute_relevancy
from app.evaluators.faithfulness import compute_faithfulness
from app.evaluators.hallucination import detect_hallucination

settings = get_settings()


async def call_llm(question: str, provider: str) -> tuple[str, float, int]:
    """Returns (answer, latency_seconds, tokens_used)"""
    start = time.time()

    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.groq_model,
            "messages": [{"role": "user", "content": question}],
            "max_tokens": 256,
            "temperature": 0.0,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        answer = data["choices"][0]["message"]["content"]
        tokens = data.get("usage", {}).get("total_tokens", 0)

    elif provider == "gemini":
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        resp = model.generate_content(question)
        answer = resp.text
        tokens = resp.usage_metadata.total_token_count if resp.usage_metadata else 0

    else:
        raise ValueError(f"Unknown provider: {provider}")

    latency = time.time() - start
    return answer, round(latency, 3), tokens


async def evaluate_question(q: EvalQuestion, provider: str) -> EvalResult:
    answer, latency, tokens = await call_llm(q.question, provider)

    relevancy = compute_relevancy(q.question, answer)
    faithfulness = compute_faithfulness(q.expected_answer, answer)
    hallucination = detect_hallucination(q.expected_answer, answer, faithfulness)

    return EvalResult(
        question_id=q.id,
        question=q.question,
        expected_answer=q.expected_answer,
        actual_answer=answer,
        relevancy_score=relevancy,
        faithfulness_score=faithfulness,
        hallucination_flag=hallucination,
        latency_seconds=latency,
        tokens_used=tokens,
        provider=provider,
    )


async def run_evaluation(provider: str | None = None) -> EvalReport:
    provider = provider or settings.llm_provider

    with open(settings.dataset_path, "r") as f:
        raw = json.load(f)
    questions = [EvalQuestion(**q) for q in raw]

    print(f"Running evaluation on {len(questions)} questions with {provider}...")

    results = []
    for i, q in enumerate(questions):
        print(f"  [{i+1}/{len(questions)}] {q.id}: {q.question[:50]}...")
        try:
            result = await evaluate_question(q, provider)
            results.append(result)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  ERROR on {q.id}: {e}")

    hallucination_rate = sum(1 for r in results if r.hallucination_flag) / len(results)
    avg_relevancy = statistics.mean(r.relevancy_score for r in results)
    avg_faithfulness = statistics.mean(r.faithfulness_score for r in results)
    latencies = sorted(r.latency_seconds for r in results)
    latency_p50 = statistics.median(latencies)
    latency_p95 = latencies[int(len(latencies) * 0.95)]
    avg_tokens = statistics.mean(r.tokens_used for r in results)

    failure_reasons = []
    if hallucination_rate > settings.eval_threshold_hallucination:
        failure_reasons.append(
            f"Hallucination rate {hallucination_rate:.1%} exceeds threshold {settings.eval_threshold_hallucination:.1%}"
        )
    if latency_p95 > settings.eval_threshold_latency_p95:
        failure_reasons.append(
            f"P95 latency {latency_p95:.2f}s exceeds threshold {settings.eval_threshold_latency_p95:.2f}s"
        )

    passed = len(failure_reasons) == 0

    model = settings.groq_model if provider == "groq" else settings.gemini_model

    report = EvalReport(
        run_id=str(uuid.uuid4())[:8],
        provider=provider,
        model=model,
        total_questions=len(results),
        hallucination_rate=round(hallucination_rate, 4),
        avg_relevancy=round(avg_relevancy, 4),
        avg_faithfulness=round(avg_faithfulness, 4),
        latency_p50=round(latency_p50, 3),
        latency_p95=round(latency_p95, 3),
        avg_tokens=round(avg_tokens, 1),
        passed=passed,
        failure_reasons=failure_reasons,
        results=results,
    )

    os.makedirs(settings.reports_dir, exist_ok=True)
    report_path = f"{settings.reports_dir}/report_{report.run_id}.json"
    with open(report_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2)

    print(f"\nReport saved to {report_path}")
    return report