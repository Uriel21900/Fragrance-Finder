import httpx

resp = httpx.get('https://fragrance-finder-alpha.vercel.app/api/trending', timeout=15)
print('Status code:', resp.status_code)
if resp.status_code == 200:
    data = resp.json()
    print(f'Total fragrances returned: {len(data)}')
    for f in data:
        name = f.get('canonical_name')
        brand = f.get('brand_name')
        prices = f.get('variants', [{}])[0].get('prices', [])
        print(f"\n[{brand}] {name} -> {len(prices)} prices")
        for p in prices[:5]:
            print(f"   [{p.get('retailer_name')}] ${p.get('price_amount')} -> {p.get('source_url')}")
else:
    print('Error:', resp.text)
