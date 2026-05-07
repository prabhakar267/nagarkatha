const LANG_NAMES = {
    '/languages/hin': 'Hindi', '/languages/tam': 'Tamil', '/languages/tel': 'Telugu',
    '/languages/ben': 'Bengali', '/languages/mar': 'Marathi', '/languages/guj': 'Gujarati',
    '/languages/kan': 'Kannada', '/languages/mal': 'Malayalam', '/languages/pan': 'Punjabi',
    '/languages/urd': 'Urdu', '/languages/ori': 'Odia', '/languages/san': 'Sanskrit',
    '/languages/asm': 'Assamese', '/languages/kas': 'Kashmiri', '/languages/sin': 'Sindhi',
    '/languages/nep': 'Nepali', '/languages/kon': 'Konkani', '/languages/mai': 'Maithili',
    '/languages/sat': 'Santali', '/languages/doi': 'Dogri', '/languages/mni': 'Manipuri',
    '/languages/bod': 'Bodo', '/languages/per': 'Persian', '/languages/ara': 'Arabic',
    '/languages/eng': 'English',
};

function langName(key) {
    return LANG_NAMES[key] || key.replace('/languages/', '');
}

let map, markers, citiesData = [];

async function init() {
    map = L.map('map', { worldCopyJump: true, zoomControl: true }).setView([22, 78], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);

    markers = L.markerClusterGroup({
        chunkedLoading: true,
        maxClusterRadius: 50,
        showCoverageOnHover: false,
        zoomToBoundsOnClick: true,
        iconCreateFunction: (cluster) => {
            const count = cluster.getChildCount();
            let dim = 36;
            if (count > 20) { dim = 50; }
            else if (count > 5) { dim = 42; }
            return L.divIcon({
                html: `<div style="background:rgba(230,126,34,0.85);color:#fff;border-radius:50%;width:${dim}px;height:${dim}px;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:13px;box-shadow:0 2px 8px rgba(0,0,0,0.3);">${count}</div>`,
                className: '',
                iconSize: [dim, dim]
            });
        }
    });

    const resp = await fetch('data/cities_for_map.json');
    citiesData = await resp.json();
    createMarkers();
    updateStats();
    map.addLayer(markers);
    map.on('click', closePreview);
}

function createMarkers() {
    citiesData.forEach(city => {
        const bookCount = city.books.length;
        const radius = Math.min(6 + Math.log2(bookCount + 1) * 3, 16);
        const marker = L.circleMarker([city.latitude, city.longitude], {
            radius: radius,
            fillColor: '#e67e22',
            color: '#d35400',
            weight: 2,
            opacity: 1,
            fillOpacity: 0.8
        });
        marker.cityData = city;
        marker.bindPopup(`
            <div class="popup-title">${city.city_name}</div>
            <div class="popup-meta">${city.country_code} · Pop: ${city.population.toLocaleString()}<br>${bookCount} book${bookCount > 1 ? 's' : ''}</div>
        `, { closeButton: false, offset: [0, -5] });
        marker.on('mouseover', () => marker.openPopup());
        marker.on('mouseout', () => setTimeout(() => marker.closePopup(), 300));
        marker.on('click', (e) => {
            L.DomEvent.stopPropagation(e);
            showPreview(city);
        });
        markers.addLayer(marker);
    });
}

function showPreview(city) {
    const panel = document.getElementById('preview');
    const langs = [...new Set(city.books.flatMap(b => b.languages))].map(langName);
    let html = `
        <h2>${city.city_name}</h2>
        <div class="city-meta">${city.country_code} · Population: ${city.population.toLocaleString()}<br>
        Lat: ${city.latitude.toFixed(4)}, Lon: ${city.longitude.toFixed(4)}</div>
        <div class="book-count">${city.books.length} book${city.books.length > 1 ? 's' : ''} · Languages: ${langs.join(', ')}</div>
    `;
    city.books.forEach(book => {
        const bookLangs = book.languages.map(langName).join(', ');
        html += `<div class="book-item">
            <div class="book-title">${book.title}</div>
            <div class="book-lang">${bookLangs}${book.publish_date ? ' · ' + book.publish_date : ''}</div>
        </div>`;
    });
    document.getElementById('preview-content').innerHTML = html;
    panel.classList.add('open');
}

function closePreview() {
    document.getElementById('preview').classList.remove('open');
}

function updateStats() {
    const allBooks = citiesData.reduce((sum, c) => sum + c.books.length, 0);
    const allLangs = new Set(citiesData.flatMap(c => c.books.flatMap(b => b.languages)));
    document.getElementById('stat-cities').textContent = citiesData.length;
    document.getElementById('stat-books').textContent = allBooks.toLocaleString();
    document.getElementById('stat-langs').textContent = allLangs.size;
}

init();
