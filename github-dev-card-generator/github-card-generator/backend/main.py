import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import github_card_agent

app = FastAPI(title="GitHub Dev Card Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(__file__)
static_path = os.path.join(BASE_DIR, "static")
frontend_path = os.path.join(BASE_DIR, "..", "frontend")

os.makedirs(os.path.join(static_path, "cards"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

if os.path.exists(frontend_path):
    app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")


class GenerateRequest(BaseModel):
    username: str
    theme: str = "dark"


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/")
async def serve_frontend():
    index = os.path.join(frontend_path, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"status": "Backend API is running. Visit /docs for API reference."}


@app.post("/generate")
async def generate_card(request: GenerateRequest):
    try:
        result = await github_card_agent.run_agent(request.username, request.theme)
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        # Return the card snippet (body content only) so the frontend
        # can inject it directly without full-page HTML conflicts
        card_file = os.path.join(static_path, "cards", f"{request.username}.html")
        if os.path.exists(card_file):
            with open(card_file, "r", encoding="utf-8") as f:
                full = f.read()
            import re
            body_match = re.search(r'<body[^>]*>(.*?)</body>', full, re.DOTALL)
            if body_match:
                result["card_html"] = body_match.group(1).strip()
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/card/{username}")
async def get_card(username: str):
    file_path = os.path.join(static_path, "cards", f"{username}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Card not found. Generate it first.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
