# Lightning.ai quick deploy

This guide shows two fast ways to deploy the API on Lightning.ai (T4 GPU) so you get a public URL.

Prereqs:
- Have a Lightning.ai account and `lightning` CLI installed: `pip install lightning`.
- (Optional) Push Docker image to a registry if you prefer custom image flow.

Option 1 — Quick deploy using the repo and `lightning_app.py` (recommended for speed)
1. Ensure `requirements.txt` includes all Python deps. Add any ComfyUI-specific requirements if needed.
2. Login to Lightning:
```bash
lightning login
```
3. Run the app on Lightning Cloud (this will upload your repo and run `lightning_app.py` on a T4):
```bash
lightning run cloud lightning_app.py --name comfyui-api --requirements requirements.txt
```
4. Lightning will provision the instance (T4), build environment, and provide a public URL. Use that URL as `PUBLIC_URL` in previous instructions.

Notes:
- To include large model files, either:
  - Upload them as artifacts and mount into the app; or
  - Build a Docker image with models preinstalled and use the Docker image flow.

Option 2 — Deploy a prebuilt Docker image
1. Build and push your Docker image (see `deploy_lightning.sh`):
```bash
export DOCKER_REPO=myuser/comfyui-api
export IMAGE_NAME=latest
./deploy_lightning.sh
```
2. In Lightning Cloud UI create a new app and select "Custom Container" pointing to `myuser/comfyui-api:latest`, choose GPU type `t4`, and deploy. Lightning will provide a public URL.

After deployment
- Use the public URL to POST `/prompt`, poll `/history/{id}`, and fetch outputs via `/view`.
- If you want notifications, include `callback_url` in the job payload; `worker.py` will POST result when done.
