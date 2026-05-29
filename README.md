# LLM Eval CI/CD Pipeline

An automated evaluation pipeline that runs every time a prompt changes, a model is swapped, or a knowledge base is updated — just like unit tests run when code changes.

Measures hallucination rate, answer relevancy, faithfulness to expected answers, latency (p50/p95), and cost per query across a golden dataset of questions. Blocks the pipeline if quality thresholds are exceeded.

---

## Live Demo

- **API Docs:** coming soon (deploy instructions below)

---

## How It Works

Every evaluation run:
1. Loads a golden dataset of question-answer pairs with known expected outputs
2. Sends each question to the configured LLM provider (Groq or Gemini)
3. Scores each response on relevancy, faithfulness, and hallucination
4. Measures latency and token usage per question
5. Computes aggregate metrics and compares against thresholds
6. Fails the pipeline (exit code 1) if hallucination rate exceeds 5% or P95 latency exceeds 5 seconds
7. Saves a full JSON report to the reports directory

---

## Features

- **Golden dataset** — 15 curated question-answer pairs across geography, biology, computer science, and machine learning categories
- **Hallucination detection** — flags responses that diverge significantly from expected answers or contain fabrication signals
- **Answer relevancy scoring** — measures how well the response addresses the question using key term coverage
- **Faithfulness scoring** — measures token overlap between actual and expected answers (ROUGE-1 style recall)
- **Latency tracking** — records per-question latency and computes p50 and p95 across the run
- **Token cost tracking** — records tokens used per question for cost estimation
- **Threshold enforcement** — pipeline fails automatically if any metric exceeds configured thresholds
- **Multi-provider support** — runs against Groq (Llama 3.3 70B) or Google Gemini with a single flag
- **REST API** — trigger evaluations and fetch reports via HTTP endpoints
- **GitHub Actions CI** — runs the full eval suite on every push, uploads report as artifact
- **Docker ready** — single docker-compose up runs the full stack

---

## Quickstart

1. Clone and install

```bash
git clone https://github.com/kasviii/llm-eval-pipeline.git
cd llm-eval-pipeline
pip install -r requirements.txt
```

2. Set up environment

```bash
cp .env.example .env
```

Add your GROQ_API_KEY and GEMINI_API_KEY to the .env file.

3. Run the evaluation pipeline from CLI

```bash
python run_eval.py
```

4. Or run against a specific provider

```bash
python run_eval.py gemini
```

5. Or start the API server

```bash
python -m uvicorn app.main:app --reload
```

6. Or run with Docker

```bash
docker-compose up
```

---

## Example Output

```
============================================================
LLM EVAL PIPELINE
============================================================
Running evaluation on 15 questions with groq...

============================================================
EVALUATION SUMMARY
============================================================
╭────────────────────┬─────────────────────────╮
│ Run ID             │ 832038fa                │
│ Provider           │ groq                    │
│ Model              │ llama-3.3-70b-versatile │
│ Total Questions    │ 15                      │
│ Hallucination Rate │ 6.7%                    │
│ Avg Relevancy      │ 100.0%                  │
│ Avg Faithfulness   │ 76.1%                   │
│ Latency P50        │ 1.22s                   │
│ Latency P95        │ 2.221s                  │
│ Avg Tokens         │ 249.1                   │
│ PASSED             │ NO                      │
╰────────────────────┴─────────────────────────╯

FAILURE REASONS:
  - Hallucination rate 6.7% exceeds threshold 5.0%
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Health check |
| GET | /health | Provider and dataset status |
| POST | /eval/run | Trigger a new evaluation run |
| GET | /eval/status | Check if evaluation is running |
| GET | /eval/report | Full report from last run |
| GET | /eval/report/summary | Summary metrics from last run |

Trigger an eval via API:

```bash
curl -X POST http://localhost:8000/eval/run
```

Check status:

```bash
curl http://localhost:8000/eval/status
```

Get summary:

```bash
curl http://localhost:8000/eval/report/summary
```

---

## Metrics Explained

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Hallucination rate | Percentage of responses that diverge from expected or contain fabrication signals | < 5% |
| Avg relevancy | How well responses address the question (key term coverage) | informational |
| Avg faithfulness | Token overlap between actual and expected answer (ROUGE-1 recall) | informational |
| Latency P50 | Median response time across all questions | informational |
| Latency P95 | 95th percentile response time (worst case) | < 5s |
| Avg tokens | Average tokens used per question for cost estimation | informational |

---

## Configuration

Edit .env to change thresholds and providers:

```
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
LLM_PROVIDER=groq
EVAL_THRESHOLD_HALLUCINATION=0.05
EVAL_THRESHOLD_LATENCY_P95=5.0
DATASET_PATH=dataset/golden.json
REPORTS_DIR=reports
```

---

## Golden Dataset

The dataset lives in dataset/golden.json. Each entry has an id, question, expected answer, category, and difficulty. Add your own entries to expand coverage:

```json
{
  "id": "q016",
  "question": "What is a transformer model?",
  "expected_answer": "A transformer is a deep learning architecture that uses self-attention mechanisms.",
  "category": "machine learning",
  "difficulty": "hard"
}
```

---

## Running Tests

```bash
pytest tests/ -v
```

10 tests covering relevancy scoring, faithfulness scoring, hallucination detection, and full pipeline integration.

---

## CI/CD

On every push to main, GitHub Actions:
1. Installs dependencies
2. Runs the unit test suite
3. Runs the full eval pipeline against the golden dataset
4. Uploads the eval report as a downloadable artifact
5. Fails the build if quality thresholds are exceeded

To enable the eval step in CI, add your API keys as GitHub secrets:
- Go to your repo on GitHub
- Settings → Secrets and variables → Actions
- Add GROQ_API_KEY and GEMINI_API_KEY

---

## Tech Stack

- **FastAPI** — async API framework for triggering and serving eval results
- **Groq** — primary LLM provider (Llama 3.3 70B)
- **Google Gemini** — secondary LLM provider
- **Pydantic** — data validation and report schemas
- **Tabulate** — formatted CLI output
- **Docker + Docker Compose** — containerization
- **GitHub Actions** — CI/CD pipeline

---

## Project Structure

```
llm-eval-pipeline/
├── app/
│   ├── main.py                 # FastAPI app and eval endpoints
│   ├── config.py               # Settings and thresholds
│   ├── models.py               # Pydantic schemas for eval data
│   └── evaluators/
│       ├── relevancy.py        # Key term coverage scoring
│       ├── faithfulness.py     # Token overlap scoring
│       ├── hallucination.py    # Hallucination detection
│       └── runner.py           # Orchestrates full eval run
├── dataset/
│   └── golden.json             # 15 curated QA pairs
├── tests/
│   └── test_evaluators.py      # 10 unit tests
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI
├── run_eval.py                 # CLI entry point
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

---

## License

MIT