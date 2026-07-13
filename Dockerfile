FROM python:3.10-slim
WORKDIR /app
COPY . /app
RUN apt-get update && apt-get install -y wget git && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1
EXPOSE 8000 8188

# Clone ComfyUI and install its requirements (best-effort)
RUN if [ ! -d "ComfyUI" ]; then git clone https://github.com/comfyanonymous/ComfyUI.git ComfyUI || true; fi
RUN if [ -f "ComfyUI/requirements.txt" ]; then pip install -r ComfyUI/requirements.txt || true; fi

# Ensure models directories exist
RUN mkdir -p /app/models/diffusion_models /app/models/text_encoders /app/models/vae

# Start FastAPI server (API). `server.py` will attempt to start ComfyUI subprocess.
CMD ["/bin/bash", "-lc", "uvicorn server:app --host 0.0.0.0 --port 8000"]
