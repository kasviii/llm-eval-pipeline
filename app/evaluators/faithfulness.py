import re

def compute_faithfulness(expected: str, actual: str) -> float:
    """
    Measures how closely the actual answer aligns with the expected answer.
    Uses token overlap (similar to ROUGE-1 recall).
    """
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "shall", "can",
        "of", "in", "on", "at", "to", "for", "with", "by", "from",
        "and", "or", "but", "not", "this", "that", "it", "its"
    }

    def tokenize(text: str) -> set:
        tokens = set(re.findall(r'\b\w+\b', text.lower()))
        return tokens - stopwords

    expected_tokens = tokenize(expected)
    actual_tokens = tokenize(actual)

    if not expected_tokens:
        return 1.0

    overlap = expected_tokens & actual_tokens
    recall = len(overlap) / len(expected_tokens)

    return round(recall, 4)