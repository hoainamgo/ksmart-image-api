# Context Snapshot

 - Date: 2026-07-03
- OS: Linux
- Workspace root: /teamspace/studios/this_studio

## Public endpoint (added)
- **API base URL (public):** `https://api.ksmart.com.es`
- **API key:** `ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf` (send as `X-API-Key` header or `api_key` query param)
- Tunnel: Cloudflare named tunnel `api-ksmart-tunnel`, fixed domain `api.ksmart.com.es` (DNS CNAME already routed). Start with `python start_tunnel.py`.
- GUI: `https://api.ksmart.com.es/` (open, no key needed for the page).

## Scripts tiện dụng (quick start)
- `start_server.sh` (Linux): khởi API server (port 8000) + Cloudflare tunnel `api-ksmart-tunnel` -> `https://api.ksmart.com.es` trong một lệnh. Chạy: `bash start_server.sh`. Log: `api_server.log`, `tunnel.log`.
- `open_gui.bat` (Windows cmd): mở GUI `https://api.ksmart.com.es/` trong trình duyệt và test nhanh `/queue`. Chạy: double-click hoặc gõ `open_gui.bat`.
- Khởi thủ công từng bước: xem `RESTART.md` (thứ tự ComfyUI → API server → worker → tunnel).

## Current status (updated)
- ComfyUI: **running** in this session on `http://127.0.0.1:8188` (Tesla T4 GPU, real FLUX.2 image generation). Start with: `setsid python ComfyUI/main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch --base-directory "$(pwd)" > comfy_launch.log 2>&1 &`. NOTE: needs `custom_nodes/` dir to exist (created) and a real GPU; without GPU it cannot start.
- App API server: running on `http://0.0.0.0:8000` with the prompt GUI served from `gui.html` at `http://localhost:8000/`.
- GPU: **available** in this session — Tesla T4 (16GB VRAM). ComfyUI runs on `http://127.0.0.1:8188` and generates **real FLUX.2 images** (not dummy). Worker copies generated PNGs into `outputs/`.
- Workflow: GUI `POST /prompt` with `{"client_id":"gui","prompt":{"prompt":"..."}}` → worker builds FLUX2 graph, calls ComfyUI, copies result `flux2_*.png` to `outputs/`, available via `GET /view?filename=...`.
- Public endpoint (Cloudflare Tunnel, fixed domain): `https://api.ksmart.com.es` (named tunnel `api-ksmart-tunnel`; binary at `cloudflared`, account cert at `~/.cloudflared/cert.pem`). All API routes (`/prompt`, `/history`, `/queue`, `/view`, `/ws`) require API key; the GUI page (`/`) is open.
- API key: required as `X-API-Key` header or `api_key` query param. Default key (env `API_KEY`) = `ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf`.
- Models: present under the workspace (used names/locations):
   - Diffusion (default): `models/diffusion_models/flux2_dev_nvfp4.safetensors` (NVFP4, fits T4 16GB, better anatomy than klein). Fallback: `flux2_dev_fp8mixed.safetensors` → `flux-2-klein-4b-fp8.safetensors`.
   - Text encoder: `models/text_encoders/split_files/text_encoders/qwen_3_4b.safetensors`
   - VAE: `models/vae/split_files/vae/flux2-vae.safetensors`
   - Text encoder: `models/text_encoders/split_files/text_encoders/qwen_3_4b.safetensors`
   - VAE: `models/vae/split_files/vae/flux2-vae.safetensors`
- API: `server.py` (FastAPI) exposes endpoints:
  - `POST /prompt` — enqueue a job
  - `GET /history/{prompt_id}` — job status
  - `GET /queue` — list jobs
  - `GET /view?filename=...` — download output file
  - WebSocket `/ws` — realtime events
- Worker: `worker.py` polls `jobs/` and calls `run_workflow.py`. `run_workflow.py` builds a FLUX2 prompt graph and calls ComfyUI HTTP `/prompt` API; on success it copies the generated `flux2_*.png` from `output/` into `outputs/` and records `result.file`. If ComfyUI is unreachable it falls back to a dummy Pillow PNG in `outputs/`.

## Last run (test)
- Recent real Flux2 outputs (saved by ComfyUI `SaveImage` into `output/`):
   - `output/flux2_00001_.png`
   - `output/flux2_00002_.png`
   - `output/flux2_00003_.png`
- Previous dummy fallback outputs (Pillow): `outputs/dummy_*.png`

## How to reproduce locally
1. Install dependencies (if not already):
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Start API server (wrapper):
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```
3. Start worker (or run one-shot processor):
   ```bash
   python worker.py     # continuous poll
   # or run a single job
   python -c "from worker import run_job; run_job('create_real_image', Path('jobs/create_real_image.json'))"
   ```
4. Send a job (example):
   ```bash
   curl -X POST "http://localhost:8000/prompt" -H "Content-Type: application/json" -d @example_workflow.json
   ```
5. Poll status and download output:
   ```bash
   curl "http://localhost:8000/history/<prompt_id>"
   curl "http://localhost:8000/view?filename=<output_filename>" -o downloaded.png
   ```

## Restart / recovery steps (after machine shutdown)

1. Ensure you are in the workspace root `/teamspace/studios/this_studio`.
2. Start ComfyUI (must run before sending prompts):
   ```bash
   # run ComfyUI in background, base-directory points to workspace so it finds `models/`
   setsid python ComfyUI/main.py --listen 0.0.0.0 --port 8188 --disable-auto-launch --base-directory "$(pwd)" > comfy_launch.log 2>&1 &
   tail -f comfy_launch.log
   ```
3. Confirm ComfyUI is up: `curl -s http://127.0.0.1:8188/ | head -n1` (should return HTML). Also check `comfy_launch.log` for "Starting server" and no validation errors.
4. Start the API wrapper:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload &
   ```
5. Start the worker:
   ```bash
   python worker.py &
   ```
6. Resubmit any queued jobs in `jobs/*.json` or post a new prompt to `http://localhost:8000/prompt`.

## Notes / troubleshooting
- If ComfyUI rejects prompts with validation errors about model names, ensure encoder/vae are in `split_files/...` layout. Use `download_models.sh` to fetch recommended files and place them under `models/`.
- If a prompt times out during polling, check `comfy_launch.log` for validation or runtime errors and `output/` for generated images.
- To export produced images from `output/` into `outputs/`, run:
  ```bash
  mkdir -p outputs && cp output/flux2_* outputs/ || true
  ```

## Exposing to internet
- Option A: Lightning.ai deploy (recommended for production). See `README.md` for notes.
- Option B: Temporary tunnel with ngrok: `start_tunnel.py` exists but requires `pyngrok` and an ngrok auth token set in `NGROK_AUTH_TOKEN` environment variable. Install with:
  ```bash
  python -m pip install pyngrok
  export NGROK_AUTHTOKEN="<token>"
  python start_tunnel.py
  ```

## Next recommended steps
1. Install/clone ComfyUI into the workspace and ensure `main.py` launches the real ComfyUI server (or modify `server.py` to start ComfyUI entrypoint).
2. Download the three model files into:
   - `models/diffusion_models/`
   - `models/text_encoders/`
   - `models/vae/`
3. Replace `run_workflow.py` fallback with actual ComfyUI execution API (or use ComfyUI Python internals) in `worker.run_job()`.
4. Deploy to Lightning.ai or run ngrok for public testing.

If you want, I can proceed to install ComfyUI and integrate it now, or prepare a Lightning.ai deployment manifest and Docker image.
