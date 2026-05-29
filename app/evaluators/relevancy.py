import re

def compute_relevancy(question: str, answer: str) -> float:
    """
    Measures how well the answer addresses the question.
    Extracts key terms from the question and checks coverage in the answer.
    """
    stopwords = {
        "what", "is", "the", "a", "an", "of", "in", "on", "at", "to",
        "for", "are", "was", "were", "how", "why", "when", "where", "who",
        "does", "do", "did", "has", "have", "had", "can", "could", "would",
        "should", "between", "and", "or", "but", "with", "from", "by"
    }

    question_words = set(re.findall(r'\b\w+\b', question.lower()))
    key_terms = question_words - stopwords

    if not key_terms:
        return 1.0

    answer_lower = answer.lower()
    matched = sum(1 for term in key_terms if term in answer_lower)
    score = matched / len(key_terms)

    return round(min(score, 1.0), 4)