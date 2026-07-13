#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(dirname "$0")"
mkdir -p "$BASE_DIR/models/diffusion_models"
mkdir -p "$BASE_DIR/models/text_encoders"
mkdir -p "$BASE_DIR/models/vae"

echo "Downloading FLUX.2 [klein] 4B distilled FP8 (may require HF token for large files)"
cd "$BASE_DIR/models/diffusion_models"
echo "Please download the model manually if wget fails (Large files may require authentication)."
echo "URL: https://huggingface.co/black-forest-labs/FLUX.2-klein-4b-fp8"

cd "$BASE_DIR/models/text_encoders"
echo "Downloading text encoder..."
wget -c "https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors" || echo "wget failed; please download manually"

cd "$BASE_DIR/models/vae"
echo "Downloading VAE..."
wget -c "https://huggingface.co/Comfy-Org/flux2-dev/resolve/main/split_files/vae/flux2-vae.safetensors" || echo "wget failed; please download manually"

echo "Done. Place diffusion model files under models/diffusion_models/."
