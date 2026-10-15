/* News from the family's Google Sheet (published to the web as CSV).
 * Only rows whose "Show" column says Yes appear. The weekly job also writes the same items
 * into the page HTML for search engines; this script refreshes them live between runs.
 * Containers: <div data-news="latest"> (homepage) and <div data-news="upcoming"> (Invite page).
 */
(function () {
  const CSV_URL = window.RAMU_NEWS_CSV || '';
  const boxes = document.querySelectorAll('[data-news]');
  if (!CSV_URL || !boxes.length) return;

  function parseCSV(text) {
    const rows = []; let row = [], cell = '', q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; }
        else if (c === '"') q = false;
        else cell += c;
      } else if (c === '"') q = true;
      else if (c === ',') { row.push(cell); cell = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); rows.push(row); row = []; cell = '';
      } else cell += c;
    }
    if (cell || row.length) { row.push(cell); rows.push(row); }
    return rows;
  }

  function items(rows) {
    const h = (rows.shift() || []).map(s => s.trim().toLowerCase());
    const col = (...names) => h.findIndex(x => names.some(n => x.startsWith(n)));
    const C = { type: col('what is it', 'type'), title: col('title'), date: col('date'), venue: col('city', 'venue'),
                details: col('details'), link: col('link'), photo: col('photo'), show: col('show') };
    return rows.map(r => ({
      type: (r[C.type] || '').trim(), title: (r[C.title] || '').trim(), date: (r[C.date] || '').trim(),
      venue: (r[C.venue] || '').trim(), details: (r[C.details] || '').trim(), link: (r[C.link] || '').trim(), photo: C.photo >= 0 ? (r[C.photo] || '').trim() : '',
      show: /^y(es)?$/i.test((r[C.show] || '').trim())
    })).filter(x => x.show && x.title && /^\d{4}-\d{2}-\d{2}$/.test(x.date));
  }

  const today = new Date().toISOString().slice(0, 10);
  const fmt = d => new Date(d + 'T12:00:00').toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
  const ytId = u => (u.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/shorts\/)([\w-]{11})/) || [])[1];
  const safe = u => /^https?:\/\//i.test(u) ? u : '';

  function card(x) {
    const el = document.createElement('article');
    el.className = 'news-card';
    const upcoming = x.date >= today && /concert/i.test(x.type);
    const meta = document.createElement('p'); meta.className = 'news-meta';
    meta.textContent = [upcoming ? 'Upcoming' : x.type, fmt(x.date), x.venue].filter(Boolean).join(' · ');
    const t = document.createElement('h3'); t.textContent = x.title;
    el.append(meta, t);
    if (x.details) { const p = document.createElement('p'); p.className = 'news-details'; p.textContent = x.details; el.append(p); }
    const link = safe(x.link), id = link && ytId(link);
    const photo = safe(x.photo);
    if (photo && !id) {
      const img = document.createElement('img'); img.className = 'news-photo'; img.loading = 'lazy';
      img.src = photo; img.alt = x.title; el.append(img);
    }
    if (id) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'news-video';
      b.style.backgroundImage = `url(https://i.ytimg.com/vi/${id}/hqdefault.jpg)`;
      b.setAttribute('aria-label', 'Play video: ' + x.title);
      b.innerHTML = '<span class="big-play"></span>';
      b.addEventListener('click', () => {
        const f = document.createElement('iframe');
        f.src = `https://www.youtube-nocookie.com/embed/${id}?autoplay=1&rel=0`;
        f.allow = 'autoplay; encrypted-media; picture-in-picture'; f.allowFullscreen = true; f.title = x.title;
        f.className = 'news-frame'; b.replaceWith(f);
      });
      el.append(b);
    } else if (link) {
      const a = document.createElement('a'); a.href = link; a.target = '_blank'; a.rel = 'noopener'; a.className = 'news-link';
      a.textContent = /facebook\.com|fb\.watch/i.test(link) ? 'View on Facebook ↗' : 'More details ↗';
      el.append(a);
    }
    return el;
  }

  fetch(CSV_URL, { cache: 'no-store' }).then(r => r.ok ? r.text() : Promise.reject()).then(text => {
    const all = items(parseCSV(text)).sort((a, b) => b.date.localeCompare(a.date));
    boxes.forEach(box => {
      const kind = box.dataset.news;
      const list = kind === 'upcoming'
        ? all.filter(x => /concert/i.test(x.type) && x.date >= today).sort((a, b) => a.date.localeCompare(b.date))
        : all.slice(0, 6);
      const section = box.closest('section');
      box.replaceChildren(...list.map(card));
      if (section) section.hidden = list.length === 0;
    });
  }).catch(() => { /* keep whatever the weekly job baked into the page */ });
})();
