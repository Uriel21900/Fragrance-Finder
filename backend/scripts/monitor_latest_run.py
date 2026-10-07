import urllib.request, json

req = urllib.request.Request(
    'https://api.github.com/repos/Uriel21900/Fragrance-Finder/actions/runs?per_page=3',
    headers={'User-Agent': 'Mozilla/5.0'}
)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    runs = data.get('workflow_runs', [])
    for r in runs:
        print(f"Run #{r['id']}: name='{r['name']}', status={r['status']}, conclusion={r['conclusion']}, event={r['event']}, commit={r['head_sha'][:7]}", flush=True)
        print(f"  URL: {r['html_url']}", flush=True)
