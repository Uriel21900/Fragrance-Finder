import urllib.request
import json
import urllib.parse

queries = [
    'Althair', 
    'Torino21', 
    'Liquid Brun', 
    'Apple Brandy', 
    'MYSLF', 
    'Le Male Elixir', 
    'Stronger With You', 
    'Spectre Ghost', 
    'Khamrah', 
    'Aventus'
]

print("Testing production search endpoint https://fragrance-finder-alpha.vercel.app/api/search:")
for q in queries:
    url = f"https://fragrance-finder-alpha.vercel.app/api/search?q={urllib.parse.quote_plus(q)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            results = data if isinstance(data, list) else data.get('results', [])
            top = results[0] if results else None
            if top:
                print(f"  [+] '{q}' -> {top.get('brand_name')} - {top.get('canonical_name')} (is_dupe={top.get('is_dupe')})")
            else:
                print(f"  [-] '{q}' -> NOT FOUND")
    except Exception as e:
        print(f"  [!] '{q}' -> Error: {e}")
