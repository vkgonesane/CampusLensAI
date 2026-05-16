from fastapi import FastAPI

app = FastAPI(
    title="CampusLensAI Backend",
    version="1.0.0"
)


@app.get("/")
def health_check():
    return {
        "message": "CampusLensAI backend is running"
    }