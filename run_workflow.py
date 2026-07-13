import requests
import json
import os
import time
from pathlib import Path
from io import BytesIO
try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None

BASE = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE / "outputs"

SEARCH_PATHS = [
    BASE / "models" / "diffusion_models",
    BASE / "models" / "text_encoders",
    BASE / "models" / "vae",
    BASE / "ComfyUI" / "models" / "diffusion_models",
    BASE / "ComfyUI" / "models" / "text_encoders",
    BASE / "ComfyUI" / "models" / "vae",
]

def find_model_file(filename: str) -> Path | None:
    if not filename:
        return None
    candidate = Path(filename)
    if candidate.is_absolute() and candidate.exists():
        return candidate
    for root in SEARCH_PATHS:
        path = root / filename
        if path.exists():
            return path
        # fallback: search recursively under the root for the filename
        try:
            for p in root.rglob(filename):
                if p.exists():
                    return p
        except Exception:
            pass
    return None


def is_comfy_prompt_graph(workflow: dict) -> bool:
    if not isinstance(workflow, dict):
        return False
    for value in workflow.values():
        if isinstance(value, dict) and "class_type" in value:
            return True
    return False


def normalize_model_name(model_name: str) -> str:
    if not model_name:
        return "flux-2-klein-4b-fp8.safetensors"
    if model_name.endswith(".safetensors"):
        return model_name
    normalized = model_name.strip().lower().replace(" ", "-").replace(".2", "-2").replace(".", "-")
    if not normalized.endswith(".safetensors"):
        normalized += ".safetensors"
    return normalized


def choose_flux2_clip_name() -> str:
    candidates = [
        "qwen_3_4b.safetensors",
        "mistral_3_small_flux2_bf16.safetensors",
        "mistral_3_small_flux2_fp8.safetensors",
        "mistral_3_small_flux2_fp4_mixed.safetensors",
    ]
    for name in candidates:
        if find_model_file(name) is not None:
            return name
    return candidates[0]


def choose_flux2_vae_name() -> str:
    candidates = ["flux2-vae.safetensors", "flux2_vae.safetensors"]
    for name in candidates:
        if find_model_file(name) is not None:
            return name
    return "flux2-vae.safetensors"


def build_flux2_prompt(payload: dict) -> dict:
    prompt_text = None
    if isinstance(payload.get("prompt"), str):
        prompt_text = payload["prompt"]
    else:
        for step in payload.get("steps", []):
            if isinstance(step, dict) and step.get("node") in ("txt2img", "txt2img_1", "txt2img_default"):
                prompt_text = step.get("prompt")
                break
    prompt_text = prompt_text or payload.get("description") or payload.get("text") or ""

    settings = payload.get("settings", {})
    width = settings.get("width", 768)
    height = settings.get("height", 768)
    batch_size = settings.get("batch_size", 1)
    steps = settings.get("steps", 20)
    sampler_name = settings.get("sampler_name", "euler")
    seed = settings.get("seed", 1234)
    guidance = settings.get("guidance", 3.5)

    model_name = payload.get("model") or payload.get("unet_name") or "flux-2-klein-4b-fp8"
    model_name = normalize_model_name(model_name)
    if find_model_file(model_name) is None:
        alt_name = model_name.lower().replace("flux-2-klein-4b-fp8", "flux2_dev_fp8mixed")
        if find_model_file(alt_name) is not None:
            model_name = alt_name

    clip_name = choose_flux2_clip_name()
    vae_name = choose_flux2_vae_name()

    # If model files live under split_files, ComfyUI expects the path starting at
    # the 'split_files' directory (e.g. 'split_files/text_encoders/qwen_3_4b.safetensors')
    def to_comfy_name(name: str) -> str:
        p = find_model_file(name)
        if p is None:
            return name
        parts = [str(x) for x in p.parts]
        if 'split_files' in parts:
            idx = parts.index('split_files')
            return '/'.join(parts[idx:])
        # If the exact file isn't under a split_files tree, try to find any
        # split_files variant elsewhere in the workspace (ComfyUI choices
        # often list only the split_files version).
        basename = p.name
        for root in SEARCH_PATHS:
            try:
                for candidate in root.rglob(basename):
                    if 'split_files' in candidate.parts:
                        idx = list(candidate.parts).index('split_files')
                        return '/'.join(candidate.parts[idx:])
            except Exception:
                pass
        return name

    clip_name = to_comfy_name(clip_name)
    vae_name = to_comfy_name(vae_name)

    # Force exact split_files path for known Flux2 encoder/vae if present
    qwen_path = BASE / 'models' / 'text_encoders' / 'split_files' / 'text_encoders' / 'qwen_3_4b.safetensors'
    if qwen_path.exists():
        clip_name = 'split_files/text_encoders/qwen_3_4b.safetensors'
    # More robust: if any split_files variant exists for the basename, prefer it
    def prefer_split_variant(name: str) -> str:
        # if already looks like a split_files path, keep it
        if name.startswith('split_files/'):
            return name
        basename = Path(name).name
        for root in SEARCH_PATHS:
            try:
                for candidate in root.rglob(basename):
                    if 'split_files' in candidate.parts:
                        idx = list(candidate.parts).index('split_files')
                        return '/'.join(candidate.parts[idx:])
            except Exception:
                pass
        return name

    vae_name = prefer_split_variant(vae_name)
    clip_name = prefer_split_variant(clip_name)

    return {
        "1": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": model_name,
                "weight_dtype": "default",
            },
        },
        "2": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": clip_name,
                "type": "flux2",
                "device": "default",
            },
        },
        "3": {
            "class_type": "VAELoader",
            "inputs": {
                "vae_name": vae_name,
            },
        },
        "4": {
            "class_type": "Flux2Scheduler",
            "inputs": {
                "steps": steps,
                "width": width,
                "height": height,
            },
        },
        "5": {
            "class_type": "EmptyFlux2LatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": batch_size,
            },
        },
        "6": {
            "class_type": "RandomNoise",
            "inputs": {
                "noise_seed": seed,
            },
        },
        "7": {
            "class_type": "KSamplerSelect",
            "inputs": {
                "sampler_name": sampler_name,
            },
        },
        "8": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "clip": ["2", 0],
                "text": prompt_text,
            },
        },
        "9": {
            "class_type": "FluxGuidance",
            "inputs": {
                "conditioning": ["8", 0],
                "guidance": guidance,
            },
        },
        # BasicGuider converts CONDITIONING -> GUIDER and expects a MODEL input.
        "13": {
            "class_type": "BasicGuider",
            "inputs": {
                "model": ["1", 0],
                "conditioning": ["9", 0],
            },
        },
        "10": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["6", 0],
                "guider": ["13", 0],
                "sampler": ["7", 0],
                "sigmas": ["4", 0],
                "latent_image": ["5", 0],
            },
        },
        "11": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["10", 0],
                "vae": ["3", 0],
            },
        },
        "12": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "flux2",
                "images": ["11", 0],
            },
        },
    }


def poll_comfy_job(comfy_url: str, prompt_id: str, timeout: int = 600):
    deadline = time.time() + timeout
    job_url = comfy_url.rstrip("/") + f"/api/jobs/{prompt_id}"
    while time.time() < deadline:
        try:
            resp = requests.get(job_url, timeout=10)
            resp.raise_for_status()
            job = resp.json()
            status = job.get("status")
            if status in ("finished", "failed", "completed"):
                return job
        except Exception:
            pass
        time.sleep(1)
    return {"status": "timeout", "prompt_id": prompt_id}


def call_comfyui_api(workflow: dict, timeout: int = 600):
    comfy_url = os.environ.get('COMFYUI_URL', 'http://127.0.0.1:8188')
    prompt_payload = None

    if isinstance(workflow, dict) and workflow.get("type") == "flux_workflow":
        prompt_payload = {"prompt": build_flux2_prompt(workflow)}
    elif isinstance(workflow, dict) and "prompt" in workflow and isinstance(workflow["prompt"], dict):
        # Already a ComfyUI-style graph wrapper, e.g. {"prompt": {...nodes...}}
        prompt_payload = workflow
    elif isinstance(workflow, dict) and is_comfy_prompt_graph(workflow):
        prompt_payload = {"prompt": workflow}
    else:
        # Simple prompt string (GUI style: {"prompt": "..."} or {"prompt": {"prompt": "..."}})
        simple = None
        if isinstance(workflow, dict) and isinstance(workflow.get("prompt"), str):
            simple = workflow["prompt"]
        elif isinstance(workflow, dict) and isinstance(workflow.get("prompt"), dict):
            simple = workflow["prompt"].get("prompt") or workflow["prompt"].get("text")
        elif isinstance(workflow, str):
            simple = workflow
        if simple:
            prompt_payload = {"prompt": build_flux2_prompt({"prompt": simple})}
        else:
            prompt_payload = {"prompt": {"1": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 0], "text": str(workflow)}}}}

    try:
        # write prompt payload for debugging
        try:
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            with open(OUTPUTS_DIR / 'last_prompt.json', 'w') as pf:
                json.dump(prompt_payload, pf, indent=2)
        except Exception:
            pass
        resp = requests.post(comfy_url.rstrip("/") + "/prompt", json=prompt_payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        prompt_id = result.get("prompt_id")
        if prompt_id:
            job_result = poll_comfy_job(comfy_url, prompt_id, timeout)
            # Extract the generated image filename from ComfyUI job output.
            out_img = _extract_comfy_output_image(job_result)
            if out_img:
                copied = _copy_comfy_output(out_img)
                if copied:
                    return {"status": "finished", "prompt_id": prompt_id, "file": copied, "job": job_result}
            return {"status": "submitted", "prompt_id": prompt_id, "job": job_result}
        return result
    except Exception as exc:
        # Fallback to dummy image generation if ComfyUI is unavailable.
        if Image is not None:
            OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
            prompt = None
            if isinstance(workflow, dict):
                prompt_data = workflow.get('prompt')
                if isinstance(prompt_data, dict):
                    prompt = prompt_data.get('prompt') or prompt_data.get('text')
            if not prompt:
                prompt = str(workflow)
            img_name = _generate_dummy_image(prompt)
            return {"status": "dummy_generated", "file": img_name, "error": str(exc)}

        OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        fname = OUTPUTS_DIR / f"workflow_{os.getpid()}.json"
        with open(fname, 'w') as f:
            json.dump(prompt_payload, f)
        return {"status": "saved_workflow_file", "path": str(fname), "error": str(exc)}


def _extract_comfy_output_image(job_result: dict) -> str | None:
    """Pull the first image filename from a ComfyUI job result."""
    if not isinstance(job_result, dict):
        return None
    outputs = job_result.get("outputs") or {}
    for node_id, node_out in outputs.items():
        if not isinstance(node_out, dict):
            continue
        images = node_out.get("images") or []
        for img in images:
            if isinstance(img, dict) and img.get("filename"):
                sub = img.get("subfolder", "")
                name = img["filename"]
                return name if not sub else f"{sub}/{name}"
    # fall back to preview_output
    preview = job_result.get("preview_output") or {}
    if preview.get("filename"):
        return preview["filename"]
    return None


def _copy_comfy_output(comfy_path: str) -> str | None:
    """Copy a ComfyUI output image into the API outputs/ dir; return its basename."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [
        BASE / "output" / comfy_path,
        BASE / "ComfyUI" / "output" / comfy_path,
    ]
    src = next((p for p in candidates if p.exists()), None)
    if src is None:
        # try recursive search under output/ and ComfyUI/output/
        for root in (BASE / "output", BASE / "ComfyUI" / "output"):
            try:
                for p in root.rglob(Path(comfy_path).name):
                    if p.exists():
                        src = p
                        break
            except Exception:
                pass
            if src:
                break
    if src is None:
        return None
    dest = OUTPUTS_DIR / src.name
    try:
        import shutil
        shutil.copyfile(src, dest)
        return dest.name
    except Exception:
        return None
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new('RGB', size, color=(30, 30, 40))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    text = f"Prompt:\n{prompt_text}"
    draw.multiline_text((10, 10), text, fill=(230, 230, 230), font=font)
    fname = f"dummy_{os.getpid()}_{int(os.times()[4])}.png"
    path = OUTPUTS_DIR / fname
    img.save(path)
    return fname


def save_output_text(job_id: str, content: str):
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    p = OUTPUTS_DIR / f"{job_id}.txt"
    with open(p, 'w') as f:
        f.write(content)
    return p.name


if __name__ == '__main__':
    print('run_workflow module - not a CLI')
