import asyncio
import json
import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pathlib import Path
import subprocess
import hmac

BASE = Path(__file__).resolve().parent
JOBS_DIR = BASE / "jobs"
OUTPUTS_DIR = BASE / "outputs"
MODELS_DIR = BASE / "models"
JOB_EXTENSIONS = [".json", ".processing", ".done", ".error"]

for d in (JOBS_DIR, OUTPUTS_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connections for realtime events
ws_connections = set()

# API key protecting all API endpoints (GUI pages stay open).
API_KEY = os.environ.get("API_KEY", "ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf")


def verify_api_key(
    x_api_key: str | None = Header(default=None),
    api_key: str | None = Query(default=None),
):
    provided = x_api_key or api_key
    if not provided or not hmac.compare_digest(provided, API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing API key")
    return True


def job_file(job_id: str, ext: str = ".json") -> Path:
    return JOBS_DIR / f"{job_id}{ext}"


def find_job_file(job_id: str) -> Path | None:
    for ext in JOB_EXTENSIONS:
        p = job_file(job_id, ext)
        if p.exists():
            return p
    return None


def read_job(job_id: str):
    p = find_job_file(job_id)
    if not p.exists():
        return None
    with open(p, 'r') as f:
        return json.load(f)


def write_job(job_id: str, data: dict):
    p = job_file(job_id)
    with open(p, 'w') as f:
        json.dump(data, f, indent=2)


def start_comfyui():
    comfy_entry = os.environ.get('COMFY_ENTRY', 'ComfyUI/main.py')
    comfy_base_dir = os.environ.get('COMFY_BASE_DIRECTORY', str(BASE))
    comfy_cmd = [
        "python", comfy_entry,
        "--listen", "0.0.0.0",
        "--port", "8188",
        "--disable-auto-launch",
        "--base-directory", comfy_base_dir,
    ]
    try:
        proc = subprocess.Popen(comfy_cmd, cwd=str(BASE))
        return proc
    except Exception as e:
        print("Failed to start ComfyUI:", e)
        return None


def start_worker():
    worker_cmd = [
        "python", "worker.py",
    ]
    try:
        proc = subprocess.Popen(worker_cmd, cwd=str(BASE))
        return proc
    except Exception as e:
        print("Failed to start worker:", e)
        return None


@app.on_event("startup")
async def on_startup():
    # Start ComfyUI and the worker in background (best-effort)
    app.state.comfy_proc = start_comfyui()
    app.state.worker_proc = start_worker()


async def broadcast_update(message: dict):
    to_remove = []
    for ws in list(ws_connections):
        try:
            await ws.send_json(message)
        except Exception:
            to_remove.append(ws)
    for r in to_remove:
        ws_connections.discard(r)


@app.post('/prompt')
async def post_prompt(request: Request, _: bool = Depends(verify_api_key)):
    payload = await request.json()
    job_id = uuid.uuid4().hex
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "created_at": asyncio.get_event_loop().time(),
        "updated_at": asyncio.get_event_loop().time(),
        "payload": payload,
        "result": None,
    }
    write_job(job_id, job_data)
    await broadcast_update({"event": "queued", "job_id": job_id})
    return JSONResponse({"prompt_id": job_id})


@app.get('/history/{prompt_id}')
async def get_history(prompt_id: str, _: bool = Depends(verify_api_key)):
    rec = read_job(prompt_id)
    if not rec:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse(rec)


@app.get('/queue')
async def get_queue(_: bool = Depends(verify_api_key)):
    items = {}
    for ext in JOB_EXTENSIONS:
        for p in JOBS_DIR.glob(f'*{ext}'):
            job_id = p.stem
            if job_id in items:
                continue
            try:
                with open(p, 'r') as f:
                    data = json.load(f)
            except Exception:
                continue
            items[job_id] = {"job_id": data.get('job_id'), "status": data.get('status', ext.strip('.'))}
    return JSONResponse({"queue": items})


@app.get('/view')
async def view_file(filename: str):
    target = OUTPUTS_DIR / filename
    if not target.exists():
        return JSONResponse({"error": "file not found"}, status_code=404)
    return FileResponse(str(target))


@app.get('/')
async def home():
    return FileResponse(str(BASE / 'gui.html'))

@app.get('/gui.html')
async def gui_file():
    return FileResponse(str(BASE / 'gui.html'))

@app.websocket('/ws')
async def websocket_endpoint(ws: WebSocket):
    key = ws.query_params.get("api_key") or ws.headers.get("x-api-key")
    if not key or not hmac.compare_digest(key, API_KEY):
        await ws.close(code=1008)
        return
    await ws.accept()
    ws_connections.add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        ws_connections.discard(ws)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
