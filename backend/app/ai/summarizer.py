def generate_summary(
    title: str,
    description: str,
    location_name: str | None
) -> str:

    location = location_name if location_name else "unknown location"

    short_description = description[:120]

    return (
        f"{title} reported at {location}. "
        f"Details: {short_description}..."
    )