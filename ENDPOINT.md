# Hướng dẫn tạo ảnh qua API Endpoint

## Endpoint

| Môi trường | URL |
|---|---|
| Local (trong studio) | `http://localhost:8000` |
| Public (Cloudflare Tunnel, fixed domain) | `https://api.ksmart.com.es` |

Public endpoint đi qua **named tunnel** `api-ksmart-tunnel` (DNS CNAME `api.ksmart.com.es` → tunnel).
Domain cố định, không đổi mỗi lần khởi động.

## API key (bắt buộc với mọi API route)

Tất cả route API (`/prompt`, `/history`, `/queue`, `/view`, `/ws`) đều yêu cầu key.
Trang GUI (`/`) mở, không cần key, nhưng GUI có ô **API key** để gửi kèm khi gọi API.

- Gửi key qua header: `X-API-Key: <KEY>`
- Hoặc query param: `?api_key=<KEY>` (WebSocket dùng `?api_key=<KEY>`)
- Key mặc định (env `API_KEY`): `ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf`

Thiếu/sai key → `401 Unauthorized`.

| Method | Path | Mô tả |
|---|---|---|
| `POST` | `/prompt` | Gửi yêu cầu tạo ảnh |
| `GET` | `/history/{prompt_id}` | Xem trạng thái job |
| `GET` | `/view?filename=...` | Tải file ảnh kết quả |
| `GET` | `/queue` | Danh sách job đang chờ / đã xử lý |
| `GET` | `/` | Giao diện GUI (nhập prompt trực tiếp) |
| `WS` | `/ws?api_key=...` | Nhận event realtime (queued/finished) |

---

## Cách 1 — Dùng GUI (nhanh nhất)

1. Mở `https://api.ksmart.com.es/` (hoặc `http://localhost:8000/`).
2. Nhập **API base URL** nếu gọi từ máy khác (để trống = origin hiện tại).
3. Nhập **API key** (`ksmart_...`). GUI lưu trong browser.
4. Gõ prompt → bấm **Submit**. Click **Job ID** để xem trạng thái.

---

## Cách 2 — Prompt đơn giản (curl / code)

```bash
curl -X POST "https://api.ksmart.com.es/prompt" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" \
  -d '{
    "client_id": "my-pc",
    "prompt": { "prompt": "A serene mountain lake at sunrise, photorealistic" }
  }'
```

**Response:** `{"prompt_id": "a1b2c3d4e5f6..."}`

---

## Cách 3 — Workflow FLUX.2 đầy đủ (khuyến nghị)

```bash
curl -X POST "https://api.ksmart.com.es/prompt" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" \
  -d @example_workflow.json
```

`example_workflow.json`:

```json
{
  "type": "flux_workflow",
  "model": "FLUX.2-klein-4b-fp8",
  "steps": [{"node": "txt2img", "prompt": "A scenic landscape, sunrise, detailed"}],
  "settings": {"width": 768, "height": 768, "batch_size": 1}
}
```

---

## Bước 2 — Kiểm tra trạng thái

```bash
PROMPT_ID="a1b2c3d4e5f6..."
curl "https://api.ksmart.com.es/history/$PROMPT_ID?api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
```

Khi xong → `"status": "finished"` kèm `result`. Nếu ComfyUI không chạy, kết quả là
ảnh dummy (placeholder) với `"status": "dummy_generated"` và `"file": "dummy_xxx.png"`.

---

## Bước 3 — Tải ảnh kết quả

```bash
FILENAME="dummy_16593_4297425.png"   # lấy từ result.file
curl "https://api.ksmart.com.es/view?filename=$FILENAME&api_key=ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf" -o result.png
```

API `/view` phục vụ file trong `outputs/`. Ảnh Flux2 thật do ComfyUI lưu vào `output/` trên server.

---

## Script hoàn chỉnh (bash)

```bash
BASE="https://api.ksmart.com.es"
KEY="ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"

RESP=$(curl -s -X POST "$BASE/prompt" -H "Content-Type: application/json" \
  -H "X-API-Key: $KEY" \
  -d '{"client_id":"script","prompt":{"prompt":"A red dragon over mountains, cinematic"}}')
PROMPT_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['prompt_id'])")
echo "Job ID: $PROMPT_ID"

for i in $(seq 1 60); do
  STATUS=$(curl -s "$BASE/history/$PROMPT_ID?api_key=$KEY" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
  echo "[$i] status=$STATUS"
  if [ "$STATUS" = "finished" ] || [ "$STATUS" = "failed" ]; then break; fi
  sleep 5
done

FILENAME=$(curl -s "$BASE/history/$PROMPT_ID?api_key=$KEY" | python3 -c "import sys,json; r=json.load(sys.stdin).get('result') or {}; print(r.get('file',''))")
if [ -n "$FILENAME" ]; then
  curl -s "$BASE/view?filename=$FILENAME&api_key=$KEY" -o result.png && echo "Saved: result.png"
else
  echo "No output file. Full:"; curl -s "$BASE/history/$PROMPT_ID?api_key=$KEY"
fi
```

---

## Gọi từ Python

```python
import time, requests

BASE = "https://api.ksmart.com.es"
KEY  = "ksmart_3xS33jgnnArmLawramxsByHnBmgyQ1w4Z96SdkcLf"
H    = {"X-API-Key": KEY}

resp = requests.post(f"{BASE}/prompt", headers=H, json={
    "type": "flux_workflow", "model": "FLUX.2-klein-4b-fp8",
    "steps": [{"node": "txt2img", "prompt": "A cyberpunk street at night"}],
    "settings": {"width": 768, "height": 768, "steps": 20, "seed": 42},
})
prompt_id = resp.json()["prompt_id"]

for _ in range(60):
    job = requests.get(f"{BASE}/history/{prompt_id}", headers=H).json()
    if job.get("status") in ("finished", "failed"): break
    time.sleep(5)

filename = (job.get("result") or {}).get("file")
if filename:
    r = requests.get(f"{BASE}/view", headers=H, params={"filename": filename})
    open("result.png", "wb").write(r.content)
    print("saved result.png")
```

---

## Xử lý lỗi

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `401` | Thiếu/sai API key | Thêm header `X-API-Key` hoặc `?api_key=` |
| `dummy_generated` trong result | ComfyUI không chạy (không có GPU trong session này) | Khởi ComfyUI trên máy có GPU, xem `RUN.md` |
| `status: queued` lâu | Worker chưa chạy | Chạy `python worker.py` |
| `/view` 404 | File chưa có trong `outputs/` | Xem `result.file` trong `/history` |

## Tóm tắt luồng

```
POST /prompt (+X-API-Key) → nhận prompt_id
        ↓
Worker xử lý → gọi ComfyUI (FLUX.2)  [fallback dummy nếu ComfyUI mất]
        ↓
GET /history/{id} (+key) → status: finished + result.file
        ↓
GET /view?filename=...&api_key=... → tải PNG
```
