from fastapi import FastAPI

app = FastAPI(
    title="CampusLensAI Backend",
    description="AI-powered campus intelligence platform",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "message": "CampusLensAI backend is running"
    }