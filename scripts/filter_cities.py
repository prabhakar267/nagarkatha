"""
Filter indian_books_with_places.jsonl to only books with city-level places.
Enriches each place with geonamescache metadata (lat, lon, population, country).
Prefers South Asian matches for Indian-language books.
Output: indian_books_with_cities.jsonl
"""

import json
import geonamescache
from pathlib import Path

INPUT = Path(__file__).parent.parent / "data" / "indian_books_with_places.jsonl"
OUTPUT = Path(__file__).parent.parent / "data" / "indian_books_with_cities.jsonl"

gc = geonamescache.GeonamesCache()

SOUTH_ASIAN_COUNTRIES = {'IN', 'PK', 'BD', 'NP', 'LK', 'BT', 'MV', 'AF'}

# Places that are countries, continents, or regions — not cities
BLOCKLIST = {
    'Asia', 'Europe', 'Africa', 'India', 'World', 'South Asia',
    'Palestine', 'Mexico', 'Jordan', 'Colombia', 'Armenia', 'Liberia',
    'Iran', 'Iraq', 'Egypt', 'China', 'Japan', 'Korea', 'Brazil',
    'Canada', 'Australia', 'Germany', 'France', 'Italy', 'Spain',
    'Russia', 'Turkey', 'Pakistan', 'Bangladesh', 'Nepal', 'Sri Lanka',
    'Afghanistan', 'England', 'Scotland', 'Wales', 'United States',
}

# Manual overrides for Indian places missing or mismatched in geonamescache
MANUAL_OVERRIDES = {
    'Goa': {'city_name': 'Goa', 'latitude': 15.4909, 'longitude': 73.8278, 'population': 1458545, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Kullu': {'city_name': 'Kullu', 'latitude': 31.9579, 'longitude': 77.1096, 'population': 18306, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Kulu': {'city_name': 'Kullu', 'latitude': 31.9579, 'longitude': 77.1096, 'population': 18306, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Konark': {'city_name': 'Konark', 'latitude': 19.8876, 'longitude': 86.0946, 'population': 15752, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Konārak': {'city_name': 'Konark', 'latitude': 19.8876, 'longitude': 86.0946, 'population': 15752, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Saran': {'city_name': 'Saran', 'latitude': 25.85, 'longitude': 84.75, 'population': 3951873, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Salt': {'city_name': 'Salt', 'latitude': 29.6077, 'longitude': 79.5210, 'population': 9000, 'countrycode': 'IN', 'timezone': 'Asia/Kolkata'},
    'Bali': {'city_name': 'Bali', 'latitude': -8.4095, 'longitude': 115.1889, 'population': 4225000, 'countrycode': 'ID', 'timezone': 'Asia/Makassar'},
    'Victoria': {'city_name': 'Melbourne', 'latitude': -37.8136, 'longitude': 144.9631, 'population': 4936349, 'countrycode': 'AU', 'timezone': 'Australia/Melbourne'},
}

# Build lookup: city name -> list of city info dicts
city_lookup = {}
for c in gc.get_cities().values():
    name = c["name"]
    if name not in city_lookup:
        city_lookup[name] = []
    city_lookup[name].append(c)


def resolve_city(place):
    """Try to match a place string to a city. Returns city info dict or None."""
    clean = place.split("(")[0].strip()

    # Check blocklist
    if clean in BLOCKLIST or place in BLOCKLIST:
        return None

    # Check manual overrides first
    if place in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[place]
    if clean in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[clean]

    # Try exact match then cleaned match
    candidates = city_lookup.get(place, []) or city_lookup.get(clean, [])
    if not candidates:
        return None

    # Prefer South Asian match
    south_asian = [c for c in candidates if c['countrycode'] in SOUTH_ASIAN_COUNTRIES]
    if south_asian:
        return max(south_asian, key=lambda c: c['population'])

    # Fall back to largest by population
    return max(candidates, key=lambda c: c['population'])


count = 0
with open(INPUT) as fin, open(OUTPUT, "w") as fout:
    for line in fin:
        book = json.loads(line)
        city_places = []
        for p in book.get("subject_places", []):
            city = resolve_city(p)
            if city:
                city_places.append({
                    "original_value": p,
                    "city_name": city.get("city_name", city.get("name", "")),
                    "latitude": city["latitude"],
                    "longitude": city["longitude"],
                    "population": city["population"],
                    "country_code": city["countrycode"],
                    "timezone": city["timezone"],
                })
        if city_places:
            book["city_places"] = city_places
            book["subject_places"] = [cp["original_value"] for cp in city_places]
            fout.write(json.dumps(book, ensure_ascii=False) + "\n")
            count += 1

print(f"✓ {count} books with city-level places saved to {OUTPUT}")
