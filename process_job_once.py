import sys
import json
from pathlib import Path
from run_workflow import call_comfyui_api

BASE = Path(__file__).resolve().parent
JOBS_DIR = BASE / "jobs"
OUTPUTS_DIR = BASE / "outputs"


def process(job_id: str):
    p = JOBS_DIR / f"{job_id}.json"
    if not p.exists():
        print('job file not found', p)
        return 2
    with open(p, 'r') as f:
        job = json.load(f)
    workflow = job.get('payload', {}).get('prompt') or job.get('payload')
    res = call_comfyui_api(workflow)
    job['status'] = 'finished'
    job['result'] = res
    with open(p, 'w') as f:
        json.dump(job, f, indent=2)
    print('result:', res)
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: process_job_once.py <job_id>')
        sys.exit(2)
    sys.exit(process(sys.argv[1]))
