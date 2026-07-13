# Hướng dẫn khởi động lại hệ thống

Dùng sau khi tắt máy / container mới. Thứ tự: **ComfyUI → API server → worker → tunnel**.

> Lưu ý GPU: ComfyUI cần NVIDIA GPU. Nếu session này không gắn GPU
> (`python ComfyUI/main.py` báo "Found no NVIDIA driver"), bỏ qua bước ComfyUI —
> worker vẫn chạy nhưng sẽ sinh **dummy PNG**. Sinh ảnh thật cần chạy trên máy có GPU
> (VPS T4 hoặc Lightning.ai, xem `LIGHTNING_DEPLOY.md`).

## 1) Vào workspace

```bash
cd /teamspace/studios/this_studio
```

## 2) Khởi ComfyUI (cần GPU)

```bash
setsid python ComfyUI/main.py --listen 0.0.0.0 --port 8188 \
  --disable-auto-launch --base-directory "$(pwd)" > comfy_launch.log 2>&1 &
```

Kiểm tra: `curl -s http://127.0.0.1:8188/ | head -n1` → HTML. Xem `comfy_launch.log`.

## 3) Khởi API server

```bash
setsid python server.py > api_server.log 2>&1 &
# hoặc: uvicorn server:app --host 0.0.0.0 --port 8000
```

Kiểm tra (cần key):
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "http://127.0.0.1:8000/queue?api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
# mong đợi 200; nếu bỏ key → 401
```

## 4) Khởi worker

```bash
setsid python worker.py > worker.log 2>&1 &
```

## 5) Khởi Cloudflare Tunnel (domain cố định)

Tunnel `api-ksmart-tunnel` đã tạo, DNS `api.ksmart.com.es` đã route sẵn:

```bash
python start_tunnel.py
# tương đương: ./cloudflared tunnel run --url http://localhost:8000 api-ksmart-tunnel
```

Kiểm tra public:
```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  "https://api.ksmart.com.es/queue?api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
```

## 6) Lưu ý

- API server tự động khởi ComfyUI + worker ở startup (best-effort). Nếu muốn tự quản lý từng process, dùng các lệnh trên.
- Đổi key: set env `API_KEY` trước khi chạy `server.py`.
- Nếu tunnel dừng: chạy lại `python start_tunnel.py`.
- Log quan trọng: `comfy_launch.log`, `api_server.log`, `worker.log`, `tunnel.log`.
