/* Site-wide player and page navigation for Ramu Maharajapuram's website.
 *
 * 1. RP – one YouTube player for the whole site. On the Listen page it sits inside the page's
 *    player card ("docked"); on every other page it shows as a mini player so music keeps going.
 *    YouTube's rules: the player must stay visible and be at least 200×200 px, so the mini
 *    player is never smaller than that, and closing it stops playback.
 * 2. Navigation – links between pages swap only the page content (the player is never reloaded).
 *    Every page is still a normal full HTML page for search engines and direct visits.
 */
(function () {
  if (window.RP) return;
  const ROOT = new URL('.', document.currentScript.src).href;
  const ICON = {
    play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5.4v13.2a1.1 1.1 0 0 0 1.7.92l10.1-6.6a1.1 1.1 0 0 0 0-1.84L9.7 4.48A1.1 1.1 0 0 0 8 5.4z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="6.5" y="5" width="4" height="14" rx="1.2"/><rect x="13.5" y="5" width="4" height="14" rx="1.2"/></svg>',
    prev: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="5" width="2.6" height="14" rx="1"/><path d="M19 5.8v12.4a1 1 0 0 1-1.55.83L9.2 13.2a1.45 1.45 0 0 1 0-2.4l8.25-5.85A1 1 0 0 1 19 5.8z"/></svg>',
    next: '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="16.4" y="5" width="2.6" height="14" rx="1"/><path d="M5 5.8v12.4a1 1 0 0 0 1.55.83l8.25-5.83a1.45 1.45 0 0 0 0-2.4L6.55 4.97A1 1 0 0 0 5 5.8z"/></svg>',
    shuffle: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M17 3.5 21.5 8 17 12.5V9.5h-2.2c-1.1 0-2.1.5-2.8 1.4l-4.6 6.2c-1.1 1.4-2.8 2.3-4.6 2.3H1.5v-3h1.3c.9 0 1.7-.4 2.2-1.1l4.6-6.2C10.8 7.4 12.7 6.5 14.8 6.5H17V3.5zm0 8 4.5 4.5L17 20.5v-3h-2.2c-1.6 0-3.1-.6-4.2-1.6l1.9-2.5c.6.7 1.4 1.1 2.3 1.1H17v-3zM1.5 6.5h1.3c1.6 0 3.1.6 4.2 1.6L5.1 10.6c-.6-.7-1.4-1.1-2.3-1.1H1.5v-3z"/></svg>',
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12 19 6.4 17.6 5 12 10.6z"/></svg>'
  };

  /* ---------- player shell (lives outside <main>, never moved) ---------- */
  const shell = document.createElement('div');
  shell.id = 'rp';
  shell.hidden = true;
  shell.innerHTML =
    '<div id="rp-video"><div id="rp-yt"></div></div>' +
    '<div id="rp-am" hidden></div>' +
    '<div id="rp-bar">' +
    '  <a id="rp-info" href="' + ROOT + 'listen/"><span id="rp-title"></span><span id="rp-album"></span></a>' +
    '  <div id="rp-ctl">' +
    '    <button type="button" class="icon-btn" id="rp-shuffle" aria-pressed="false" aria-label="Shuffle" title="Shuffle">' + ICON.shuffle + '</button>' +
    '    <button type="button" class="icon-btn" id="rp-next" aria-label="Next song" title="Next song">' + ICON.next + '</button>' +
    '    <button type="button" class="icon-btn" id="rp-close" aria-label="Stop and close the player" title="Close">' + ICON.close + '</button>' +
    '  </div>' +
    '</div>';
  document.body.appendChild(shell);
  const $ = (id) => document.getElementById(id);

  let queue = [], idx = -1, shuffle = false, player = null, ready = false, pending = null, playing = false;
  // The mini player appears on other pages only once the visitor has actually played something.
  let started = false;
  let dockEl = null, raf = 0;
  let source = 'yt';
  const SOURCES = ['yt', 'apple', 'spotify', 'deezer'];
  try { const v = localStorage.getItem('rp-src'); source = SOURCES.includes(v) ? v : 'yt'; } catch (e) {}
  let amUrl = '';
  const listeners = { change: [], state: [] };
  const emit = (t) => listeners[t].forEach((f) => { try { f(); } catch (e) { console.error(e); } });

  function loadApi() {
    if (window.YT && window.YT.Player) return Promise.resolve();
    if (loadApi.p) return loadApi.p;
    loadApi.p = new Promise((res) => {
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = function () { if (prev) prev(); res(); };
      const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
    });
    return loadApi.p;
  }

  function ensurePlayer(videoId, autoplay, start) {
    if (player) {
      if (!ready) { pending = { videoId, autoplay, start }; return; }
      if (autoplay) player.loadVideoById({ videoId, startSeconds: start || 0 });
      else player.cueVideoById({ videoId, startSeconds: start || 0 });
      return;
    }
    pending = { videoId, autoplay, start };
    loadApi().then(() => {
      if (player) return;
      player = new YT.Player('rp-yt', {
        host: 'https://www.youtube-nocookie.com', width: '100%', height: '100%', videoId,
        playerVars: { playsinline: 1, rel: 0, modestbranding: 1, autoplay: autoplay ? 1 : 0, start: Math.floor(start || 0) },
        events: {
          onReady: () => {
            ready = true;
            if (pending && pending.videoId !== videoId) ensurePlayer(pending.videoId, pending.autoplay, pending.start);
            else if (pending && pending.autoplay) player.playVideo();
            pending = null;
          },
          onStateChange: (e) => {
            playing = e.data === YT.PlayerState.PLAYING;
            if (playing && !started) { started = true; save(); }
            if (e.data === YT.PlayerState.ENDED) next(); else { paint(); emit('state'); }
            if (playing) pauseOtherMedia();
          },
          onError: () => next()
        }
      });
    });
  }

  /* ---------- Apple Music (Apple's free embedded player) ----------
   * Everyone hears 30-second previews; Apple Music subscribers can sign in inside the player
   * for full songs. Websites can't start or stop it, so visitors press play in Apple's player
   * and there is no automatic next song. */
  // Embed address for a song on the chosen app, or '' if the song isn't on it.
  function embedFor(s, src) {
    const l = s && s.l; if (!l) return '';
    try {
      if (src === 'apple' && l.apple) {
        const x = new URL(l.apple); x.hostname = 'embed.music.apple.com'; x.searchParams.delete('uo'); return x.href;
      }
      if (src === 'spotify' && l.spotify) {
        const m = l.spotify.match(/open\.spotify\.com\/(track|album)\/([A-Za-z0-9]+)/);
        return m ? 'https://open.spotify.com/embed/' + m[1] + '/' + m[2] + '?utm_source=generator&theme=0' : '';
      }
      if (src === 'deezer' && l.deezer) {
        const m = l.deezer.match(/deezer\.com\/(?:[a-z]{2}\/)?(track|album)\/(\d+)/);
        return m ? 'https://widget.deezer.com/widget/dark/' + m[1] + '/' + m[2] + '?tracklist=false' : '';
      }
    } catch (e) {}
    return '';
  }
  function appleEmbed(s) { return embedFor(s, source); }
  function usingApple() { return source !== 'yt' && !!appleEmbed(current()); }
  function showApple(url) {
    const box = $('rp-am');
    if (url === amUrl && box.firstChild) return;
    amUrl = url;
    box.innerHTML = '';
    if (!url) return;
    const f = document.createElement('iframe');
    f.src = url;
    f.allow = 'autoplay *; encrypted-media *; fullscreen *; clipboard-write';
    f.setAttribute('sandbox', 'allow-forms allow-popups allow-same-origin allow-scripts allow-storage-access-by-user-activation allow-top-navigation-by-user-activation');
    const single = /[?&]i=|\/track\//.test(url);
    f.className = 'em-' + source + (single ? ' em-song' : ' em-album');
    f.title = { apple: 'Apple Music', spotify: 'Spotify', deezer: 'Deezer' }[source] + ' player';
    box.appendChild(f);
  }
  function applySource() {
    const apple = usingApple();
    shell.classList.toggle('am', apple);
    document.body.classList.toggle('rp-am', apple);
    $('rp-am').hidden = !apple;
    $('rp-video').hidden = apple;
    if (apple) { if (player && ready && playing) player.pauseVideo(); showApple(appleEmbed(current())); }
    else showApple('');
  }

  function current() { return idx >= 0 ? queue[idx] : null; }
  function show() { shell.hidden = !current() || (!dockEl && !started); layout(); }

  function paint() {
    const s = current();
    $('rp-title').textContent = s ? s.t : '';
    $('rp-album').textContent = s ? s.a : '';
    $('rp-shuffle').setAttribute('aria-pressed', String(shuffle));
    $('rp-info').href = ROOT + 'listen/' + (s ? '#v=' + s.id : '');
  }

  function setQueue(q, i) { queue = q.map((s) => ({ id: s.id, t: s.t, a: s.a, l: s.l })); idx = i; }

  function play(q, i) {
    started = true;
    if (q) setQueue(q, i); else if (i != null) idx = i;
    const s = current(); if (!s) return;
    if (source !== 'yt' && appleEmbed(s)) { applySource(); show(); paint(); save(); emit('change'); return; }
    ensurePlayer(s.id, true, 0); applySource(); show(); paint(); save(); emit('change');
  }
  function prepare(q, i, start) {
    setQueue(q, i);
    const s = current(); if (!s) return;
    if (source !== 'yt' && appleEmbed(s)) { applySource(); show(); paint(); save(); emit('change'); return; }
    ensurePlayer(s.id, false, start || 0); applySource(); show(); paint(); save(); emit('change');
  }
  function step(d) {
    if (!queue.length) return;
    if (shuffle && queue.length > 1) { let j; do { j = Math.floor(Math.random() * queue.length); } while (j === idx); idx = j; }
    else idx = (idx + d + queue.length) % queue.length;
    play(null, idx);
  }
  function next() { step(1); }
  function prev() { step(-1); }
  function toggle() {
    if (!current() || usingApple()) return;
    if (!player || !ready) { play(null, idx); return; }
    const st = player.getPlayerState();
    if (st === YT.PlayerState.PLAYING) player.pauseVideo();
    else if (st === YT.PlayerState.PAUSED || st === YT.PlayerState.CUED) player.playVideo();
    else play(null, idx);
  }
  function pause() { if (player && ready && playing) player.pauseVideo(); }
  function close() {
    if (player) { try { player.destroy(); } catch (e) {} }
    player = null; ready = false; playing = false; queue = []; idx = -1; started = false;
    const v = $('rp-video'); v.innerHTML = '<div id="rp-yt"></div>';
    showApple(''); shell.classList.remove('am'); $('rp-am').hidden = true; $('rp-video').hidden = false;
    try { sessionStorage.removeItem('rp'); } catch (e) {}
    show(); paint(); emit('change'); emit('state');
  }

  /* ---------- docked (Listen page) vs mini player ---------- */
  function layout() {
    const docked = !!dockEl;
    shell.classList.toggle('docked', docked);
    shell.classList.toggle('mini', !docked && !shell.hidden);
    document.body.classList.toggle('rp-mini', !docked && !shell.hidden);
    document.body.classList.toggle('rp-am', shell.classList.contains('am'));
    place();
  }
  function place() {
    raf = 0;
    const v = $('rp-video'), am = $('rp-am');
    if (!dockEl) { v.style.cssText = ''; am.style.cssText = ''; return; }
    const r = dockEl.getBoundingClientRect();
    const css = 'left:' + r.left + 'px;top:' + r.top + 'px;width:' + r.width + 'px;height:' + r.height + 'px';
    v.style.cssText = css; am.style.cssText = css;
  }
  const schedule = () => { if (dockEl && !raf) raf = requestAnimationFrame(place); };
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('resize', schedule);
  const ro = 'ResizeObserver' in window ? new ResizeObserver(schedule) : null;
  function dock(el) { dockEl = el; if (ro) ro.observe(el); show(); }
  function undock() { if (ro && dockEl) ro.unobserve(dockEl); dockEl = null; show(); }

  /* ---------- keep music and page videos from playing over each other ---------- */
  function pauseOtherMedia() { document.querySelectorAll('main video').forEach((v) => { if (!v.paused) v.pause(); }); }
  document.addEventListener('play', (e) => { if (e.target.tagName === 'VIDEO') pause(); }, true);

  /* ---------- remember the song across full page reloads (this tab only) ---------- */
  function save() {
    try {
      const t = player && ready && player.getCurrentTime ? player.getCurrentTime() : 0;
      if (current() && started) sessionStorage.setItem('rp', JSON.stringify({ queue, idx, shuffle, t }));
    } catch (e) {}
  }
  setInterval(() => { if (playing) save(); }, 5000);
  addEventListener('pagehide', save);

  $('rp-shuffle').addEventListener('click', () => { shuffle = !shuffle; save(); paint(); emit('change'); });
  $('rp-next').addEventListener('click', next);
  $('rp-close').addEventListener('click', close);

  /* ---------- navigation without reloading the player ---------- */
  let leaveFns = [];
  function onLeave(fn) { leaveFns.push(fn); }
  function runLeave() { const f = leaveFns; leaveFns = []; f.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } }); }

  function internal(a) {
    if (!a || a.target === '_blank' || a.hasAttribute('download')) return false;
    const u = new URL(a.href, location.href);
    if (u.origin !== location.origin || !u.href.startsWith(ROOT)) return false;
    if (!/\/$|\.html$/.test(u.pathname)) return false;
    if (u.pathname === location.pathname && u.search === location.search && u.hash) return false;
    return u;
  }

  document.addEventListener('click', (e) => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest('a[href]'); const u = internal(a);
    if (!u) return;
    if (!current() || !started) return; // nothing played yet: ordinary navigation is fine
    e.preventDefault();
    go(u.href, true);
  });

  addEventListener('popstate', () => { if (history.state && history.state.rp) go(location.href, false, history.state.y || 0); else location.reload(); });

  async function go(url, push, y) {
    let doc;
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      if (!res.ok) throw new Error(res.status);
      doc = new DOMParser().parseFromString(await res.text(), 'text/html');
      if (!doc.querySelector('main')) throw new Error('no main');
    } catch (err) { location.href = url; return; }

    runLeave();
    undock();
    if (push) {
      history.replaceState({ rp: true, y: scrollY }, '');
      history.pushState({ rp: true, y: 0 }, '', url);
    }
    document.title = doc.title;
    ['meta[name="description"]', 'link[rel="canonical"]'].forEach((sel) => {
      const n = doc.querySelector(sel), o = document.querySelector(sel);
      if (n && o) o.replaceWith(n.cloneNode(true));
    });
    doc.querySelectorAll('head link[rel="stylesheet"]').forEach((l) => {
      const href = new URL(l.getAttribute('href'), url).href.split('?')[0];
      const have = [...document.querySelectorAll('head link[rel="stylesheet"]')].some((x) => x.href.split('?')[0] === href);
      if (!have) document.head.appendChild(l.cloneNode(true));
    });

    [...document.body.children].forEach((n) => { if (n !== shell) n.remove(); });
    document.body.className = doc.body.className;
    const scripts = [];
    [...doc.body.children].forEach((n) => {
      if (n.tagName === 'SCRIPT') { scripts.push(n); return; }
      document.body.insertBefore(document.importNode(n, true), shell);
    });
    for (const s of scripts) await runScript(s, url);

    const hash = new URL(url).hash;
    const target = hash && hash.length > 1 && !hash.startsWith('#v=') ? document.getElementById(decodeURIComponent(hash.slice(1))) : null;
    if (target) target.scrollIntoView(); else scrollTo(0, y || 0);
    layout();
  }

  function runScript(old, base) {
    const src = old.getAttribute('src');
    const type = old.getAttribute('type');
    if (type && type !== 'text/javascript' && type !== 'module') return Promise.resolve();
    if (src && /(^|\/)app\.js(\?|$)/.test(src)) return Promise.resolve();
    return new Promise((res) => {
      const s = document.createElement('script');
      if (src) { s.src = new URL(src, base).href; s.onload = s.onerror = res; }
      else { s.textContent = '(function(){\n' + old.textContent + '\n})();'; }
      document.body.appendChild(s);
      if (!src) res();
    });
  }

  window.RP = {
    play, prepare, toggle, next, prev, pause, close, current, dock, undock, onLeave,
    isPlaying: () => playing && !usingApple(),
    getSource: () => source,
    usingApple,
    hasApple: (song) => !!appleEmbed(song),
    hasSource: (song, src) => !!embedFor(song, src),
    setSource: (v) => {
      source = SOURCES.includes(v) ? v : 'yt';
      try { localStorage.setItem('rp-src', source); } catch (e) {}
      if (current()) { if (!usingApple() && !player) ensurePlayer(current().id, false, 0); applySource(); }
      paint(); emit('change'); emit('state');
    },
    setShuffle: (v) => { shuffle = !!v; save(); paint(); },
    getShuffle: () => shuffle,
    queueIds: () => queue.map((s) => s.id),
    on: (t, fn) => { listeners[t].push(fn); return () => { listeners[t] = listeners[t].filter((f) => f !== fn); }; }
  };

  // Resume after a full reload (same tab): show the player paused where it left off.
  try {
    const saved = JSON.parse(sessionStorage.getItem('rp') || 'null');
    if (saved && saved.queue && saved.queue.length && !document.body.classList.contains('listen-page')) {
      shuffle = !!saved.shuffle; started = true;
      prepare(saved.queue, saved.idx, saved.t);
    } else if (saved && saved.queue && saved.queue.length) {
      shuffle = !!saved.shuffle; started = true; setQueue(saved.queue, saved.idx); window.RP._resumeAt = saved.t;
    }
  } catch (e) {}
  history.replaceState(Object.assign({}, history.state, { rp: true, y: scrollY }), '');
})();
