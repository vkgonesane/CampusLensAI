def classify_signal(description: str) -> tuple[str, str]:
    """
    Returns:
    (category, department)
    """

    text = description.lower()

    if any(word in text for word in ["wifi", "internet", "network", "projector"]):
        return ("IT", "IT Department")

    if any(word in text for word in ["water", "leak", "washroom", "toilet"]):
        return ("Infrastructure", "Infrastructure Department")

    if any(word in text for word in ["dirty", "garbage", "cleanliness", "dustbin"]):
        return ("Sanitation", "Sanitation Department")

    if any(word in text for word in ["light", "fan", "electricity", "ac"]):
        return ("Electrical", "Electrical Department")

    if any(word in text for word in ["unsafe", "security", "fight", "harassment"]):
        return ("Security", "Security Department")

    return ("General", "Admin Department")