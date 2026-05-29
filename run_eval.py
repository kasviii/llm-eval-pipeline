import asyncio
import sys
from app.evaluators.runner import run_evaluation
from tabulate import tabulate


async def main():
    provider = sys.argv[1] if len(sys.argv) > 1 else None

    print("=" * 60)
    print("LLM EVAL PIPELINE")
    print("=" * 60)

    report = await run_evaluation(provider)

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)

    summary = [
        ["Run ID", report.run_id],
        ["Provider", report.provider],
        ["Model", report.model],
        ["Total Questions", report.total_questions],
        ["Hallucination Rate", f"{report.hallucination_rate:.1%}"],
        ["Avg Relevancy", f"{report.avg_relevancy:.1%}"],
        ["Avg Faithfulness", f"{report.avg_faithfulness:.1%}"],
        ["Latency P50", f"{report.latency_p50}s"],
        ["Latency P95", f"{report.latency_p95}s"],
        ["Avg Tokens", report.avg_tokens],
        ["PASSED", "YES" if report.passed else "NO"],
    ]

    print(tabulate(summary, tablefmt="rounded_outline"))

    if report.failure_reasons:
        print("\nFAILURE REASONS:")
        for reason in report.failure_reasons:
            print(f"  - {reason}")

    print("\nPER-QUESTION RESULTS:")
    rows = []
    for r in report.results:
        rows.append([
            r.question_id,
            r.question[:40] + "...",
            f"{r.relevancy_score:.0%}",
            f"{r.faithfulness_score:.0%}",
            "YES" if r.hallucination_flag else "no",
            f"{r.latency_seconds}s",
            r.tokens_used,
        ])

    print(tabulate(
        rows,
        headers=["ID", "Question", "Relevancy", "Faithfulness", "Hallucination", "Latency", "Tokens"],
        tablefmt="rounded_outline"
    ))

    if not report.passed:
        print("\nPIPELINE FAILED — thresholds exceeded")
        sys.exit(1)
    else:
        print("\nPIPELINE PASSED")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())