import re

CONTRADICTION_PATTERNS = [
    (r'\bnot\s+(\w+)', r'\b\1\b'),
    (r'\bnever\b', r'\balways\b'),
    (r'\bimpossible\b', r'\bpossible\b'),
    (r'\bfalse\b', r'\btrue\b'),
]

FABRICATION_SIGNALS = [
    "as of my knowledge",
    "i believe",
    "i think",
    "i'm not sure but",
    "it might be",
    "possibly",
    "i cannot confirm",
]


def detect_hallucination(expected: str, actual: str, faithfulness_score: float) -> bool:
    """
    Flags a response as hallucinated if:
    1. Faithfulness score is very low (answer diverges significantly from expected)
    2. Answer contains fabrication signal phrases on factual questions
    3. Answer contains direct contradictions to expected
    """
    # low faithfulness is a strong hallucination signal
    if faithfulness_score < 0.15:
        return True

    actual_lower = actual.lower()
    expected_lower = expected.lower()

    # check for fabrication signals
    for signal in FABRICATION_SIGNALS:
        if signal in actual_lower:
            return True

    # check for direct contradictions
    expected_key_terms = set(re.findall(r'\b\w{4,}\b', expected_lower))
    for term in expected_key_terms:
        negated = f"not {term}"
        if negated in actual_lower and term in expected_lower:
            return True

    return False