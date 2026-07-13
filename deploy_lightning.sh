#!/usr/bin/env bash
set -euo pipefail

# deploy_lightning.sh
# Build Docker image for the ComfyUI API and push to a container registry.
# Then deploy via Lightning.ai by pointing the cloud service to the image.

IMAGE_NAME=${IMAGE_NAME:-comfyui-api:latest}
DOCKER_REPO=${DOCKER_REPO:-}

if [ -z "$DOCKER_REPO" ]; then
  echo "Set DOCKER_REPO (e.g. myuser/comfyui-api) before running."
  echo "Example: DOCKER_REPO=myuser/comfyui-api IMAGE_NAME=latest $0"
  exit 2
fi

echo "Building Docker image $DOCKER_REPO:$IMAGE_NAME"
docker build -t "$DOCKER_REPO:$IMAGE_NAME" .

echo "Pushing to Docker registry. Make sure you are logged in (docker login)."
docker push "$DOCKER_REPO:$IMAGE_NAME"

echo "Image pushed: $DOCKER_REPO:$IMAGE_NAME"
echo "Next: create a Lightning.ai deployment that uses this image."
echo "- Option A (Lightning Cloud UI): create a new app and use the image name above."
echo "- Option B (Lightning CLI): use Lightning's instructions to deploy a custom image." 
echo "If you want, provide registry/image here and I can guide the Lightning UI steps." 
