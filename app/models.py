from pydantic import BaseModel
from typing import Optional

class EvalQuestion(BaseModel):
    id: str
    question: str
    expected_answer: str
    category: str
    difficulty: str = "medium"

class EvalResult(BaseModel):
    question_id: str
    question: str
    expected_answer: str
    actual_answer: str
    relevancy_score: float
    faithfulness_score: float
    hallucination_flag: bool
    latency_seconds: float
    tokens_used: int
    provider: str

class EvalReport(BaseModel):
    run_id: str
    provider: str
    model: str
    total_questions: int
    hallucination_rate: float
    avg_relevancy: float
    avg_faithfulness: float
    latency_p50: float
    latency_p95: float
    avg_tokens: float
    passed: bool
    failure_reasons: list[str]
    results: list[EvalResult]