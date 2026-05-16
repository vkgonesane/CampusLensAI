from difflib import SequenceMatcher


def detect_duplicate_score(
    current_description: str,
    previous_descriptions: list[str]
) -> float:

    highest_score = 0.0

    for old_description in previous_descriptions:
        similarity = SequenceMatcher(
            None,
            current_description.lower(),
            old_description.lower()
        ).ratio()

        if similarity > highest_score:
            highest_score = similarity

    return round(highest_score, 2)