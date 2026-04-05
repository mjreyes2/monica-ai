import urllib.request, json

places = ['england', 'london england', 'london, england', 'london', 'cairo egypt', 'cairo', 'south africa']
for p in places:
    encoded = urllib.request.quote(p)
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded}&count=1&language=en"
    req = urllib.request.Request(url, headers={"User-Agent": "Monica-AI/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        results = data.get("results", [])
        if results:
            r = results[0]
            print(f"'{p}' -> {r['name']} ({r['latitude']}, {r['longitude']}) country={r.get('country','?')}")
        else:
            print(f"'{p}' -> NOT FOUND")
    except Exception as e:
        print(f"'{p}' -> ERROR: {e}")
