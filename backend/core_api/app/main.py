from fastapi import FastAPI

app = FastAPI(title="AI_VoIP_Agent", version="1.0")

@app.get('/health')
def health() -> dict:
    return {"status": "ok", "service": "core_api"}