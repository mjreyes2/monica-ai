import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test the _clean_place_name and _KNOWN_LOCATIONS
from services.ai_service import AIService

# Test clean_place_name
tests = [
    'aerial view of the of south africa',
    'the location of cairo',
    'cairo egypt',
    'london england',
    'london, england',
    'south africa',
    'england',
]
print("=== Clean Place Name ===")
for t in tests:
    print(f"  '{t}' -> '{AIService._clean_place_name(t)}'")

print("\n=== Known Locations ===")
for name in ['england', 'south africa', 'france', 'florida', 'new york']:
    if name in AIService._KNOWN_LOCATIONS:
        lat, lng, n, c = AIService._KNOWN_LOCATIONS[name]
        print(f"  '{name}' -> {n} ({lat}, {lng}) [{c}]")
    else:
        print(f"  '{name}' -> NOT IN LOOKUP")
