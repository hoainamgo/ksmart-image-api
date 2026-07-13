# HƯỚNG DẪN CHẠY (Quick Run Guide)

Môi trường: `ComfyUI` trong `ComfyUI/`, model dưới `models/` (xem `context.md`).
API server: FastAPI `server.py` (tự khởi ComfyUI + worker, best-effort).

> Cần GPU NVIDIA để ComfyUI sinh ảnh thật. Container không có GPU sẽ chỉ sinh
> dummy PNG. Xem `RESTART.md` (phần lưu ý GPU) và `LIGHTNING_DEPLOY.md`.

## 1) Cài đặt phụ thuộc

```bash
python -m pip install -r requirements.txt
```

## 2) Khởi ComfyUI (cần GPU, chạy trước khi gửi prompt)

```bash
setsid python ComfyUI/main.py --listen 0.0.0.0 --port 8188 \
  --disable-auto-launch --base-directory "$(pwd)" > comfy_launch.log 2>&1 &
# Kiểm tra: curl -s http://127.0.0.1:8188/ | head -n1  → HTML
```

## 3) Khởi API server

```bash
setsid python server.py > api_server.log 2>&1 &
# hoặc: uvicorn server:app --host 0.0.0.0 --port 8000
```

API key bắt buộc với mọi route API (GUI mở). Đổi key qua env `API_KEY` trước khi chạy.

## 4) Khởi worker

```bash
setsid python worker.py > worker.log 2>&1 &
# Hoặc 1 job đơn: python -c "from worker import run_job; from pathlib import Path; run_job('create_real_image', Path('jobs/create_real_image.json'))"
```

## 5) Gửi job mẫu

```bash
curl -X POST "http://127.0.0.1:8000/prompt" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" \
  -d @example_workflow.json
```

## 6) Kiểm tra & tải ảnh

```bash
curl "http://127.0.0.1:8000/history/<prompt_id>?api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
curl "http://127.0.0.1:8000/view?filename=<output_filename>&api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" -o downloaded.png
```

## 7) Sao chép ảnh ComfyUI (nếu ghi vào `output/`)

```bash
mkdir -p outputs && cp output/flux2_* outputs/ || true
```

## GUI (cấu hình trong trình duyệt)

Mở `http://localhost:8000/` (hoặc `https://api.ksmart.com.es/`).
- **API base URL**: để trống = origin hiện tại; hoặc nhập URL public.
- **API key**: nhập `ksmart_...`, GUI lưu trong `localStorage` và tự gửi kèm mọi request.
Xem chi tiết ở `ENDPOINT.md`.

## Troubleshooting

- `Value not in list` cho `vae_name`/`clip_name`: đảm bảo file encoder/vae dưới `split_files/...`.
- Job `timeout`: xem `comfy_launch.log`.
- `dummy_generated`: ComfyUI không chạy (thiếu GPU).
- `401`: thiếu/sai API key.

## Model download

Script `download_models.sh` tải encoder/VAE gợi ý. Thủ công đặt vào:
- `models/diffusion_models/` (hoặc `.../split_files/diffusion_models/`)
- `models/text_encoders/split_files/text_encoders/`
- `models/vae/split_files/vae/`
