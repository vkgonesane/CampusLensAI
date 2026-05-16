def calculate_hotspot_score(
    location_signal_count: int
) -> float:

    if location_signal_count >= 10:
        return 1.0

    if location_signal_count >= 7:
        return 0.8

    if location_signal_count >= 5:
        return 0.6

    if location_signal_count >= 3:
        return 0.4

    return 0.1