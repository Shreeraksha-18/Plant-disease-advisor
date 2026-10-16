from fastapi import FastAPI

app = FastAPI(title="Plant Disease Advisor API")

@app.get("/health")
def health():
    return {"status": "ok"}