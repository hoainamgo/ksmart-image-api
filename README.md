# ComfyUI on Lightning.ai - scaffold

Mục tiêu: chạy ComfyUI trên Lightning.ai, public endpoint cho `/prompt`, `/history/{id}`, `/queue`, `/view`, và WebSocket `/ws`.

Tệp chính:
- `server.py`: FastAPI wrapper; start ComfyUI subprocess and exposes API.
- `worker.py`: simple poller that processes `jobs/` (placeholder — replace with ComfyUI execution logic).
- `download_models.sh`: helper để tải các files mô hình vào `models/`.
- `Dockerfile`, `requirements.txt`.

Thư mục mô hình (theo yêu cầu):
- `models/diffusion_models/`
- `models/text_encoders/`
- `models/vae/`

Chạy local (tùy biến):

1) Cài dependencies:
```bash
python -m pip install -r requirements.txt
```

2) Tải mô hình (nếu wget không được, tải thủ công từ Hugging Face):
```bash
./download_models.sh
```

3) Chạy server (sẽ tự khởi ComfyUI trên port 8188 và API trên 8000):
```bash
python server.py
# hoặc dùng uvicorn trực tiếp:
uvicorn server:app --host 0.0.0.0 --port 8000
```

4) Chạy worker để process job queue (thay thế nội dung `run_job` bằng logic gọi ComfyUI hoặc thực thi workflow):
```bash
python worker.py
```

Test với `example_workflow.json`:

```bash
curl -X POST "http://localhost:8000/prompt" \
  -H "Content-Type: application/json" \
  -d @example_workflow.json

# Sau khi có prompt_id, poll kết quả:
curl "http://localhost:8000/history/<prompt_id>"
```

API mẫu:
- POST `/prompt` -> body JSON: `{ "client_id":"...", "prompt": { ... workflow json ... } }` returns `{ "prompt_id": "..." }`
- GET `/history/{prompt_id}` -> trạng thái job
- GET `/queue` -> danh sách job đang xếp
- GET `/view?filename=...` -> lấy file từ `outputs/`
- WebSocket `/ws` -> nhận event realtime (queued, started, finished)

Deployment trên Lightning.ai
- Tùy cách Lightning.ai cung cấp: bạn có thể deploy bằng Docker image (upload image or push to registry and connect via Lightning cloud), hoặc sử dụng Lightning Apps to run the container and Lightning sẽ cấp một public URL.
- Nếu Lightning.ai tự cấp public URL khi deploy container, dùng URL đó (ví dụ `https://<PUBLIC_URL>/prompt`).
- Nếu không, sử dụng tunnel (ngrok, cloudflared) hoặc cấu hình reverse-proxy của Lightning.

Expose to internet
- Sử dụng domain cố định `https://api.ksmart.com.es` (Cloudflare Tunnel) thay vì URL động.
- `cloudflared` binary đã có sẵn trong workspace; tài khoản cert tại `~/.cloudflared/cert.pem`.
- Chạy tunnel: `python start_tunnel.py` (forward `http://localhost:8000` -> `https://api.ksmart.com.es`).
- Biến môi trường: `PORT` (mặc định 8000), `TUNNEL_HOSTNAME` (mặc định `api.ksmart.com.es`).

Gợi ý cấu hình cho T4 16GB
- Đặt batch size = 1, resolution giảm nếu OOM (768 hoặc 896), sử dụng FLUX.2-klein-4b-fp8.
- Đặt mô hình vào `models/diffusion_models/`, text encoder vào `models/text_encoders/`, vae vào `models/vae/`.

Tiếp theo (bạn/cộng tác viên cần làm):
1. Thay `worker.run_job()` bằng logic gọi API nội bộ của ComfyUI hoặc sử dụng ComfyUI Python API để chạy workflow JSON (tham khảo https://docs.comfy.org/tutorials/flux/flux-2-klein và tài liệu ComfyUI).
2. Nếu muốn, nâng cấp `server.py` để forward workflow trực tiếp tới ComfyUI HTTP/WebSocket API (nếu có) thay vì worker polling.
3. Triển khai container trên Lightning.ai hoặc push image lên registry và cấu hình.

Ví dụ curl gửi job:
```bash
curl -X POST "http://<PUBLIC_URL>/prompt" \
  -H "Content-Type: application/json" \
  -d '{"client_id":"pc-remote-01","prompt": { /* workflow JSON */ }}'
```

Ghi chú: scaffold này triển khai API, queueing và WebSocket broadcast. Việc gọi và chạy workflow trong ComfyUI phụ thuộc vào cách bạn muốn tích hợp (ComfyUI internal API hoặc chạy task bằng Python), vui lòng cập nhật `worker.py` hoặc thêm module `run_workflow.py` theo tài liệu ComfyUI.
