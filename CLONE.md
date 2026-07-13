# ksmart-image-api

API server sinh ảnh bằng ComfyUI + FLUX.2, expose qua public endpoint `https://api.ksmart.com.es`.
Chạy được trên bất kỳ máy Linux có NVIDIA GPU (đã test Tesla T4 16GB).

## Cấu trúc repo

- `server.py` — FastAPI wrapper, tự khởi ComfyUI + worker (best-effort), expose `/prompt`, `/history`, `/queue`, `/view`, `/ws`.
- `worker.py` — poll `jobs/`, gọi `run_workflow.py`.
- `run_workflow.py` — build FLUX2 prompt graph, gọi ComfyUI HTTP API, copy ảnh kết quả vào `outputs/`.
- `gui.html` — giao diện web nhập prompt.
- `start_server.sh` — khởi server + tunnel (Linux). `open_gui.bat` — mở GUI (Windows cmd).
- `start_tunnel.py` — Cloudflare tunnel tới domain cố định `api.ksmart.com.es`.
- `ComfyUI/` — **git submodule** (comfyanonymous/ComfyUI, pinned commit).
- `ENDPOINT.md`, `RUN.md`, `RESTART.md` — tài liệu chi tiết từng phần.

## Clone về máy GPU khác

```bash
git clone --recurse-submodules <YOUR_REPO_URL> ksmart-image-api
cd ksmart-image-api
# Nếu đã clone mà quên --recurse-submodules:
# git submodule update --init --recursive
```

## Cài đặt

```bash
python -m pip install -r requirements.txt
# ComfyUI deps (chạy trong submodule):
pip install -r ComfyUI/requirements.txt
# Nếu dùng torch GPU:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Models (không commit vào repo, tải riêng)

Đặt models vào (đúng layout `split_files`):
- `models/diffusion_models/flux-2-klein-4b-fp8.safetensors`
- `models/text_encoders/split_files/text_encoders/qwen_3_4b.safetensors`
- `models/vae/split_files/vae/flux2-vae.safetensors`

Tải nhanh:
```bash
./download_models.sh
# hoặc copy thủ công từ máy cũ: scp -r models/ user@newhost:/path/ksmart-image-api/
```

## Chạy (GPU)

```bash
# 1) ComfyUI (cần GPU, chạy trước)
setsid python ComfyUI/main.py --listen 0.0.0.0 --port 8188 \
  --disable-auto-launch --base-directory "$(pwd)" > comfy_launch.log 2>&1 &
# Kiểm tra: curl -s http://127.0.0.1:8188/ | head -n1  -> HTML

# 2) API server + worker
bash start_server.sh
# hoặc thủ công:
# setsid python server.py > api_server.log 2>&1 &
# setsid python worker.py > worker.log 2>&1 &
```

## Gửi prompt (test local)

```bash
curl -X POST "http://127.0.0.1:8000/prompt" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" \
  -d '{"client_id":"gui","prompt":{"prompt":"A red dragon over mountains, cinematic"}}'
```

Xem `ENDPOINT.md` để lấy ảnh thật qua `/view` và public endpoint.

## Public endpoint (tùy chọn)

Cần binary `cloudflared` + cert `~/.cloudflared/cert.pem`, rồi:
```bash
python start_tunnel.py   # forward localhost:8000 -> https://api.ksmart.com.es
```

## Lưu ý

- Không có GPU → worker sinh dummy PNG (fallback). Ảnh thật cần NVIDIA GPU.
- `models/`, `outputs/`, `*.log` đã nằm trong `.gitignore` — không commit.
- ComfyUI là submodule: update bằng `cd ComfyUI && git pull && cd .. && git add ComfyUI`.
