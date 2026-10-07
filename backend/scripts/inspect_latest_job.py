import urllib.request
import json
import sys

run_id = sys.argv[1] if len(sys.argv) > 1 else '37663761731'
req = urllib.request.Request(
    f'https://api.github.com/repos/Uriel21900/Fragrance-Finder/actions/runs/{run_id}/jobs',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    for job in data.get('jobs', []):
        print(f"Job: {job['name']} - status={job['status']}, conclusion={job['conclusion']}", flush=True)
        for step in job.get('steps', []):
            print(f"  Step {step.get('number')}: {step['name']} -> status={step.get('status')}, conclusion={step.get('conclusion')}", flush=True)
