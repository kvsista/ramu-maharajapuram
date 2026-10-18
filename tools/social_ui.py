"""Shared pieces for showing Ramu's Instagram / Facebook posts (homepage strip and Watch page)."""


def player(card_selector):
    """The pop-up that plays an Instagram post with Instagram's own player, loaded only when a card is tapped."""
    return f'''    <dialog class="social-player" id="social-player" aria-label="Post">
      <div class="social-player-bar"><a id="social-open" target="_blank" rel="noopener">Open ↗</a><button type="button" id="social-close">Close</button></div>
      <div class="social-player-frame" id="social-frame"></div>
    </dialog>
    <script>
    (() => {{
      // Tapping an Instagram card opens Instagram's own player here; nothing loads from Instagram until then.
      const dlg = document.getElementById('social-player'), frame = document.getElementById('social-frame'), open = document.getElementById('social-open');
      if (!dlg.showModal) return;
      const shut = () => {{ frame.replaceChildren(); dlg.close(); }};
      document.querySelectorAll('{card_selector}[data-embed]').forEach((a) => a.addEventListener('click', (e) => {{
        e.preventDefault();
        if (window.RP) RP.pause();
        document.querySelectorAll('main video').forEach((v) => v.pause());
        const f = document.createElement('iframe');
        f.src = a.dataset.embed; f.title = a.dataset.where + ' post'; f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true;
        frame.replaceChildren(f); open.href = a.href; open.textContent = 'Open on ' + a.dataset.where + ' ↗';
        dlg.showModal();
      }}));
      document.getElementById('social-close').addEventListener('click', shut);
      dlg.addEventListener('click', (e) => {{ if (e.target === dlg) shut(); }});
      dlg.addEventListener('cancel', () => frame.replaceChildren());
    }})();
    </script>
'''
