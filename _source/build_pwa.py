import pathlib, sys

src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

def rep(s, old, new):
    if old not in s:
        raise SystemExit(f"pattern not found: {old[:60]!r}")
    return s.replace(old, new, 1)

s0 = src.replace("const IS_PWA = false;", "const IS_PWA = true;", 1)
assert s0 != src
src = s0
# 1. Storage: this device only (no claude.ai runtime outside artifacts)
s = rep(src,
"""    let db = null, id = null;
    try {
      if (window.claude?.use) {
        const [d, u] = await Promise.all([claude.use('db'), claude.use('user')]);
        db = d; id = u ? await u.id() : null;
      }
    } catch (e) { db = null; }
    if (db && id) { this.col = db.collection('data/users/' + id); S.mode = 'cloud'; this.subscribe(); }
    else { S.mode = 'local'; this.loadLocal(); }""",
"""    try { navigator.storage?.persist?.(); } catch (e) {}
    S.mode = 'local'; this.loadLocal();""")

# 2. Backup section instead of the account notice
s = rep(s,
"""  html += `<section class="card"><h2>Sauvegarde</h2><div class="small">${S.mode === 'cloud'
    ? 'Tes données sont enregistrées dans ton espace privé, lié à ton compte Claude. Elles se synchronisent entre ton PC et ton téléphone. Personne d’autre ne peut les lire.'
    : 'Tu n’es pas connecté : les données restent dans ce navigateur, sur cet appareil uniquement. Connecte-toi à claude.ai pour les synchroniser.'}</div></section>`;""",
"""  html += `<section class="card"><h2>Sauvegarde</h2>
    <div class="small">Tes données restent sur cet appareil, rien n’est envoyé sur Internet. Exporte une sauvegarde de temps en temps, et pour passer du téléphone au PC.</div>
    <div class="actions" style="display:flex;gap:8px;flex-wrap:wrap"><button class="btn" data-action="export">Exporter (.json)</button><label class="btn ghost" for="importFile" style="cursor:pointer">Importer</label></div>
    <input type="file" id="importFile" accept="application/json,.json" hidden>
    <div class="small muted" id="backupMsg">${esc(S.backupMsg || '')}</div></section>`;""")

# 3. Export / import handlers
s = rep(s,
"""    case 'wiz-finish': wizFinish(!!t.dataset.skip); break;
  }
});""",
"""    case 'wiz-finish': wizFinish(!!t.dataset.skip); break;
    case 'export': exportData(); break;
  }
});
function exportData() {
  S.settings.lastExport = todayStr(); Store.persistLocal();
  const blob = new Blob([JSON.stringify({ app: 'cap-epargne', version: 1, exported: new Date().toISOString(), settings: S.settings, months: S.months }, null, 2)], { type: 'application/json' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `cap-epargne-${todayStr()}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  S.backupMsg = 'Sauvegarde exportée.'; render();
}
document.addEventListener('change', async e => {
  if (e.target.id !== 'importFile' || !e.target.files[0]) return;
  try {
    const data = JSON.parse(await e.target.files[0].text());
    if (data.app !== 'cap-epargne' || !data.settings?.cats) throw new Error('format');
    S.settings = data.settings; S.months = data.months || {};
    Store.persistLocal(); applyRecurring();
    S.backupMsg = 'Sauvegarde importée : tes données ont été remplacées.';
  } catch (err) {
    S.backupMsg = 'Ce fichier n’est pas une sauvegarde Cap Épargne valide.';
  }
  render();
});""")

# 4. Full document head for a standalone PWA
head = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#1D7454">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Cap Épargne">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" type="image/png" sizes="192x192" href="icons/icon-192.png">
<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">
"""
s = rep(s, "<title>Cap Épargne</title>", head + "<title>Cap Épargne</title>")
s = rep(s, "</style>\n", """:root { padding-top: env(safe-area-inset-top, 0px); }
body { margin: 0; }
[hidden] { display: none !important; }
</style>
</head>
<body>
""")
s = rep(s, "Store.init();\n})();\n</script>", """Store.init();
if ('serviceWorker' in navigator) window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
})();
</script>
</body>
</html>""")

(out / "index.html").write_text(s, encoding="utf-8")

(out / "manifest.webmanifest").write_text("""{
  "name": "Cap Épargne",
  "short_name": "Cap Épargne",
  "description": "Dépenses, budgets et projets d'épargne voyage.",
  "lang": "fr",
  "start_url": "./",
  "scope": "./",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#F1F4F0",
  "theme_color": "#1D7454",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
""", encoding="utf-8")

(out / "sw.js").write_text("""// Cache the app shell so Cap Épargne opens offline. Bump VERSION on each release.
const VERSION = 'cap-epargne-v2';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icons/icon-192.png', './icons/icon-512.png', './icons/apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const url = new URL(e.request.url);
  // Pages: network first so updates show up, cache when offline
  if (e.request.mode === 'navigate') {
    e.respondWith(fetch(e.request).then(r => { const copy = r.clone(); caches.open(VERSION).then(c => c.put('./index.html', copy)); return r; }).catch(() => caches.match('./index.html')));
    return;
  }
  // Everything else (icons, Google Fonts): cache first
  if (url.origin === location.origin || url.host.endsWith('fonts.googleapis.com') || url.host.endsWith('fonts.gstatic.com')) {
    e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).then(r => {
      if (r.ok || r.type === 'opaque') { const copy = r.clone(); caches.open(VERSION).then(c => c.put(e.request, copy)); }
      return r;
    })));
  }
});
""", encoding="utf-8")
print("ok", len(s))
