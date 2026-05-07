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

const BOOKS_PER_BATCH = 20;
let currentCity = null;
let renderedCount = 0;

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderBookItem(book, index) {
    const bookLangs = book.languages.map(langName).join(', ');
    const nativeTitle = book.title_native && book.title_native !== book.title
        ? `<div class="book-title-native">${escapeHtml(book.title_native)}</div>` : '';
    const olUrl = `https://openlibrary.org${book.key}`;

    let details = '';
    if (book.publishers && book.publishers.length) {
        details += `<div class="book-detail"><span class="detail-label">Publisher</span> ${escapeHtml(book.publishers.join(', '))}</div>`;
    }
    if (book.subjects && book.subjects.length) {
        details += `<div class="book-detail"><span class="detail-label">Subjects</span> ${escapeHtml(book.subjects.slice(0, 5).join(', '))}${book.subjects.length > 5 ? '…' : ''}</div>`;
    }
    if (book.number_of_pages) {
        details += `<div class="book-detail"><span class="detail-label">Pages</span> ${book.number_of_pages}</div>`;
    }
    if (book.description) {
        const desc = book.description.length > 200 ? book.description.slice(0, 200) + '…' : book.description;
        details += `<div class="book-detail book-description">${escapeHtml(desc)}</div>`;
    }
    details += `<div class="book-detail"><a href="${olUrl}" target="_blank" rel="noopener" onclick="event.stopPropagation()">View on Open Library →</a></div>`;

    return `<div class="book-item" onclick="toggleBookDetails(this)">
        <div class="book-header">
            <div>
                <div class="book-title">${escapeHtml(book.title)}</div>
                ${nativeTitle}
                <div class="book-lang">${bookLangs}${book.publish_date ? ' · ' + book.publish_date : ''}</div>
            </div>
            <span class="expand-icon">▸</span>
        </div>
        <div class="book-details">${details}</div>
    </div>`;
}

function toggleBookDetails(el) {
    el.classList.toggle('expanded');
}

function renderNextBatch() {
    if (!currentCity || renderedCount >= currentCity.books.length) return;
    const container = document.getElementById('book-list');
    const end = Math.min(renderedCount + BOOKS_PER_BATCH, currentCity.books.length);
    let html = '';
    for (let i = renderedCount; i < end; i++) {
        html += renderBookItem(currentCity.books[i], i);
    }
    container.insertAdjacentHTML('beforeend', html);
    renderedCount = end;
}

function onPreviewScroll(e) {
    const el = e.target;
    if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
        renderNextBatch();
    }
}

function showPreview(city) {
    const panel = document.getElementById('preview');
    currentCity = city;
    renderedCount = 0;
    const langs = [...new Set(city.books.flatMap(b => b.languages))].map(langName);
    let html = `
        <h2>${city.city_name}</h2>
        <div class="city-meta">${city.country_code} · Population: ${city.population.toLocaleString()}<br>
        Lat: ${city.latitude.toFixed(4)}, Lon: ${city.longitude.toFixed(4)}</div>
        <div class="book-count">${city.books.length} book${city.books.length > 1 ? 's' : ''} · Languages: ${langs.join(', ')}</div>
        <div id="book-list"></div>
    `;
    document.getElementById('preview-content').innerHTML = html;
    renderNextBatch();
    panel.classList.add('open');
    panel.removeEventListener('scroll', onPreviewScroll);
    panel.addEventListener('scroll', onPreviewScroll);
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
