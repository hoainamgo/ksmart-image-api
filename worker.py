import time
import json
from pathlib import Path
import subprocess
from run_workflow import call_comfyui_api, save_output_text

BASE = Path(__file__).resolve().parent
JOBS_DIR = BASE / "jobs"
OUTPUTS_DIR = BASE / "outputs"


def run_job(job_id: str, job_path: Path):
    print(f"Running job {job_id}")
    with open(job_path, 'r') as f:
        job = json.load(f)
    workflow = job.get('payload', {}).get('prompt') or job.get('payload')

    # Try to call ComfyUI via HTTP API; fallback to dummy image generation
    result = call_comfyui_api(workflow)

    # Save metadata result into the original job json file so API can read it
    job['status'] = 'finished' if result else 'failed'
    job['result'] = result
    with open(job_path, 'w') as f:
        json.dump(job, f, indent=2)

    # If result references a generated file, ensure it's in outputs and return name
    out_file = None
    if isinstance(result, dict):
        if 'file' in result:
            out_file = result['file']
        elif 'path' in result:
            out_file = Path(result['path']).name

    if out_file is None:
        out_file = save_output_text(job_id, json.dumps({'job': job_id, 'result': result}, indent=2))

    # If the original job included a callback_url, POST result there
    try:
        callback = job.get('payload', {}).get('callback_url')
        if callback:
            import requests
            requests.post(callback, json={'job_id': job_id, 'result': result}, timeout=10)
    except Exception:
        pass

    return out_file, result


def main():
    print("Worker started, polling jobs/...\n")
    while True:
        jobs = sorted(JOBS_DIR.glob('*.json'))
        if not jobs:
            time.sleep(1)
            continue
        for jp in jobs:
            job_id = jp.stem
            proc_path = JOBS_DIR / f"{job_id}.processing"
            try:
                jp.rename(proc_path)
            except Exception:
                continue
            try:
                out_name, out_meta = run_job(job_id, proc_path)
                proc_path.rename(JOBS_DIR / f"{job_id}.done")
                print(f"Job {job_id} done -> {out_name}")
            except Exception as e:
                print(f"Job {job_id} failed: {e}")
                proc_path.rename(JOBS_DIR / f"{job_id}.error")


if __name__ == '__main__':
    main()
