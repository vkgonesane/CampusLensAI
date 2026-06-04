from difflib import SequenceMatcher


def calculate_text_similarity(text_one: str, text_two: str) -> float:
    similarity = SequenceMatcher(
        None,
        text_one.lower(),
        text_two.lower()
    ).ratio()

    return round(similarity, 2)


def detect_duplicate_score(
    current_description: str,
    previous_descriptions: list[str]
) -> float:
    highest_score = 0.0

    for old_description in previous_descriptions:
        similarity = calculate_text_similarity(
            current_description,
            old_description
        )

        if similarity > highest_score:
            highest_score = similarity

    return round(highest_score, 2)


def find_best_duplicate_match(
    current_description: str,
    previous_signals: list
):
    best_score = 0.0
    best_signal = None

    for signal in previous_signals:
        similarity = calculate_text_similarity(
            current_description,
            signal.description
        )

        if similarity > best_score:
            best_score = similarity
            best_signal = signal

    return {
        "score": round(best_score, 2),
        "matched_signal": best_signal
    }