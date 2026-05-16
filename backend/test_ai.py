from app.ai.ai_service import analyze_signal

result = analyze_signal(
    title="Washroom tap leaking",
    description="The washroom tap is leaking again and water is spreading everywhere.",
    location_name="Block A Washroom",
    reopen_count=1,
    previous_descriptions=[
        "Tap leaking near Block A",
        "Water leakage issue in washroom"
    ],
    location_signal_count=6
)

print(result)