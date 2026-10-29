import json, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from optimization.model import solve
from optimization.validation import validate

app = FastAPI(title="Disaster Relief Distribution Optimizer")

@app.get("/api/demo")
def demo():
    return json.loads((ROOT / "data" / "demo.json").read_text(encoding="utf-8"))

@app.post("/api/optimize")
def optimize(scenario: dict):
    errs = validate(scenario)
    if errs:
        return JSONResponse({"status": "Invalid", "errors": errs}, status_code=422)
    try:
        return solve(scenario)
    except Exception as e:  # solver failure must not crash the app
        return JSONResponse({"status": "Error", "errors": [str(e)]}, status_code=500)

@app.get("/")
def index():
    return FileResponse(ROOT / "frontend" / "index.html")
