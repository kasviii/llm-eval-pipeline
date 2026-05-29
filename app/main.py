from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio

from app.config import get_settings
from app.models import EvalReport
from app.evaluators.runner import run_evaluation

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Automated LLM evaluation pipeline — runs quality checks on every model or prompt change.",
)

# store latest report in memory
latest_report: EvalReport | None = None
is_running: bool = False


@app.get("/")
@app.head("/")
async def root():
    return {
        "name": settings.app_name,
        "version": settings.version,
        "status": "running",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "provider": settings.llm_provider,
        "dataset": settings.dataset_path,
    }


@app.post("/eval/run")
async def trigger_eval(background_tasks: BackgroundTasks, provider: str = None):
    global is_running
    if is_running:
        return JSONResponse(
            status_code=409,
            content={"error": "Evaluation already running. Check /eval/status."}
        )

    async def run():
        global latest_report, is_running
        is_running = True
        try:
            latest_report = await run_evaluation(provider)
        finally:
            is_running = False

    background_tasks.add_task(run)
    return {"message": "Evaluation started.", "check_status": "/eval/status"}


@app.get("/eval/status")
async def eval_status():
    global is_running, latest_report
    if is_running:
        return {"status": "running"}
    if latest_report is None:
        return {"status": "no_runs_yet"}
    return {
        "status": "completed",
        "run_id": latest_report.run_id,
        "passed": latest_report.passed,
        "hallucination_rate": latest_report.hallucination_rate,
        "latency_p95": latest_report.latency_p95,
        "failure_reasons": latest_report.failure_reasons,
    }


@app.get("/eval/report")
async def get_report():
    global latest_report
    if latest_report is None:
        return JSONResponse(
            status_code=404,
            content={"error": "No evaluation report available. Run /eval/run first."}
        )
    return latest_report


@app.get("/eval/report/summary")
async def get_summary():
    global latest_report
    if latest_report is None:
        return JSONResponse(
            status_code=404,
            content={"error": "No report yet."}
        )
    r = latest_report
    return {
        "run_id": r.run_id,
        "provider": r.provider,
        "model": r.model,
        "total_questions": r.total_questions,
        "passed": r.passed,
        "failure_reasons": r.failure_reasons,
        "metrics": {
            "hallucination_rate": f"{r.hallucination_rate:.1%}",
            "avg_relevancy": f"{r.avg_relevancy:.1%}",
            "avg_faithfulness": f"{r.avg_faithfulness:.1%}",
            "latency_p50": f"{r.latency_p50}s",
            "latency_p95": f"{r.latency_p95}s",
            "avg_tokens": r.avg_tokens,
        }
    }