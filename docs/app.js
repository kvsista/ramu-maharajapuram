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
    close: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.4 5 5 6.4 10.6 12 5 17.6 6.4 19 12 13.4 17.6 19 19 17.6 13.4 12 19 6.4 17.6 5 12 10.6z"/></svg>'
  };

  /* ---------- player shell (lives outside <main>, never moved) ---------- */
  const shell = document.createElement('div');
  shell.id = 'rp';
  shell.hidden = true;
  shell.innerHTML =
    '<div id="rp-video"><div id="rp-yt"></div></div>' +
    '<div id="rp-bar">' +
    '  <a id="rp-info" href="' + ROOT + 'listen/"><span id="rp-title"></span><span id="rp-album"></span></a>' +
    '  <div id="rp-ctl">' +
    '    <button type="button" class="ctl" id="rp-prev" aria-label="Previous song">' + ICON.prev + '</button>' +
    '    <button type="button" class="ctl main" id="rp-toggle" aria-label="Play">' + ICON.play + '</button>' +
    '    <button type="button" class="ctl" id="rp-next" aria-label="Next song">' + ICON.next + '</button>' +
    '    <button type="button" class="ctl" id="rp-close" aria-label="Stop and close the player">' + ICON.close + '</button>' +
    '  </div>' +
    '</div>';
  document.body.appendChild(shell);
  const $ = (id) => document.getElementById(id);

  let queue = [], idx = -1, shuffle = false, player = null, ready = false, pending = null, playing = false;
  let dockEl = null, raf = 0;
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
            if (e.data === YT.PlayerState.ENDED) next(); else { paint(); emit('state'); }
            if (playing) pauseOtherMedia();
          },
          onError: () => next()
        }
      });
    });
  }

  function current() { return idx >= 0 ? queue[idx] : null; }
  function show() { shell.hidden = !current(); layout(); }

  function paint() {
    const s = current();
    $('rp-title').textContent = s ? s.t : '';
    $('rp-album').textContent = s ? s.a : '';
    $('rp-toggle').innerHTML = playing ? ICON.pause : ICON.play;
    $('rp-toggle').setAttribute('aria-label', playing ? 'Pause' : 'Play');
    $('rp-info').href = ROOT + 'listen/' + (s ? '#v=' + s.id : '');
  }

  function setQueue(q, i) { queue = q.map((s) => ({ id: s.id, t: s.t, a: s.a, l: s.l })); idx = i; }

  function play(q, i) {
    if (q) setQueue(q, i); else if (i != null) idx = i;
    const s = current(); if (!s) return;
    ensurePlayer(s.id, true, 0); show(); paint(); save(); emit('change');
  }
  function prepare(q, i, start) {
    setQueue(q, i);
    const s = current(); if (!s) return;
    ensurePlayer(s.id, false, start || 0); show(); paint(); save(); emit('change');
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
    if (!current()) return;
    if (!player || !ready) { play(null, idx); return; }
    const st = player.getPlayerState();
    if (st === YT.PlayerState.PLAYING) player.pauseVideo();
    else if (st === YT.PlayerState.PAUSED || st === YT.PlayerState.CUED) player.playVideo();
    else play(null, idx);
  }
  function pause() { if (player && ready && playing) player.pauseVideo(); }
  function close() {
    if (player) { try { player.destroy(); } catch (e) {} }
    player = null; ready = false; playing = false; queue = []; idx = -1;
    const v = $('rp-video'); v.innerHTML = '<div id="rp-yt"></div>';
    try { sessionStorage.removeItem('rp'); } catch (e) {}
    show(); paint(); emit('change'); emit('state');
  }

  /* ---------- docked (Listen page) vs mini player ---------- */
  function layout() {
    const docked = !!dockEl;
    shell.classList.toggle('docked', docked);
    shell.classList.toggle('mini', !docked && !shell.hidden);
    document.body.classList.toggle('rp-mini', !docked && !shell.hidden);
    place();
  }
  function place() {
    raf = 0;
    const v = $('rp-video');
    if (!dockEl) { v.style.cssText = ''; return; }
    const r = dockEl.getBoundingClientRect();
    v.style.cssText = 'left:' + r.left + 'px;top:' + r.top + 'px;width:' + r.width + 'px;height:' + r.height + 'px';
  }
  const schedule = () => { if (dockEl && !raf) raf = requestAnimationFrame(place); };
  addEventListener('scroll', schedule, { passive: true });
  addEventListener('resize', schedule);
  const ro = 'ResizeObserver' in window ? new ResizeObserver(schedule) : null;
  function dock(el) { dockEl = el; if (ro) ro.observe(el); layout(); }
  function undock() { if (ro && dockEl) ro.unobserve(dockEl); dockEl = null; layout(); }

  /* ---------- keep music and page videos from playing over each other ---------- */
  function pauseOtherMedia() { document.querySelectorAll('main video').forEach((v) => { if (!v.paused) v.pause(); }); }
  document.addEventListener('play', (e) => { if (e.target.tagName === 'VIDEO') pause(); }, true);

  /* ---------- remember the song across full page reloads (this tab only) ---------- */
  function save() {
    try {
      const t = player && ready && player.getCurrentTime ? player.getCurrentTime() : 0;
      if (current()) sessionStorage.setItem('rp', JSON.stringify({ queue, idx, shuffle, t }));
    } catch (e) {}
  }
  setInterval(() => { if (playing) save(); }, 5000);
  addEventListener('pagehide', save);

  $('rp-toggle').addEventListener('click', toggle);
  $('rp-next').addEventListener('click', next);
  $('rp-prev').addEventListener('click', prev);
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
    if (!current()) return; // nothing playing: ordinary navigation is fine
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
    isPlaying: () => playing,
    setShuffle: (v) => { shuffle = !!v; save(); },
    getShuffle: () => shuffle,
    queueIds: () => queue.map((s) => s.id),
    on: (t, fn) => { listeners[t].push(fn); return () => { listeners[t] = listeners[t].filter((f) => f !== fn); }; }
  };

  // Resume after a full reload (same tab): show the player paused where it left off.
  try {
    const saved = JSON.parse(sessionStorage.getItem('rp') || 'null');
    if (saved && saved.queue && saved.queue.length && !document.body.classList.contains('listen-page')) {
      shuffle = !!saved.shuffle;
      prepare(saved.queue, saved.idx, saved.t);
    } else if (saved && saved.queue && saved.queue.length) {
      shuffle = !!saved.shuffle; setQueue(saved.queue, saved.idx); window.RP._resumeAt = saved.t;
    }
  } catch (e) {}
  history.replaceState(Object.assign({}, history.state, { rp: true, y: scrollY }), '');
})();
