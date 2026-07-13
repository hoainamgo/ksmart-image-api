from lightning import LightningApp, LightningWork, CloudCompute
import subprocess
import os


class ComfyServerWork(LightningWork):
    def __init__(self, **kwargs):
        super().__init__(parallel=True, **kwargs)

    def run(self):
        # Ensure models dir exists (user must provide model files via artifact or mount)
        os.makedirs('models/diffusion_models', exist_ok=True)
        os.makedirs('models/text_encoders', exist_ok=True)
        os.makedirs('models/vae', exist_ok=True)

        # Start the FastAPI server (server.py will try to start ComfyUI subprocess)
        cmd = ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
        subprocess.run(cmd)


app = LightningApp(ComfyServerWork(cloud_compute=CloudCompute("t4", 1), mounts=[]))
