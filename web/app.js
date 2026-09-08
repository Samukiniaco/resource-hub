// Web Resource Hub — lê o MESMO catalog.json (editor continua funcionando, sem conversão)
const CATALOG_URLS = [
  "../data/catalog.json", // quando servido da raiz via python -m http.server
  "data/catalog.json",
  "https://raw.githubusercontent.com/Samukiniaco/resource-hub/master/data/catalog.json",
];
let catalog = null;

const $ = (s) => document.querySelector(s);

async function loadCatalog() {
  for (const u of CATALOG_URLS) {
    try {
      const r = await fetch(u, { cache: "no-store" });
      if (!r.ok) continue;
      const j = await r.json();
      if (j.schema_version !== 1) continue;
      catalog = j;
      $("#status-text").textContent = `Catálogo v${j.app.catalog_version} carregado`;
      return j;
    } catch (e) { /* tenta próxima */ }
  }
  $("#status-text").textContent = "Offline — sem catálogo";
  return null;
}

function card({ title, desc, link, banner, warning }) {
  const d = document.createElement("div");
  d.className = "card";
  const img = banner && /^https?:\/\//.test(banner) ? `<img loading="lazy" src="${banner}" onerror="this.remove()">` : "";
  d.innerHTML = `<h3>● ${escapeHtml(title)}</h3><p>${escapeHtml(desc || "Sem descrição.")}</p>${img}${
    warning ? `<div class="warn">⚠ ${escapeHtml(warning)}</div>` : ""
  }<div class="row"><button class="btn" data-open="${escapeAttr(link)}">Abrir ↗</button>
  <button class="btn" data-copy="${escapeAttr(link)}">Copiar link</button>
  <span class="mono">${escapeHtml((link || "sem link").slice(0, 52))}</span></div>`;
  d.querySelector("[data-open]").onclick = (e) => { const u = e.target.dataset.open; if (/^https?:\/\//.test(u)) window.open(u, "_blank", "noopener"); };
  d.querySelector("[data-copy]").onclick = async (e) => { try { await navigator.clipboard.writeText(e.target.dataset.copy); e.target.textContent = "✓ Copiado!"; setTimeout(() => (e.target.textContent = "Copiar link"), 1400); } catch {} };
  return d;
}
function escapeHtml(s) { return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }
function escapeAttr(s) { return escapeHtml(s).replace(/"/g, "&quot;"); }

function versionKey(s) {
  return String(s).toLowerCase().split(/[.\-_\s]+/).map((p) => (/^\d+$/.test(p) ? String(p).padStart(6, "0") : p)).join(".");
}

function renderMinecraft() {
  const list = $("#mc-list"); list.innerHTML = "";
  const q = ($("#mc-search").value || "").toLowerCase();
  const idf = $("#mc-id").value;
  const sort = $("#mc-sort").value;
  let items = (catalog?.minecraft?.versions || []).filter((v) => {
    if (idf !== "Todos" && v.id !== idf) return false;
    if (q && !(v.name + " " + v.description + " " + v.id).toLowerCase().includes(q)) return false;
    return true;
  });
  if (sort === "A-Z (nome)") items.sort((a, b) => a.name.localeCompare(b.name));
  else if (sort === "Z-A (nome)") items.sort((a, b) => b.name.localeCompare(a.name));
  else if (sort === "Versão ↓") items.sort((a, b) => (versionKey(a.id) < versionKey(b.id) ? 1 : -1));
  else if (sort === "Versão ↑") items.sort((a, b) => (versionKey(a.id) > versionKey(b.id) ? 1 : -1));
  if (!items.length) list.innerHTML = `<div class="card">Nenhum resultado.</div>`;
  items.forEach((v) => list.appendChild(card({ title: v.name, desc: v.description, link: v.link, banner: v.banner, warning: v.warning })));
}

function renderSimple(el, items, map) {
  const list = $(el); list.innerHTML = "";
  if (!items.length) list.innerHTML = `<div class="card">Nada por aqui.</div>`;
  items.forEach((x) => list.appendChild(card(map(x))));
}

async function renderHistory() {
  const box = $("#history"); box.innerHTML = "Carregando…";
  try {
    const r = await fetch("https://api.github.com/repos/Samukiniaco/resource-hub/commits?path=data/catalog.json&per_page=20");
    if (!r.ok) throw new Error("API " + r.status);
    const commits = await r.json();
    box.innerHTML = "";
    for (const c of commits.slice(0, 10)) {
      const sha = c.sha, short = sha.slice(0, 7);
      const date = (c.commit?.committer?.date || "").slice(0, 10);
      const msg = (c.commit?.message || "").split("\n")[0];
      let ver = "?", changelog = msg;
      try {
        const raw = await (await fetch(`https://raw.githubusercontent.com/Samukiniaco/resource-hub/${sha}/data/catalog.json`, { cache: "force-cache" })).json();
        ver = raw.app?.catalog_version || "?"; changelog = raw.app?.changelog || msg;
      } catch {}
      const det = document.createElement("details");
      det.className = "hist";
      det.innerHTML = `<summary>v${escapeHtml(ver)} <span class="meta">· ${date} · ${short}</span><br><span class="meta">${escapeHtml(msg)}</span></summary>
        <pre>${escapeHtml(changelog)}</pre>
        <div class="row"><a class="btn" href="https://raw.githubusercontent.com/Samukiniaco/resource-hub/${sha}/data/catalog.json" target="_blank" rel="noopener">Abrir Raw</a>
        <a class="btn" href="https://github.com/Samukiniaco/resource-hub/commit/${sha}" target="_blank" rel="noopener">Commit</a></div>`;
      box.appendChild(det);
    }
  } catch (e) {
    box.innerHTML = `Offline — <a href="https://github.com/Samukiniaco/resource-hub/commits/master/data/catalog.json" target="_blank" rel="noopener">ver commits no GitHub</a>`;
  }
}

async function init() {
  document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => {
    document.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    document.querySelector("#tab-" + b.dataset.tab).classList.add("active");
  }));
  $("#btn-url").onclick = () => window.open("https://raw.githubusercontent.com/Samukiniaco/resource-hub/master/data/catalog.json", "_blank", "noopener");
  $("#btn-refresh").onclick = () => location.reload();
  await loadCatalog();
  if (!catalog) return;
  $("#cat-version").textContent = catalog.app.catalog_version;
  $("#cat-stats").textContent = `${catalog.minecraft.versions.length} MC · ${catalog.java.length} Java · ${catalog.other.length} outros`;
  $("#changelog").textContent = catalog.app.changelog || "—";
  const url = "https://raw.githubusercontent.com/Samukiniaco/resource-hub/master/data/catalog.json";
  const a = $("#cat-url"); a.href = url; a.textContent = url;
  const ids = [...new Set(catalog.minecraft.versions.map((v) => v.id))].sort();
  ids.forEach((id) => { const o = document.createElement("option"); o.textContent = id; $("#mc-id").appendChild(o); });
  ["mc-search", "mc-id", "mc-sort"].forEach((id) => document.querySelector("#" + id).addEventListener("input", renderMinecraft));
  renderMinecraft();
  renderSimple("#libs-list", [catalog.libraries].filter(Boolean), (l) => ({ title: l.name, desc: l.description, link: l.link || l.url, banner: l.banner, warning: l.warning }));
  renderSimple("#java-list", catalog.java, (j) => ({ title: j.name, desc: j.description || j.version, link: j.link }));
  renderSimple("#other-list", catalog.other, (o) => ({ title: o.category && o.category !== "other" ? `${o.name} · ${o.category}` : o.name, desc: o.description, link: o.link, banner: o.banner, warning: o.warning }));
  renderHistory();
}
init();
