import urllib.request
import urllib.parse
import json

for q in ["Aventus", "Light Blue", "Acqua di Gio", "Eros"]:
    url = f"https://fragrance-finder-alpha.vercel.app/api/search?q={urllib.parse.quote(q)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"\nResults for '{q}': {len(data)}")
            for x in data[:4]:
                print(f" - {x.get('canonical_name')} | Gender: {x.get('gender')} | Image: {x.get('image_url')}")
    except Exception as e:
        print(f"Error fetching live API for '{q}': {e}")

