# Nagarkatha

An interactive map showing cities mentioned in books written in Indian languages, sourced from [Open Library](https://openlibrary.org/).

**🌐 Live Demo**: [https://prabhakar267.github.io/nagarkatha/](https://prabhakar267.github.io/nagarkatha/)

## What is this?

A visualization of **1,651 books** across **22 Indian languages** that reference specific cities. Each marker on the map represents a city, sized by the number of books associated with it. Click a marker to see the full list of books.

**386 cities** · **2,057 book-city pairs** · **22 languages**

## How it was built

### 1. Data Source

[Open Library](https://openlibrary.org/) maintains a free, open catalog of every book ever published. They provide [monthly data dumps](https://openlibrary.org/developers/dumps) — the editions dump (~11 GB gzipped) contains metadata for 30M+ book editions including language, subjects, and `subject_places`.

### 2. Extraction Pipeline

```
Open Library Editions Dump (11 GB .gz)
        │
        ▼  [DuckDB query — filter by Indian languages + has subject_places]
        │
  21,073 books with place data (indian_books_with_places.jsonl)
        │
        ▼  [geonamescache — classify places as city vs state/country/region]
        │
  1,651 books with city-level places (indian_books_with_cities.jsonl)
        │
        ▼  [Aggregate by city, enrich with lat/lon/population]
        │
  386 cities (data/cities_for_map.json) → Map visualization
```

**Key decisions:**
- Used [DuckDB](https://duckdb.org/) to query the gzipped dump directly (no decompression needed, handles 20MB+ lines)
- Used [geonamescache](https://pypi.org/project/geonamescache/) (32,444 world cities) to distinguish cities from countries/states/regions
- Filtered to only books where `subject_places` matches a known city name

### 3. Languages Covered

Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Odia, Sanskrit, Assamese, Kashmiri, Sindhi, Nepali, Konkani, Maithili, Santali, Dogri, Manipuri, Bodo

### 4. Map Visualization

Static single-page app using [Leaflet.js](https://leafletjs.com/) with marker clustering. Hosted on GitHub Pages — no backend required.

## Project Structure

```
├── index.html                  # Map visualization (GitHub Pages entry point)
├── data/
│   └── cities_for_map.json     # Aggregated city data with book lists
├── scripts/
│   ├── fetch_books.py          # (Alt) Fetch via Open Library API with resume support
│   ├── extract_indian_books.py # Extract Indian-language books from dump using DuckDB
│   └── filter_cities.py        # Filter to city-level places using geonamescache
├── docs/
│   └── preview.png             # Screenshot for README
└── README.md
```

## Reproducing the Data

### Prerequisites

```bash
python3 -m venv venv
source venv/bin/activate
pip install duckdb geonamescache
```

### Steps

```bash
# 1. Download the Open Library editions dump (~11 GB)
mkdir -p dumps
curl -L -o dumps/ol_dump_editions_latest.txt.gz \
  "https://openlibrary.org/data/ol_dump_editions_latest.txt.gz"

# 2. Extract Indian-language books with places
python3 scripts/extract_indian_books.py

# 3. Filter to city-level places only
python3 scripts/filter_cities.py

# 4. Serve locally
python3 -m http.server 8000
# Open http://localhost:8000
```

## Limitations

- **Place coverage is partial** — only ~21k of the ~300k Indian-language books in Open Library have `subject_places` metadata
- **City matching is name-based** — ambiguous names (e.g., "Hyderabad" exists in both India and Pakistan) resolve to the largest city by population
- **False positives** — some entries like "Goa (State)" or "Asia" match city names in geonamescache; these are included but rare
- **No full-text analysis** — places are from catalog metadata only, not extracted from book content

## Tech Stack

- **Data processing**: Python, DuckDB, geonamescache
- **Visualization**: Leaflet.js, Leaflet.markercluster
- **Hosting**: GitHub Pages
- **Data source**: Open Library bulk data dumps

## License

MIT
