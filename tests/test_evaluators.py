from app.evaluators.relevancy import compute_relevancy
from app.evaluators.faithfulness import compute_faithfulness
from app.evaluators.hallucination import detect_hallucination


def test_relevancy_perfect():
    score = compute_relevancy(
        "What is gradient descent?",
        "Gradient descent is an optimization algorithm used in machine learning."
    )
    assert score == 1.0


def test_relevancy_partial():
    score = compute_relevancy(
        "What is gradient descent in machine learning?",
        "The weather is nice today."
    )
    assert score < 0.3


def test_relevancy_empty_answer():
    score = compute_relevancy("What is Python?", "")
    assert score == 0.0


def test_faithfulness_perfect():
    expected = "Paris is the capital of France."
    actual = "Paris is the capital of France."
    score = compute_faithfulness(expected, actual)
    assert score == 1.0


def test_faithfulness_partial():
    expected = "The mitochondria is the powerhouse of the cell."
    actual = "Mitochondria produce energy for cells through ATP synthesis."
    score = compute_faithfulness(expected, actual)
    assert 0.2 < score < 1.0


def test_faithfulness_completely_wrong():
    expected = "Binary search has time complexity O(log n)."
    actual = "The sky is blue and clouds are white."
    score = compute_faithfulness(expected, actual)
    assert score < 0.2


def test_hallucination_detected_low_faithfulness():
    expected = "Binary search has a time complexity of O(log n)."
    actual = "The weather in Paris is sunny and warm today."
    faithfulness = compute_faithfulness(expected, actual)
    result = detect_hallucination(expected, actual, faithfulness)
    assert result is True


def test_hallucination_not_detected_good_answer():
    expected = "The mitochondria is the powerhouse of the cell."
    actual = "Mitochondria are known as the powerhouse of the cell."
    faithfulness = compute_faithfulness(expected, actual)
    result = detect_hallucination(expected, actual, faithfulness)
    assert result is False


def test_hallucination_fabrication_signal():
    expected = "Paris is the capital of France."
    actual = "I believe Paris is the capital of France."
    result = detect_hallucination(expected, actual, 0.9)
    assert result is True


def test_full_pipeline_scores():
    question = "What is Docker?"
    expected = "Docker is a platform for running applications in containers."
    actual = "Docker is a containerization platform that packages applications and dependencies."

    relevancy = compute_relevancy(question, actual)
    faithfulness = compute_faithfulness(expected, actual)
    hallucination = detect_hallucination(expected, actual, faithfulness)

    assert relevancy > 0.5
    assert faithfulness > 0.3
    assert hallucination is False