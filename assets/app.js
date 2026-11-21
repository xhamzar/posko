
"use strict";
/* ============ POSKO SPA — bicara ke /api/* (JSON). Kalau API belum live,
   otomatis jatuh ke MODE DEMO dengan data contoh biar tampilan bisa diintip. */
const API = "/api";
const store = {
  unread: 0,
  get token(){ return localStorage.getItem("posko_token") || ""; },
  set token(v){ v ? localStorage.setItem("posko_token", v) : localStorage.removeItem("posko_token"); },
  get me(){ try { return JSON.parse(localStorage.getItem("posko_me") || "null"); } catch(e){ return null; } },
  set me(v){ v ? localStorage.setItem("posko_me", JSON.stringify(v)) : localStorage.removeItem("posko_me"); }
};
let DEMO = false;

/* ---------- data demo ---------- */
const demoDB = {
  favs: [],
  nodeFavs: [],
  nodes: [
    {id:"umum", name:"Umum", desc:"Obrolan segala rupa"},
    {id:"teknologi", name:"Teknologi", desc:"Gadget, software, internet"},
    {id:"santai", name:"Santai", desc:"Ngobrol ringan penghilang penat"},
    {id:"tanya", name:"Tanya Jawab", desc:"Bertanya apa saja, warga menjawab"}
  ],
  users: [
    {username:"driyan", joined:"2026-10-22", role:"admin", coins:120, bio:"Penjaga pos utama. Senggol dong.", avatar:"kucing"},
    {username:"warga01", joined:"2026-10-22", role:"member", coins:45, bio:"Warga baru, masih malu-malu.", avatar:"kodok"}
  ],
  coinTx: [
    {from:null, to:"driyan", amount:20, type:"welcome", note:"Bonus warga baru", created:"2026-10-22T13:00:00Z"},
    {from:"warga01", to:"driyan", amount:5, type:"tip", note:"", created:"2026-10-22T13:05:00Z"}
  ],
  topics: [
    {id:"t1", node:"umum", author:"driyan", title:"Selamat datang di POSKO! Perkenalan dulu yuk",
     content:"Halo warga POSKO! Forum ini baru dibuka. Silakan perkenalan di balasan: nama, asal, dan lagi suka ngulik apa.",
     created:"2026-10-22T13:00:00Z", last:"2026-10-22T13:05:00Z", pinned:true, locked:false, replies:0, views:128},
    {id:"t2", node:"teknologi", author:"warga01", title:"Ada yang masih pakai PHP 5.4 di 2026? Ternyata masih ada yang nambal CVE-nya",
     content:"Baru baca thread soal backport patch CVE buat PHP 5.4. Legacy emang nggak ada matinya.",
     created:"2026-10-22T13:02:00Z", last:"2026-10-22T13:04:00Z", pinned:false, locked:false, replies:0, views:57}
  ],
  replies: [
    {id:"r1", topic:"t1", author:"warga01", content:"Hadir! Warga pertama check-in. Lagi suka ngulik emulator browser.", created:"2026-10-22T13:05:00Z"},
    {id:"r2", topic:"t2", author:"driyan", content:"Yang penting backup dulu sebelum nimpa install. Pelajaran klasik.", created:"2026-10-22T13:04:00Z"}
  ]
};

/* ---------- helper API ---------- */
/* Indikator loading global: bar hijau tipis di paling atas layar, nyala selama
   ada panggilan API berjalan (jeda tampil 120ms biar nggak kedip buat yang cepat). */
let _apiInFlight = 0, _lbTimer = null;
function loadStart() {
  _apiInFlight++;
  if (_apiInFlight === 1) {
    clearTimeout(_lbTimer);
    _lbTimer = setTimeout(() => { const b = document.getElementById("loadbar"); if (b) b.classList.add("on"); }, 120);
  }
}
function loadEnd() {
  _apiInFlight = Math.max(0, _apiInFlight - 1);
  if (_apiInFlight === 0) {
    clearTimeout(_lbTimer);
    const b = document.getElementById("loadbar");
    if (b) b.classList.remove("on");
  }
}
async function api(path, opts = {}) {
  loadStart();
  try {
    const headers = {"Content-Type":"application/json"};
    if (store.token) headers["Authorization"] = "Bearer " + store.token;
    const res = await fetch(API + path, {method: opts.method || "GET", headers,
      body: opts.body ? JSON.stringify(opts.body) : undefined});
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.error || ("HTTP " + res.status)); }
    return res.json();
  } finally { loadEnd(); }
}
async function apiOrDemo(path, demoFn) {
  if (DEMO) return demoFn();
  try { return await api(path); }
  catch (e) { DEMO = true; document.getElementById("demo-badge").style.display = "inline-block"; return demoFn(); }
}

/* ---------- helper tampilan ---------- */
const $view = document.getElementById("view");
const $side = document.getElementById("side");
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const STICKER_CDN = "https://cdn.jsdelivr.net/gh/xhamzar/posko-stickers@main/";
let _stikCache = null;
function insertAtCursor(ta, text) {
  const st = ta.selectionStart ?? ta.value.length, en = ta.selectionEnd ?? ta.value.length;
  const before = ta.value.slice(0, st), after = ta.value.slice(en);
  const pad = before && !/\n$/.test(before) ? "\n" : "";
  const padA = after && !/^\n/.test(after) ? "\n" : "";
  ta.value = before + pad + text + padA + after;
  ta.focus();
  const pos = (before + pad + text).length;
  try { ta.setSelectionRange(pos, pos); } catch (e) {}
}
function prettyStik(x) {
  return String(x).replace(/[-_]+/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}
async function loadStikPacks() {
  if (_stikCache) return _stikCache;
  let manifest = null;
  try {
    const r = await fetch(STICKER_CDN + "manifest.json");
    if (r.ok) manifest = await r.json();
  } catch (e) {}
  let paths = [];
  try {
    const r = await fetch("https://api.github.com/repos/xhamzar/posko-stickers/git/trees/main?recursive=1");
    if (r.ok) {
      const j = await r.json();
      paths = (j.tree || []).filter(x => x.type === "blob").map(x => x.path);
    }
  } catch (e) {}
  const IMG_RE = /\.(webp|png|gif|jpe?g|apng|avif)$/i;
  const packs = new Map();
  const ensure = id => {
    if (!packs.has(id)) packs.set(id, {id, name: prettyStik(id), stickers: [], seen: new Set()});
    return packs.get(id);
  };
  if (manifest && Array.isArray(manifest.packs)) {
    for (const p of manifest.packs) {
      const pack = ensure(p.id);
      if (p.name) pack.name = p.name;
      for (const st of (p.stickers || [])) {
        if (st.file && !pack.seen.has(st.file)) {
          pack.seen.add(st.file);
          pack.stickers.push({file: st.file, label: st.label || prettyStik(st.file.split("/").pop().replace(/\.[^.]+$/, ""))});
        }
      }
    }
  }
  for (const path of paths) {
    const m = path.match(/^packs\/([^/]+)\/([^/]+)$/);
    if (!m || !IMG_RE.test(m[2])) continue;
    const pack = ensure(m[1]);
    if (!pack.seen.has(path)) {
      pack.seen.add(path);
      pack.stickers.push({file: path, label: prettyStik(m[2].replace(/\.[^.]+$/, ""))});
    }
  }
  const out = [...packs.values()].filter(p => p.stickers.length)
    .map(p => ({id: p.id, name: p.name, stickers: p.stickers}));
  if (!out.length) throw new Error("Tidak ada stiker");
  _stikCache = {packs: out};
  return _stikCache;
}
async function toggleStiker(target) {
  const panel = document.querySelector(`.stik-panel[data-panel="${target}"]`);
  if (!panel) return;
  if (!panel.hidden) { panel.hidden = true; return; }
  panel.hidden = false;
  if (panel.dataset.loaded) return;
  panel.innerHTML = `<div class="muted">Memuat stiker…</div>`;
  try {
    const data = await loadStikPacks();
    panel.innerHTML = data.packs.map(pack => `
      <div class="stik-pack">${esc(pack.name)}</div>
      <div class="stik-grid">${pack.stickers.map(st => `
        <button type="button" class="stik-item" title="${esc(st.label)}" onclick="pickStiker('${target}', '${esc(st.file)}')"><img src="${STICKER_CDN}${esc(st.file)}" alt="${esc(st.label)}" loading="lazy"></button>`).join("")}
      </div>`).join("");
    panel.dataset.loaded = "1";
  } catch (e) {
    panel.innerHTML = `<div class="muted">Stiker belum bisa dimuat. Coba lagi nanti.</div>`;
  }
}
function pickStiker(target, file) {
  const ta = document.getElementById(target);
  if (ta) insertAtCursor(ta, `[stiker:${STICKER_CDN}${file}]`);
  const panel = document.querySelector(`.stik-panel[data-panel="${target}"]`);
  if (panel) panel.hidden = true;
}
const URL_RE = /(https?:\/\/[^\s<>"']+)/g;
function embedFor(rawUrl) {
  let url = rawUrl, trail = "";
  const tm = url.match(/[.,;:!?]+$/);
  if (tm) { trail = tm[0]; url = url.slice(0, -trail.length); }
  if (url.endsWith(")") && !url.includes("(")) { trail = ")" + trail; url = url.slice(0, -1); }
  let html;
  const yt = url.match(/(?:youtube\.com\/(?:watch\?v=|shorts\/|embed\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  if (yt) {
    html = `<span class="yt-lite" data-yt="${yt[1]}" onclick="playYt(this)" title="Putar video"><img src="https://i.ytimg.com/vi/${yt[1]}/hqdefault.jpg" alt="Video YouTube" loading="lazy"></span>`;
  } else if (url.startsWith("https://") && /\.(png|jpe?g|gif|webp|avif)(\?[^\s]*)?$/i.test(url)) {
    html = `<a href="${esc(url)}" target="_blank" rel="noopener"><img class="post-img" src="${esc(url)}" alt="" loading="lazy"></a>`;
  } else {
    html = `<a href="${esc(url)}" target="_blank" rel="noopener nofollow">${esc(url)}</a>`;
  }
  return html + esc(trail);
}
const STIKER_RE = /\[stiker:(https:\/\/[^\]\s]+)\]/g;
function richText(text) {
  return String(text ?? "").split(STIKER_RE).map((p, i) => i % 2 === 1
    ? `<img class="post-sticker" src="${esc(p)}" alt="stiker" loading="lazy">`
    : p.split(URL_RE).map(q => /^https?:\/\//.test(q) ? embedFor(q) : linkMentions(esc(q))).join("")).join("");
}
function jualLockHtml(kind, ref, idx, price) {
  const btn = store.me
    ? `<button class="btn small" data-unlock="${kind}:${ref}:${idx}:${price}">Buka · ${price} POSK</button>`
    : `<a class="btn small" href="#/login">Masuk untuk Membuka</a>`;
  return `<span class="jual-lock"><span class="jual-ic">${ic("lock")}</span><span class="jual-tx"><b>Konten Berbayar</b><small>${price} POSK · buka sekali, kebuka selamanya</small></span>${btn}</span>`;
}
function rich(text) {
  const src = String(text ?? "");
  const re = /\[\[JUAL-(LOCKED|OPEN):(topic|reply):([A-Za-z0-9_-]+):(\d+):(\d+)\]\]/g;
  let out = "", last = 0, m;
  while ((m = re.exec(src))) {
    out += richText(src.slice(last, m.index));
    const st = m[1], kind = m[2], ref = m[3], idx = +m[4], price = +m[5];
    if (st === "LOCKED") {
      out += jualLockHtml(kind, ref, idx, price);
      last = re.lastIndex;
    } else {
      const closeTag = "[[/JUAL-OPEN]]";
      const close = src.indexOf(closeTag, re.lastIndex);
      const inner = close >= 0 ? src.slice(re.lastIndex, close) : "";
      out += `<span class="jual-open"><span class="jual-head">${ic("unlock")} Konten berbayar · ${price} POSK · sudah dibuka</span><span class="jual-body">${richText(inner)}</span></span>`;
      last = close >= 0 ? close + closeTag.length : re.lastIndex;
      re.lastIndex = last;
    }
  }
  return out + richText(src.slice(last));
}
function linkMentions(escaped) {
  return escaped.replace(/(^|[\s(])@([A-Za-z0-9_]{3,24})/g, '$1<a class="mention" href="#/member/$2">@$2</a>');
}
function playYt(el) {
  const id = el.getAttribute("data-yt");
  el.outerHTML = `<span class="yt-wrap"><iframe src="https://www.youtube-nocookie.com/embed/${id}?autoplay=1" title="Video YouTube" allow="accelerometer; autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe></span>`;
}
function fileToB64(blob) {
  return new Promise((res, rej) => {
    const fr = new FileReader();
    fr.onload = () => res(String(fr.result).split(",")[1]);
    fr.onerror = rej;
    fr.readAsDataURL(blob);
  });
}
async function compressImage(file) {
  if (file.type === "image/gif") {
    if (file.size > 2_500_000) throw new Error("GIF terlalu besar (maks 2,5MB)");
    return await fileToB64(file);
  }
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, 1600 / Math.max(bmp.width, bmp.height));
  const cv = document.createElement("canvas");
  cv.width = Math.round(bmp.width * scale);
  cv.height = Math.round(bmp.height * scale);
  cv.getContext("2d").drawImage(bmp, 0, 0, cv.width, cv.height);
  const blob = await new Promise(res => cv.toBlob(res, "image/jpeg", 0.82));
  if (!blob) throw new Error("Gagal memproses gambar");
  return await fileToB64(blob);
}
const IMGBB_KEY = "0c269acc21a39ba4cbe043fc6eb9df43"; // upload gambar langsung ke imgbb dari browser user
async function uploadImage(input, targetId) {
  const file = input.files && input.files[0];
  const row = input.closest(".uprow");
  const status = row ? row.querySelector(".up-status") : null;
  input.value = "";
  if (!file) return;
  if (DEMO) { flash("Mode demo: upload gambar nonaktif", true); return; }
  loadStart();
  try {
    if (status) status.textContent = "Menyiapkan gambar…";
    const b64 = await compressImage(file);
    if (status) status.textContent = "Mengupload…";
    const fd = new FormData();
    fd.append("image", b64);
    const resp = await fetch("https://api.imgbb.com/1/upload?key=" + IMGBB_KEY, {method: "POST", body: fd});
    const dj = await resp.json().catch(() => null);
    if (!resp.ok || !dj || !dj.data || !dj.data.url) throw new Error((dj && dj.error && dj.error.message) || "Upload ke imgbb gagal");
    const r = {url: dj.data.url};
    const ta = document.getElementById(targetId);
    ta.value += (ta.value && !ta.value.endsWith("\n") ? "\n" : "") + r.url + "\n";
    ta.focus();
    if (status) status.textContent = "Gambar terupload — linknya sudah masuk ke tulisan.";
  } catch (e) {
    if (status) status.textContent = "";
    flash(e.message || "Upload gagal", true);
  } finally { loadEnd(); }
}
const initial = name => esc((name || "?").trim().charAt(0).toUpperCase());

/* ---------- Avatar Aset (potongan gambar dari CDN) ---------- */
const AVA_CDN = "https://cdn.jsdelivr.net/gh/xhamzar/posko-stickers@main/avatar/";
const AVA_CATS = [["model", "Model"], ["body", "Badan"], ["face", "Wajah"], ["mulut", "Mulut"], ["hair", "Rambut"], ["outfit", "Baju"], ["celana", "Celana"], ["spatu", "Sepatu"], ["acc", "Kepala"], ["back", "Punggung"], ["hand", "Tangan"], ["pet", "Peliharaan"], ["border", "Bingkai"], ["status", "Lencana"]];
const AVA_ORDER = ["back", "body", "spatu", "celana", "outfit", "hand", "face", "mulut", "hair", "acc"];
const AVA_DISABLED = ["back", "mulut"]; // dinonaktifkan sementara oleh Driyan 23 Okt (masih bug) — hapus dari daftar ini untuk mengaktifkan lagi
const AVA_ANCH = {back: {l: 22, t: 35.2, w: 56}, body: {l: 26.2, t: 15.9, w: 47.6}, spatu: {l: 29.8, t: 76.1, w: 40.5}, celana: {l: 31, t: 59.1, w: 38.1}, outfit: {l: 28.6, t: 48.9, w: 42.9}, hand: {l: 75, t: 56.8, h: 29.5}, face: {l: 31.5, t: 26.1, w: 36.9}, mulut: {l: 46.5, t: 48, w: 7}, hair: {l: 20.2, t: 5.7, w: 59.5}, acc: {l: 23.8, t: 1.1, w: 52.4}};
const AVA_RECT = {border_0: [11.1, 11.7, 83.8, 95.7], border_2: [11.5, 11, 88.5, 89], border_3: [10, 2.3, 86.7, 93.1], border_4: [11.5, 11, 88.5, 89]};
const AVA_DEFAULT = {body: "body_1", face: "face_0", hair: "hair_2", outfit: "outfit_0", celana: "celana_0", spatu: "spatu_0"};
const AVA_CORE = ["body", "face", "hair", "outfit", "celana", "spatu"];
function avaParse(str) {
  if (str && String(str).startsWith("a:")) {
    try { return {...AVA_DEFAULT, ...JSON.parse(String(str).slice(2))}; } catch (e) {}
  }
  return {...AVA_DEFAULT};
}
function avaImg(cat, id) { return AVA_CDN + cat + "/" + id + (id.endsWith("_idle") ? ".gif" : ".png"); }
function avaLayers(cfg) {
  return AVA_ORDER.filter(c => cfg[c] && !AVA_DISABLED.includes(c)).map(c => {
    const a = AVA_ANCH[c];
    const st = a.h
      ? `left:${a.l}%;top:${a.t}%;height:${a.h}%;transform:translateX(-50%)`
      : `left:${a.l}%;top:${a.t}%;width:${a.w}%`;
    return `<img class="avt-layer" src="${avaImg(c, cfg[c])}" style="${st}" alt="" loading="lazy" draggable="false">`;
  }).join("");
}
function avaChar(cfg) { if (cfg.model) return `<img class="avt-model" src="${avaImg("model", cfg.model)}" alt="" draggable="false">`; return `<span class="avt">${avaLayers(cfg)}</span>`; }
function avaCard(cfg) {
  const [l, t, r, b] = AVA_RECT[cfg.border] || [11, 11, 89, 89];
  return `<span class="avt-card">
    <img class="avt-frame" src="${avaImg("border", cfg.border)}" alt="" draggable="false">
    <span class="avt-window" style="left:${l}%;top:${t}%;width:${r - l}%;height:${b - t}%">
      <span class="avt" style="left:-11%;top:-5%;width:122%">${avaLayers(cfg)}</span>
    </span>
    ${cfg.pet ? `<img class="avt-pet" src="${avaImg("pet", cfg.pet)}" alt="" loading="lazy" draggable="false">` : ""}
    ${cfg.status ? `<img class="avt-status" src="${avaImg("status", cfg.status)}" alt="" loading="lazy" draggable="false">` : ""}
  </span>`;
}
function avatarHtml(name, avatarId, cls = "") {
  const cfg = avaParse(avatarId);
  if (cfg.model) return `<div class="avatar ${cls} avt-wrap"><img class="avt-model" src="${avaImg("model", cfg.model)}" alt="" loading="lazy" draggable="false"></div>`;
  if (cls === "big" && cfg.border) return `<div class="avatar big avt-wrap">${avaCard(cfg)}</div>`;
  return `<div class="avatar ${cls} avt-wrap">${avaChar(cfg)}</div>`;
}
function ago(iso) {
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "baru saja";
  if (s < 3600) return Math.floor(s / 60) + " menit lalu";
  if (s < 86400) return Math.floor(s / 3600) + " jam lalu";
  return Math.floor(s / 86400) + " hari lalu";
}
/* ---------- POSKOIN ---------- */
const coinChip = n => `<span class="coin-chip"><span class="coin-badge">P</span>${Number(n || 0)} POSK</span>`;
const demoUser = name => demoDB.users.find(u => u.username === name);
function demoCredit(name, amount, type, note, from = null) {
  const u = demoUser(name);
  if (u) u.coins = (u.coins || 0) + amount;
  demoDB.coinTx.push({from, to: name, amount, type, note, created: new Date().toISOString()});
}
async function refreshUnread() {
  if (DEMO || !store.me || !store.token) return;
  try {
    const r = await api("/notif");
    if (store.unread !== r.unread) { store.unread = r.unread; renderNav(); }
  } catch (e) { /* diam */ }
}
async function refreshCoins() {
  if (DEMO || !store.me || !store.token) return;
  try {
    const r = await api("/coin");
    if (store.me && r.balance !== store.me.coins) {
      store.me = {...store.me, coins: r.balance};
      renderNav(); renderSide();
    }
  } catch (e) {}
}
async function tipUser(toName, topicId) {
  const me = store.me;
  if (!me) return;
  const v = prompt("Kasih tip POSK ke " + toName + " berapa? (saldo kamu: " + (me.coins ?? 0) + " POSK)", "5");
  if (v === null) return;
  const amount = parseInt(v, 10);
  if (!amount || amount < 1) { flash("Jumlah tip tidak valid.", true); return; }
  try {
    if (DEMO) {
      const sender = demoUser(me.username), recv = demoUser(toName);
      if (!recv) throw new Error("User tujuan tidak ditemukan");
      if (!sender || (sender.coins || 0) < amount) throw new Error("Saldo POSK tidak cukup");
      sender.coins -= amount; recv.coins += amount;
      demoDB.coinTx.push({from: me.username, to: toName, amount, type: "tip", note: "", created: new Date().toISOString()});
      store.me = {...me, coins: sender.coins};
    } else {
      const r = await api("/coin", {method: "POST", body: {action: "tip", to: toName, amount}});
      store.me = {...me, coins: r.balance};
    }
    renderNav(); renderSide();
    flash("Berhasil kasih " + amount + " POSK ke " + toName + " 🎉");
    if (topicId) pageTopic(topicId);
  } catch (err) { flash(err.message, true); }
}
function flash(msg, isErr) {
  document.getElementById("flash").innerHTML =
    `<div class="flash${isErr ? " error" : ""}">${esc(msg)}</div>`;
}
function renderNav() {
  const me = store.me, el = document.getElementById("nav-user");
  el.innerHTML = me
    ? `<button class="avatar-btn" id="avatar-btn" type="button" aria-label="Menu akun">${avatarHtml(me.username, me.avatar, "small")}${store.unread ? `<span class="nbadge">${store.unread > 99 ? "99+" : store.unread}</span>` : ""}</button>
       <div class="usermenu" id="user-menu" hidden>
         <div class="um-head">${avatarHtml(me.username, me.avatar, "small")}<div class="um-id"><b>${esc(me.username)}</b><br><a href="#/koin">${coinChip(me.coins ?? 0)}</a></div></div>
         <a class="um-item" href="#/member/${esc(me.username)}">Profil Saya</a>
         <a class="um-item" href="#/koleksi">Koleksi Tema</a>
         <a class="um-item" href="#/timeline">Garis Waktu</a>
         <a class="um-item" href="#/notif">Notifikasi${store.unread ? ` (${store.unread})` : ""}</a>
         <a class="um-item" href="#/pos">Peta Pos</a>
         <a class="um-item" href="#/koin">POSKOIN Saya</a>
         <a class="um-item" href="#/new">Buat Topik</a>
         <a class="um-item" href="#/" id="logout">Keluar</a>
       </div>`
    : `<a href="#/login">Masuk</a> <a href="#/register">Daftar</a>`;
  const fl = document.getElementById("foot-links");
  if (fl) fl.innerHTML = me
    ? `<a href="#/">Beranda</a>
       <a href="#/koin">POSKOIN</a>
       <a href="#/new">Buat Topik</a>
       <a href="#/notif">Notifikasi${store.unread ? ` (${store.unread})` : ""}</a>
       <a href="#/member/${esc(me.username)}">Profil Saya</a>
       <a href="#/dokumen">Dokumen</a>
       <a href="#/about">Tentang</a>`
    : `<a href="#/">Beranda</a>
       <a href="#/dokumen">Dokumen</a>
       <a href="#/about">Tentang</a>
       <a href="#/login">Masuk</a>
       <a href="#/register">Daftar</a>`;
  const ab = document.getElementById("avatar-btn");
  if (ab) ab.onclick = e => { e.stopPropagation(); const m = document.getElementById("user-menu"); if (m) m.hidden = !m.hidden; };
  const lo = document.getElementById("logout");
  if (lo) lo.onclick = e => { e.preventDefault(); store.token = ""; store.me = null; location.hash = "#/"; renderNav(); };
}
const NODE_COLORS = ["#2e4b3f", "#3a6fd8", "#c93a3a", "#e2703a", "#b8860b", "#8a5fc0", "#3f9e4d", "#546e7a"];
async function getNodes() {
  const r = await apiOrDemo("/nodes", () => ({nodes: demoDB.nodes, favs: demoDB.nodeFavs || []}));
  if (Array.isArray(r)) return {nodes: r, favs: []};
  return {nodes: r.nodes || [], favs: r.favs || []};
}
function nodeTile(n, cls = "") {
  const words = (n.name || n.id || "?").trim().split(/\s+/);
  const ini = (words.length > 1 ? words[0][0] + words[1][0] : (words[0] || "?").slice(0, 2)).toUpperCase();
  return `<span class="node-tile ${cls}" style="background:${esc(n.color || NODE_COLORS[0])}">${esc(ini)}</span>`;
}
async function toggleFollow(nodeId, nowFav) {
  if (DEMO) {
    const i = demoDB.nodeFavs.indexOf(nodeId);
    if (nowFav && i < 0) demoDB.nodeFavs.push(nodeId);
    if (!nowFav && i >= 0) demoDB.nodeFavs.splice(i, 1);
    return {fav: nowFav};
  }
  return api("/nodes", {method: "POST", body: {action: nowFav ? "follow" : "unfollow", node: nodeId}});
}

let _popTags = null, _popTagsAt = 0;
async function popularTags() {
  if (_popTags && Date.now() - _popTagsAt < 60000) return _popTags;
  try {
    const all = await topicList();
    const cnt = {};
    all.forEach(t => (t.tags || []).forEach(x => { cnt[x] = (cnt[x] || 0) + 1; }));
    _popTags = Object.entries(cnt).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([tag, n]) => ({tag, n}));
    _popTagsAt = Date.now();
  } catch (e) { _popTags = _popTags || []; }
  return _popTags;
}
async function renderSide() {
  const {nodes, favs} = await getNodes();
  const me = store.me;
  const popTags = await popularTags();
  $side.innerHTML = `
    <div class="box"><div class="body">
      <div class="side-title">${me ? "Halo, " + esc(me.username) : "Selamat datang di POSKO"}</div>
      <div class="muted">${me ? "Siaga jaga pos hari ini." : "Sudah punya akun? <a href='#/login'>Masuk</a> — belum? <a href='#/register'>Daftar gratis</a>."}</div>
    </div></div>
    ${me ? `<div class="box"><div class="head"><b>POSKOIN Saya</b></div><div class="body">
      <div style="display:flex;align-items:center;gap:8px"><span class="coin-badge" style="width:26px;height:26px;font-size:15px">P</span>
      <span class="coin-big" style="font-size:22px">${Number(me.coins ?? 0)}</span><span class="muted">POSK</span></div>
      <div class="muted" style="margin-top:6px">Dapat POSK dari bikin topik (+5) &amp; balasan bermanfaat (+2), atau tip dari warga. <a href="#/koin">Riwayat &amp; aturan</a></div>
    </div></div>` : ""}
    ${me && favs.length ? `<div class="box"><div class="head"><b>Pos Saya</b></div><div class="body">
      ${nodes.filter(n => favs.includes(n.id)).map(n => `<a class="node-link" href="#/node/${esc(n.id)}">${nodeTile(n, "small")}<span>${esc(n.name)}</span></a>`).join("")}
    </div></div>` : ""}
    <div class="box"><div class="head"><b>Node (Pos Jaga)</b> · <a href="#/pos">Peta Pos</a></div><div class="body node-list">
      <a href="#/">Semua Topik</a>
      ${nodes.map(n => `<a class="node-link" href="#/node/${esc(n.id)}">${nodeTile(n, "small")}<span>${esc(n.name)}</span></a>`).join("")}
    </div></div>
    ${popTags.length ? `<div class="box"><div class="head"><b>Tag Populer</b></div><div class="body"><div class="tag-pills" style="margin-top:0">
      ${popTags.map(p => `<a class="tag-pill" href="#/tag/${esc(encodeURIComponent(p.tag))}">#${esc(p.tag)} · ${p.n}</a>`).join("")}
    </div></div></div>` : ""}
    <div class="box"><div class="body muted">POSKO = Pusat Obrolan &amp; Sharing Komunitas Online. Jaga sopan santun, jangan spam, hormati warga lain.</div></div>`;
}
function tagPills(t) {
  const tags = (t && t.tags) || [];
  if (!tags.length) return "";
  return `<div class="tag-pills">${tags.map(x => `<a class="tag-pill" href="#/tag/${esc(encodeURIComponent(x))}">#${esc(x)}</a>`).join("")}</div>`;
}
function topicRow(t) {
  return `<div class="cell">
    ${avatarHtml(t.author, t.avatar)}
    <div style="min-width:0">
      <a class="topic-title" href="#/topic/${esc(t.id)}">${esc(t.title)}</a>
      ${t.pinned ? '<span class="pin">★ PIN</span>' : ""} ${t.locked ? '<span class="lock">🔒 terkunci</span>' : ""}
      <div class="meta"><a class="node-tag" href="#/node/${esc(t.node)}">${esc(t.node)}</a>
      &nbsp;oleh <b>${esc(t.author)}</b> · ${ago(t.last)} · ${t.views ?? 0} kali dilihat</div>
      ${tagPills(t)}
    </div>
    <div class="count">${t.replies ?? 0}</div>
  </div>`;
}
const PER_PAGE = 20;
async function topicList(filter = {}, page = 1) {
  page = Math.max(1, parseInt(page, 10) || 1);
  const qs = new URLSearchParams({...filter, page, per_page: PER_PAGE}).toString();
  const norm = r => Array.isArray(r)
    ? {topics: r, total: r.length, page: 1, per_page: r.length || PER_PAGE, pages: 1}
    : r;
  return norm(await apiOrDemo("/topics" + (qs ? "?" + qs : ""), () => {
    let list = [...demoDB.topics];
    if (filter.node) list = list.filter(t => t.node === filter.node);
    if (filter.tag) list = list.filter(t => (t.tags || []).includes(filter.tag));
    if (filter.q) list = list.filter(t => (t.title + " " + t.content + " " + (t.tags || []).join(" ")).toLowerCase().includes(filter.q.toLowerCase()));
    if (filter.author) list = list.filter(t => t.author === filter.author);
    list.sort((a, b) => (b.pinned - a.pinned) || (new Date(b.last) - new Date(a.last)));
    list.forEach(t => { t.replies = demoDB.replies.filter(r => r.topic === t.id).length;
      const u = demoUser(t.author); t.avatar = u ? (u.avatar || "") : ""; });
    const total = list.length, pages = Math.max(1, Math.ceil(total / PER_PAGE));
    page = Math.min(page, pages);
    return {topics: list.slice((page - 1) * PER_PAGE, page * PER_PAGE),
      total, page, per_page: PER_PAGE, pages};
  }));
}
/* ---------- pagination ---------- */
function pagerHTML(p, base) {
  if (!p || p.pages <= 1) return "";
  const link = pg => base + (base.includes("?") ? "&" : "?") + "page=" + pg;
  const btn = (pg, label, cls = "") => cls === "cur"
    ? `<span class="pg-btn cur">${label}</span>`
    : `<a class="pg-btn" href="${link(pg)}">${label}</a>`;
  let nums = "", last = 0;
  for (let i = 1; i <= p.pages; i++) {
    if (i === 1 || i === p.pages || Math.abs(i - p.page) <= 2) {
      if (last && i - last > 1) nums += `<span class="pg-gap">…</span>`;
      nums += btn(i, i, i === p.page ? "cur" : "");
      last = i;
    }
  }
  return `<div class="pg-wrap">`
    + (p.page > 1 ? btn(p.page - 1, "‹") : `<span class="pg-btn dis">‹</span>`)
    + nums
    + (p.page < p.pages ? btn(p.page + 1, "›") : `<span class="pg-btn dis">›</span>`)
    + `<span class="pg-info">${p.total} topik</span></div>`;
}

/* ---------- halaman ---------- */
async function pageHome(page = 1) {
  const r = await topicList({}, page);
  const topics = r.topics;
  $view.innerHTML = `<div class="box"><div class="head">Topik Terbaru
    <span class="fr">${store.me ? '<a class="btn primary" href="#/new">+ Topik Baru</a>' : '<a class="btn primary" href="#/login">Masuk untuk Buat Topik</a>'}</span></div>
    ${topics.map(topicRow).join("") || '<div class="cell">Belum ada topik.</div>'}
    ${pagerHTML(r, "#/")}</div>`;
}
/* ---------- Peta Pos (direktori Node / Pos Jaga) ---------- */
async function pagePos() {
  const {nodes, favs} = await getNodes();
  const me = store.me;
  let newColor = NODE_COLORS[0];
  const card = n => `<div class="pos-card">
    <div style="display:flex;gap:10px;align-items:flex-start">
      ${nodeTile(n)}
      <div style="min-width:0;flex:1">
        <a href="#/node/${esc(n.id)}"><b>${esc(n.name)}</b></a>
        <div class="muted" style="font-size:12px">${esc(n.desc || "")}</div>
        <div class="meta" style="margin-top:2px">@${esc(n.owner || "admin")} · ${n.topics ?? 0} topik · ${n.followers ?? 0} pengikut</div>
      </div>
    </div>
    <div class="act-row">
      <a class="btn" href="#/node/${esc(n.id)}">Masuk Pos</a>
      ${me ? `<button class="btn" data-follow="${esc(n.id)}">${favs.includes(n.id) ? "Berhenti Ikuti" : "Ikuti"}</button>` : ""}
    </div>
  </div>`;
  $view.innerHTML = `<div class="box"><div class="head"><b>Peta Pos</b>
    <div class="muted">Semua Pos Jaga di POSKO. Ikuti pos favoritmu biar muncul di sidebar "Pos Saya".</div></div>
    <div class="body">
      ${me ? `<button class="btn primary" id="btn-open-pos">Buka Pos Baru</button>
      <form id="pos-form" style="display:none;margin-top:12px">
        <label>Nama Pos (3-30 karakter)</label>
        <input type="text" id="pos-name" maxlength="30" placeholder="Misal: Memancing, Retro Game, Fotografi" required>
        <label>Deskripsi Singkat</label>
        <input type="text" id="pos-desc" maxlength="120" placeholder="Pos ini bahas apa?">
        <label>Warna Pos</label>
        <div class="av-swatches" id="pos-colors">${NODE_COLORS.map((c, i) =>
          `<button type="button" class="color-sw${i === 0 ? " sel" : ""}" data-color="${c}" style="background:${c}" aria-label="${c}"></button>`).join("")}</div>
        <div class="muted" style="margin:8px 0">Biaya buka pos: <b>200 POSK</b> (admin gratis). Saldo kamu: <b>${me.coins ?? 0} POSK</b>. Kamu otomatis jadi Penjaga pos ini.</div>
        <button class="btn primary" type="submit">Buka Pos</button>
        <button class="btn" type="button" id="pos-cancel">Batal</button>
      </form>` : `<div class="muted"><a href="#/login">Masuk</a> buat mengikuti pos atau membuka Pos Jaga baru.</div>`}
      <div class="pos-grid" style="margin-top:14px">${nodes.map(card).join("")}</div>
    </div></div>`;
  $view.querySelectorAll("[data-follow]").forEach(b => b.onclick = async () => {
    try {
      const now = b.textContent.includes("Berhenti");
      await toggleFollow(b.dataset.follow, !now);
      pagePos(); renderSide();
      flash(!now ? "Pos diikuti." : "Berhenti mengikuti pos.");
    } catch (err) { flash(err.message, true); }
  });
  const bo = document.getElementById("btn-open-pos");
  if (bo) bo.onclick = () => { const f = document.getElementById("pos-form"); f.style.display = f.style.display === "none" ? "block" : "none"; };
  const pc = document.getElementById("pos-cancel");
  if (pc) pc.onclick = () => document.getElementById("pos-form").style.display = "none";
  $view.querySelectorAll("#pos-colors .color-sw").forEach(b => b.onclick = () => {
    newColor = b.dataset.color;
    $view.querySelectorAll("#pos-colors .color-sw").forEach(x => x.classList.toggle("sel", x === b));
  });
  const pf = document.getElementById("pos-form");
  if (pf) pf.onsubmit = async e => {
    e.preventDefault();
    const name = document.getElementById("pos-name").value.trim();
    const desc = document.getElementById("pos-desc").value.trim();
    try {
      if (DEMO) { flash("Mode demo: buka pos nonaktif", true); return; }
      const r = await api("/nodes", {method: "POST", body: {action: "create", name, desc, color: newColor}});
      if (store.me && typeof r.node === "object") store.me = {...store.me, coins: Math.max(0, (store.me.coins ?? 0) - (store.me.role === "admin" ? 0 : 200))};
      renderNav(); renderSide();
      flash("Pos Jaga baru dibuka 🎉");
      location.hash = "#/node/" + r.node.id;
    } catch (err) { flash(err.message, true); }
  };
}
async function pageNode(id, page = 1) {
  const {nodes, favs} = await getNodes();
  const node = nodes.find(n => n.id === id) || {id, name: id, desc: "", color: NODE_COLORS[0], owner: "admin", topics: 0, followers: 0};
  const r = await topicList({node: id}, page);
  const topics = r.topics;
  const me = store.me;
  const faved = favs.includes(id);
  $view.innerHTML = `<div class="box"><div class="head">
    <div style="display:flex;gap:12px;align-items:flex-start">
      ${nodeTile(node, "big")}
      <div style="min-width:0;flex:1">
        <b style="font-size:17px">${esc(node.name)}</b>
        <div class="muted">${esc(node.desc || "")}</div>
        <div class="meta" style="margin-top:3px">Penjaga: <a href="#/member/${esc(node.owner || "admin")}">@${esc(node.owner || "admin")}</a>
          · ${node.topics ?? r.total} topik · <span id="node-followers">${node.followers ?? 0}</span> pengikut</div>
        <div class="act-row">
          ${me ? `<button class="btn" id="btn-node-follow">${faved ? "Berhenti Ikuti" : "Ikuti Pos"}</button>
          <button class="btn primary" id="btn-node-new">Buat Topik di Pos Ini</button>` : ""}
        </div>
      </div>
    </div></div>
    ${topics.map(topicRow).join("") || '<div class="cell">Belum ada topik di pos ini.</div>'}${pagerHTML(r, "#/node/" + encodeURIComponent(id))}</div>`;
  const bf = document.getElementById("btn-node-follow");
  if (bf) bf.onclick = async () => {
    try {
      const now = bf.textContent.includes("Berhenti");
      const r = await toggleFollow(id, !now);
      bf.textContent = !now ? "Berhenti Ikuti" : "Ikuti Pos";
      if (r && typeof r.followers === "number") document.getElementById("node-followers").textContent = r.followers;
      renderSide();
      flash(!now ? "Pos diikuti — muncul di Pos Saya." : "Berhenti mengikuti pos.");
    } catch (err) { flash(err.message, true); }
  };
  const bn = document.getElementById("btn-node-new");
  if (bn) bn.onclick = () => { window._newNode = id; location.hash = "#/new"; };
}
/* ---------- ikon SVG (gaya garis minimal) ---------- */
const IC = {
  edit: '<svg viewBox="0 0 24 24"><path d="M17 3a2.83 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/></svg>',
  trash: '<svg viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>',
  pin: '<svg viewBox="0 0 24 24"><path d="M9 3h6v5l2 4H7l2-4z"/><path d="M12 12v9"/></svg>',
  lock: '<svg viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
  unlock: '<svg viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.7-1.6"/></svg>',
  lock: '<svg viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
  unlock: '<svg viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.7-1.6"/></svg>',
  coin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><text x="12" y="16.5" text-anchor="middle" font-size="11" font-weight="700" fill="currentColor" stroke="none">P</text></svg>',
  bookmark: '<svg viewBox="0 0 24 24"><path d="M6 3h12a1 1 0 0 1 1 1v17l-7-4.2L5 21V4a1 1 0 0 1 1-1z"/></svg>',
  reply: '<svg viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 6 6v5"/></svg>',
  share: '<svg viewBox="0 0 24 24"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4"/><path d="M15.4 6.5l-6.8 4"/></svg>'
};
const ic = n => IC[n] || "";

async function pageTopic(id) {
  let seen = false;
  try { seen = sessionStorage.getItem("pv:" + id) === "1";
        if (!seen) sessionStorage.setItem("pv:" + id, "1"); } catch (e) {}
  const data = await apiOrDemo("/topic?id=" + encodeURIComponent(id) + (seen ? "" : "&hit=1"), () => {
    const t = demoDB.topics.find(x => x.id === id);
    if (!t) throw new Error("Topik tidak ditemukan");
    if (!seen) t.views = (t.views || 0) + 1;
    const withAv = o => { const u = demoUser(o.author); return {...o, avatar: u ? (u.avatar || "") : ""}; };
    return {topic: withAv(t), replies: demoDB.replies.filter(r => r.topic === id).map(withAv)};
  });
  const t = data.topic, me = store.me, isAdmin = me && me.role === "admin";
  const {nodes: allNodes} = await getNodes();
  const nodeOwner = (allNodes.find(n => n.id === t.node) || {}).owner || "admin";
  const isPenjaga = !!(me && nodeOwner !== "admin" && me.username === nodeOwner);
  const canMod = !!(isAdmin || isPenjaga);
  const canEditTopic = me && (me.username === t.author || isAdmin);
  const canDelTopic = !!(canEditTopic || isPenjaga);
  const canEditReply = r => me && (me.username === r.author || isAdmin);
  const canDelReply = r => !!(canEditReply(r) || isPenjaga);
  $view.innerHTML = `
    <div class="box">
      <div class="head"><a href="#/node/${esc(t.node)}" class="node-tag">${esc(t.node)}</a>
        <div style="font-size:18px;margin-top:6px">${esc(t.title)}</div>
        <div class="meta"><span style="display:inline-block;vertical-align:-7px;margin-right:4px">${avatarHtml(t.author, t.avatar, "small")}</span>oleh <a href="#/member/${esc(t.author)}"><b>${esc(t.author)}</b></a> · ${ago(t.created)} · ${t.views ?? 0} kali dilihat
        ${t.pinned ? '· <span class="pin">★ PIN</span>' : ""} ${t.locked ? '· <span class="lock">🔒 terkunci</span>' : ""}</div>
        ${tagPills(t)}
        <div class="act-row">
          ${canEditTopic ? `<button class="icon-btn" id="btn-edit-topic" title="Edit Topik" aria-label="Edit Topik">${ic("edit")}</button>` : ""}
          ${canDelTopic ? `<button class="icon-btn danger" id="btn-del-topic" title="Hapus Topik" aria-label="Hapus Topik">${ic("trash")}</button>` : ""}
          ${canMod ? `<button class="icon-btn${t.pinned ? " on" : ""}" data-mod="pin" title="${t.pinned ? "Lepas Pin" : "Pin Topik"}" aria-label="Pin Topik">${ic("pin")}</button>
          <button class="icon-btn${t.locked ? " on" : ""}" data-mod="lock" title="${t.locked ? "Buka Kunci" : "Kunci Topik"}" aria-label="Kunci Topik">${ic(t.locked ? "unlock" : "lock")}</button>` : ""}
          ${me && me.username !== t.author ? `<button class="icon-btn" data-tipuser="${esc(t.author)}" title="Kasih POSKOIN" aria-label="Kasih POSKOIN">${ic("coin")}</button>` : ""}
          ${me ? `<button class="icon-btn" id="btn-fav" title="Simpan ke Koleksi" aria-label="Koleksi">${ic("bookmark")}</button>` : ""}
          <button class="icon-btn" id="btn-share" title="Bagikan Topik" aria-label="Bagikan Topik">${ic("share")}</button>
          ${me && !t.locked && me.username !== t.author ? `<button class="icon-btn" id="btn-replyto" title="Balas" aria-label="Balas">${ic("reply")}</button>` : ""}
        </div>
        ${canEditTopic ? `<form id="edit-topic-form" style="display:none;margin-top:10px">
          <label>Judul</label><input type="text" id="et-title" maxlength="160" value="${esc(t.title)}">
          <label>Isi</label><textarea id="et-content">${esc(t.contentRaw || t.content)}</textarea>
          <label>Tag (maks 5, pisahkan koma)</label><input type="text" id="et-tags" maxlength="140" value="${esc((t.tags || []).join(", "))}">
          <button class="btn primary" type="submit">Simpan Perubahan</button>
          <button class="btn" type="button" id="et-cancel">Batal</button></form>` : ""}
      </div>
      <div class="body"><div class="content">${rich(t.content)}</div></div>
    </div>
    <div class="box"><div class="head"><b>${data.replies.length} Balasan</b></div>
      ${data.replies.map(r => `<div class="reply"><div class="rhead">
          ${avatarHtml(r.author, r.avatar, "small")}
          <div><a href="#/member/${esc(r.author)}"><b>${esc(r.author)}</b></a>
          <span class="meta"> · ${ago(r.created)}${r.edited ? " · diedit" : ""}</span>
          ${(canDelReply(r) || (me && me.username !== r.author) || (me && !t.locked)) ? `<div class="act-row" style="margin-top:4px">
            ${canEditReply(r) ? `<button class="icon-btn" data-redit="${esc(r.id)}" title="Edit Balasan" aria-label="Edit Balasan">${ic("edit")}</button>` : ""}
            ${canDelReply(r) ? `<button class="icon-btn danger" data-rdel="${esc(r.id)}" title="Hapus Balasan" aria-label="Hapus Balasan">${ic("trash")}</button>` : ""}
            ${me && me.username !== r.author ? `<button class="icon-btn" data-tipuser="${esc(r.author)}" title="Kasih POSKOIN" aria-label="Kasih POSKOIN">${ic("coin")}</button>` : ""}
            ${me && !t.locked ? `<button class="icon-btn" data-replyto="${esc(r.author)}" title="Balas ${esc(r.author)}" aria-label="Balas">${ic("reply")}</button>` : ""}
          </div>` : ""}
          </div></div>
          <div class="rbody" id="rbody-${esc(r.id)}">${rich(r.content)}</div>
          ${canEditReply(r) ? `<form class="redit-form" id="rform-${esc(r.id)}" style="display:none;margin:8px 0 0 58px">
            <textarea id="rtext-${esc(r.id)}">${esc(r.contentRaw || r.content)}</textarea>
            <button class="btn primary" type="submit">Simpan</button>
            <button class="btn" type="button" data-rcancel="${esc(r.id)}">Batal</button></form>` : ""}
          </div>`).join("") || '<div class="reply">Belum ada balasan.</div>'}
    </div>
    ${me && !t.locked ? `<div class="box"><div class="head"><b>Tulis Balasan</b></div><div class="body">
        <form id="reply-form"><textarea id="reply-content" placeholder="Tulis balasanmu…" required></textarea>
        <div class="uprow"><label class="btn">Upload Gambar<input type="file" accept="image/*" hidden onchange="uploadImage(this, 'reply-content')"></label><button type="button" class="btn" onclick="toggleStiker('reply-content')">Stiker</button><span class="muted up-status"></span></div>
        <div class="stik-panel" data-panel="reply-content" hidden></div>
        <button class="btn primary" type="submit">Kirim Balasan</button></form></div></div>`
      : `<div class="box"><div class="body muted">${t.locked ? "Topik ini terkunci." : 'Kamu harus <a href="#/login">masuk</a> dulu buat membalas.'}</div></div>`}`;
  document.querySelectorAll("[data-mod]").forEach(b => b.onclick = () => moderate(id, b.dataset.mod));
  document.querySelectorAll("[data-tipuser]").forEach(b => b.onclick = () => tipUser(b.dataset.tipuser, id));
  const replyTo = name => {
    const ta = document.getElementById("reply-content");
    if (!ta) return;
    const tag = "@" + name + " ";
    if (!ta.value.includes(tag)) ta.value = tag + ta.value;
    ta.focus();
    ta.scrollIntoView({behavior: "smooth", block: "center"});
  };
  document.querySelectorAll("[data-replyto]").forEach(b => b.onclick = () => replyTo(b.dataset.replyto));
  const brt = document.getElementById("btn-replyto");
  if (brt) brt.onclick = () => replyTo(t.author);
  const bf = document.getElementById("btn-fav");
  if (bf) {
    let faved = false;
    const paint = () => { bf.classList.toggle("on", faved); bf.title = faved ? "Hapus dari Koleksi" : "Simpan ke Koleksi"; };
    if (DEMO) { faved = (demoDB.favs || []).includes(id); paint(); }
    else api("/fav").then(r => { faved = (r.ids || []).includes(id); paint(); }).catch(() => {});
    paint();
    bf.onclick = async () => {
      try {
        if (DEMO) { const i = demoDB.favs.indexOf(id); if (i >= 0) { demoDB.favs.splice(i, 1); faved = false; } else { demoDB.favs.push(id); faved = true; } }
        else { const r = await api("/fav", {method: "POST", body: {topic: id}}); faved = !!r.fav; }
        paint();
        flash(faved ? "Masuk Koleksi Tema." : "Dihapus dari Koleksi Tema.");
      } catch (err) { flash(err.message, true); }
    };
  }
  const bsh = document.getElementById("btn-share");
  if (bsh) bsh.onclick = async () => {
    const url = location.origin + "/t/" + id;
    if (navigator.share) { try { await navigator.share({title: t.title, url}); } catch (e) {} return; }
    try { await navigator.clipboard.writeText(url); flash("Link topik tersalin. Tempel di WhatsApp buat dapetin kartu preview-nya."); }
    catch (e) { window.prompt("Salin link topik ini:", url); }
  };
  const bet = document.getElementById("btn-edit-topic");
  if (bet) bet.onclick = () => { const f = document.getElementById("edit-topic-form"); f.style.display = f.style.display === "none" ? "block" : "none"; };
  const etc = document.getElementById("et-cancel");
  if (etc) etc.onclick = () => document.getElementById("edit-topic-form").style.display = "none";
  const etf = document.getElementById("edit-topic-form");
  if (etf) etf.onsubmit = async e => {
    e.preventDefault();
    const body = {kind: "topic", id, title: document.getElementById("et-title").value.trim(), content: document.getElementById("et-content").value.trim(),
      tags: document.getElementById("et-tags").value.split(",").map(s => s.trim().toLowerCase()).filter(Boolean).slice(0, 5)};
    try {
      if (DEMO) { const tt = demoDB.topics.find(x => x.id === id); tt.title = body.title; tt.content = body.content; tt.tags = body.tags; }
      else await api("/edit", {method: "POST", body});
      pageTopic(id);
    } catch (err) { flash(err.message, true); }
  };
  const bdt = document.getElementById("btn-del-topic");
  if (bdt) bdt.onclick = () => removeItem("topic", id, id);
  document.querySelectorAll("[data-redit]").forEach(b => b.onclick = () => {
    const f = document.getElementById("rform-" + b.dataset.redit);
    f.style.display = f.style.display === "none" ? "block" : "none";
  });
  document.querySelectorAll("[data-rcancel]").forEach(b => b.onclick = () => {
    document.getElementById("rform-" + b.dataset.rcancel).style.display = "none";
  });
  document.querySelectorAll(".redit-form").forEach(f => f.onsubmit = async e => {
    e.preventDefault();
    const rid = f.id.replace("rform-", "");
    const content = document.getElementById("rtext-" + rid).value.trim();
    try {
      if (DEMO) { const rr = demoDB.replies.find(x => x.id === rid); rr.content = content; rr.edited = true; }
      else await api("/edit", {method: "POST", body: {kind: "reply", id: rid, content}});
      pageTopic(id);
    } catch (err) { flash(err.message, true); }
  });
  document.querySelectorAll("[data-rdel]").forEach(b => b.onclick = () => removeItem("reply", b.dataset.rdel, id));
  const rf = document.getElementById("reply-form");
  if (rf) rf.onsubmit = async e => {
    e.preventDefault();
    const content = document.getElementById("reply-content").value.trim();
    if (!content) return;
    try {
      let awarded = 0;
      if (DEMO) {
        demoDB.replies.push({id: "r" + Date.now(), topic: id, author: me.username, content, created: new Date().toISOString()});
        if (content.length >= 10) { awarded = 2; demoCredit(me.username, 2, "reward", "Reward balasan");
          const u = demoUser(me.username); if (u) store.me = {...me, coins: u.coins}; }
      } else {
        const r = await api("/replies", {method: "POST", body: {topic: id, content}});
        awarded = r.awarded || 0;
        if (r.balance !== undefined) store.me = {...me, coins: r.balance};
      }
      await pageTopic(id);
      renderNav();
      if (awarded) flash("+" + awarded + " POSK buat balasanmu 🪙");
    } catch (err) { flash(err.message, true); }
  };
}
async function moderate(id, action) {
  try {
    if (DEMO) {
      const t = demoDB.topics.find(x => x.id === id);
      if (action === "pin") t.pinned = !t.pinned;
      if (action === "lock") t.locked = !t.locked;
      if (action === "delete") { demoDB.topics = demoDB.topics.filter(x => x.id !== id); location.hash = "#/"; return; }
      pageTopic(id);
    } else { await api("/moderate", {method: "POST", body: {topic: id, action}}); pageTopic(id); }
  } catch (err) { flash(err.message, true); }
}
async function removeItem(kind, did, topicId) {
  if (!confirm(kind === "topic" ? "Hapus topik ini beserta semua balasannya?" : "Hapus balasan ini?")) return;
  try {
    if (DEMO) {
      if (kind === "topic") { demoDB.topics = demoDB.topics.filter(x => x.id !== did); demoDB.replies = demoDB.replies.filter(x => x.topic !== did); location.hash = "#/"; return; }
      demoDB.replies = demoDB.replies.filter(x => x.id !== did); pageTopic(topicId);
    } else {
      await api("/remove", {method: "POST", body: {kind, id: did}});
      if (kind === "topic") location.hash = "#/"; else pageTopic(topicId);
    }
  } catch (err) { flash(err.message, true); }
}
async function pageTag(tag, page = 1) {
  const tg = (tag || "").trim().toLowerCase();
  const r = await topicList({tag: tg}, page);
  const topics = r.topics;
  $view.innerHTML = `<div class="box"><div class="head"><b>Tag: #${esc(tg)}</b>
    <div class="muted">Semua topik bertag ini, dari Pos mana pun.</div></div>
    ${topics.map(topicRow).join("") || '<div class="cell">Belum ada topik dengan tag ini.</div>'}${pagerHTML(r, "#/tag/" + encodeURIComponent(tg))}</div>`;
}
async function pageNew() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya sebelum buat topik."); return; }
  const {nodes} = await getNodes();
  const preNode = window._newNode || "";
  window._newNode = "";
  $view.innerHTML = `<div class="box"><div class="head"><b>Buat Topik Baru</b></div><div class="body">
    <form id="new-form">
      <label>Node</label><select id="new-node">${nodes.map(n => `<option value="${esc(n.id)}" ${n.id === preNode ? "selected" : ""}>${esc(n.name)}</option>`).join("")}</select>
      <label>Judul</label><input type="text" id="new-title" required maxlength="120">
      <label>Isi</label><textarea id="new-content" required></textarea>
      <label>Tag (opsional, maks 5, pisahkan koma)</label><input type="text" id="new-tags" maxlength="140" placeholder="misal: deepseek, open-source">
      <div class="uprow"><label class="btn">Upload Gambar<input type="file" accept="image/*" hidden onchange="uploadImage(this, 'new-content')"></label><button type="button" class="btn" onclick="toggleStiker('new-content')">Stiker</button><span class="muted up-status"></span></div>
      <div class="stik-panel" data-panel="new-content" hidden></div>
      <button class="btn primary" type="submit">Terbitkan Topik</button>
    </form></div></div>`;
  document.getElementById("new-form").onsubmit = async e => {
    e.preventDefault();
    const body = {node: document.getElementById("new-node").value,
      title: document.getElementById("new-title").value.trim(),
      content: document.getElementById("new-content").value.trim(),
      tags: document.getElementById("new-tags").value.split(",").map(s => s.trim().toLowerCase()).filter(Boolean).slice(0, 5)};
    try {
      if (DEMO) { const id = "t" + Date.now(); demoDB.topics.push({id, ...body, author: me.username,
        created: new Date().toISOString(), last: new Date().toISOString(), pinned: false, locked: false, replies: 0});
        demoCredit(me.username, 5, "reward", "Reward topik baru");
        const u = demoUser(me.username); if (u) store.me = {...me, coins: u.coins};
        window.__flash = "+5 POSK buat topik barumu 🪙";
        location.hash = "#/topic/" + id; }
      else { const r = await api("/topics", {method: "POST", body});
        if (r.balance !== undefined) store.me = {...me, coins: r.balance};
        if (r.awarded) window.__flash = "+" + r.awarded + " POSK buat topik barumu 🪙";
        location.hash = "#/topic/" + r.id; }
    } catch (err) { flash(err.message, true); }
  };
}
function pageLogin() {
  $view.innerHTML = `<div class="box"><div class="head"><b>Masuk ke POSKO</b></div><div class="body">
    <form id="login-form"><label>Email</label><input type="email" id="li-email" required>
    <label>Password</label><input type="password" id="li-pass" required>
    <button class="btn primary" type="submit">Masuk</button>
    <span class="muted"> Belum punya akun? <a href="#/register">Daftar</a></span></form></div></div>`;
  document.getElementById("login-form").onsubmit = async e => {
    e.preventDefault();
    const email = document.getElementById("li-email").value.trim();
    try {
      if (DEMO) { const un = email.split("@")[0]; const du = demoUser(un);
        store.me = {username: un, email, role: email.startsWith("driyan") ? "admin" : "member", coins: du ? (du.coins ?? 0) : 0,
          bio: du ? (du.bio || "") : "", avatar: du ? (du.avatar || "") : ""}; store.token = "demo"; }
      else { const r = await api("/login", {method: "POST", body: {email, password: document.getElementById("li-pass").value}}); store.token = r.token; store.me = r.user; }
      renderNav(); renderSide(); location.hash = "#/"; flash("Selamat datang kembali, " + store.me.username + "!");
    } catch (err) { flash(err.message, true); }
  };
}
function pageRegister() {
  $view.innerHTML = `<div class="box"><div class="head"><b>Daftar Akun POSKO</b></div><div class="body">
    <form id="reg-form"><label>Username</label><input type="text" id="rg-user" required maxlength="24" pattern="[A-Za-z0-9_]+">
    <label>Email</label><input type="email" id="rg-email" required>
    <label>Password</label><input type="password" id="rg-pass" required minlength="6">
    <button class="btn primary" type="submit">Daftar</button></form></div></div>`;
  document.getElementById("reg-form").onsubmit = async e => {
    e.preventDefault();
    const body = {username: document.getElementById("rg-user").value.trim(),
      email: document.getElementById("rg-email").value.trim(),
      password: document.getElementById("rg-pass").value};
    try {
      if (DEMO) { demoDB.users.push({username: body.username, joined: new Date().toISOString().slice(0,10), role: "member", coins: 0, bio: "", avatar: ""});
        demoCredit(body.username, 20, "welcome", "Bonus warga baru");
        store.me = {username: body.username, email: body.email, role: "member", coins: 20, bio: "", avatar: ""}; store.token = "demo"; }
      else { const r = await api("/register", {method: "POST", body}); store.token = r.token; store.me = r.user; }
      renderNav(); renderSide(); location.hash = "#/"; flash("Akun berhasil dibuat. Selamat bergabung di POSKO, " + body.username + "!");
    } catch (err) { flash(err.message, true); }
  };
}
async function pageMember(username, page = 1) {
  const me = store.me, isAdmin = me && me.role === "admin";
  let p = null;
  if (DEMO) {
    const u = demoUser(username);
    if (u) p = {username: u.username, role: u.role, joined: u.joined, bio: u.bio || "",
      avatar: u.avatar || "", coins: u.coins ?? 0,
      stats: {topics: demoDB.topics.filter(t => t.author === username).length,
              replies: demoDB.replies.filter(r => r.author === username).length}};
  } else {
    try { p = await api("/profile?user=" + encodeURIComponent(username)); } catch (e) {}
  }
  if (!p) { $view.innerHTML = `<div class="flash error">User tidak ditemukan.</div>`; return; }
  const r = await topicList({author: username}, page);
  const topics = r.topics;
  const own = me && me.username === p.username;
  $view.innerHTML = `
    <div class="box"><div class="body">
      <div style="display:flex;gap:14px;align-items:flex-start">
        ${avatarHtml(p.username, p.avatar, "big")}
        <div style="min-width:0">
          <b style="font-size:18px">${esc(p.username)}</b>
          <span class="role-badge">${p.role === "admin" ? "ADMIN" : "WARGA"}</span>
          <div class="muted">Bergabung ${esc(p.joined || "-")}</div>
          <div style="margin-top:4px">${p.bio ? esc(p.bio) : '<span class="muted">Belum ada bio.</span>'}</div>
          <div class="stat-row">
            <span>Topik: <b>${p.stats.topics}</b></span>
            <span>Balasan: <b>${p.stats.replies}</b></span>
            <span>${coinChip(p.coins)}</span>
          </div>
        </div>
      </div>
      ${own ? `<div style="margin-top:12px"><button class="btn" id="btn-edit-profile">Edit Profil</button>
        <a class="btn" href="#/koin">POSKOIN Saya</a></div>
      <form id="profile-form" style="display:none;margin-top:12px">
        <label>Bio (maks 160 karakter)</label>
        <input type="text" id="pf-bio" maxlength="160" value="${esc(p.bio || "")}" placeholder="Ceritain dikit tentang kamu…">
        <label>Avatar</label>
        <div style="display:flex;gap:10px;align-items:center;margin:2px 0 10px">
          ${avatarHtml(p.username, p.avatar)}
          <span class="muted">Avatar aset POSKO</span>
          <a class="btn" href="#/avatar">Ganti Avatar</a>
        </div>
        <button class="btn primary" type="submit">Simpan Profil</button>
        <button class="btn" type="button" id="pf-cancel">Batal</button>
      </form>` : ""}
    </div></div>
    <div class="box"><div class="head"><b>Topik oleh ${esc(p.username)}</b></div>
      ${topics.map(topicRow).join("") || '<div class="cell">Belum ada topik.</div>'}${pagerHTML(r, "#/member/" + encodeURIComponent(p.username))}</div>
    ${isAdmin && !own ? `<div class="box"><div class="head"><b>Admin — Grant POSKOIN</b></div><div class="body">
      <form id="grant-form"><label>Jumlah POSK untuk ${esc(p.username)} (negatif = tarik saldo)</label>
      <input type="number" id="grant-amount" value="10">
      <button class="btn primary" type="submit">Proses</button></form></div></div>` : ""}`;
  const bep = document.getElementById("btn-edit-profile");
  if (bep) bep.onclick = () => { const f = document.getElementById("profile-form"); f.style.display = f.style.display === "none" ? "block" : "none"; };
  const pfc = document.getElementById("pf-cancel");
  if (pfc) pfc.onclick = () => document.getElementById("profile-form").style.display = "none";
  const pf = document.getElementById("profile-form");
  if (pf) pf.onsubmit = async e => {
    e.preventDefault();
    const bio = document.getElementById("pf-bio").value.trim();
    try {
      if (DEMO) { const u = demoUser(username); u.bio = bio; store.me = {...me, bio}; }
      else { const r = await api("/profile", {method: "POST", body: {bio}}); store.me = {...me, bio: r.bio, avatar: r.avatar}; }
      flash("Profil disimpan 🎉");
      pageMember(username);
    } catch (err) { flash(err.message, true); }
  };
  const gf = document.getElementById("grant-form");
  if (gf) gf.onsubmit = async e => {
    e.preventDefault();
    const amount = parseInt(document.getElementById("grant-amount").value, 10);
    if (!amount) { flash("Jumlah tidak valid.", true); return; }
    try {
      if (DEMO) {
        const u = demoUser(username);
        if (!u) throw new Error("User tidak ditemukan");
        if (amount < 0 && (u.coins || 0) < -amount) throw new Error("Saldo user tidak cukup untuk ditarik segitu");
        u.coins = (u.coins || 0) + amount;
        demoDB.coinTx.push(amount > 0
          ? {from: me.username, to: username, amount, type: "grant", note: "Grant dari admin " + me.username, created: new Date().toISOString()}
          : {from: username, to: null, amount: -amount, type: "grant", note: "Ditarik oleh admin " + me.username, created: new Date().toISOString()});
      } else await api("/coin", {method: "POST", body: {action: "grant", to: username, amount}});
      flash("Grant " + amount + " POSK ke " + username + " berhasil.");
      pageMember(username);
    } catch (err) { flash(err.message, true); }
  };
}
async function pageKoin() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya buat lihat POSKOIN."); return; }
  let balance = me.coins ?? 0, history = [];
  if (DEMO) {
    const u = demoUser(me.username);
    balance = u ? (u.coins ?? 0) : balance;
    history = demoDB.coinTx.filter(x => x.from === me.username || x.to === me.username).slice().reverse();
  } else {
    const r = await api("/coin");
    balance = r.balance; history = r.history;
    store.me = {...me, coins: balance};
    renderNav();
  }
  const label = {welcome: "Bonus warga baru", reward: "Reward aktivitas", tip: "Tip warga", grant: "Grant admin", shop: "Belanja avatar", node: "Buka Pos Jaga", unlock: "Buka konten berbayar", fee: "Biaya pos"};
  const rows = history.map(x => {
    const incoming = x.to === me.username;
    const other = x.type === "tip" ? (incoming ? "dari " + esc(x.from || "") : "ke " + esc(x.to || "")) : "";
    return `<div class="cell"><div style="min-width:0">
      <b>${esc(label[x.type] || x.type)}</b> ${other}
      ${x.note ? `<div class="meta">${esc(x.note)}</div>` : ""}
      <div class="meta">${ago(x.created)}</div></div>
      <div class="${incoming ? "tx-pos" : "tx-neg"}" style="margin-left:auto;align-self:center">${incoming ? "+" : "−"}${x.amount} POSK</div></div>`;
  }).join("");
  $view.innerHTML = `
    <div class="box"><div class="head"><b>POSKOIN Saya</b></div><div class="body">
      <div style="display:flex;align-items:center;gap:10px"><span class="coin-badge" style="width:34px;height:34px;font-size:19px">P</span>
      <span class="coin-big">${Number(balance)}</span><span class="muted">POSK — koin internal POSKO</span></div>
    </div></div>
    <div class="box"><div class="head"><b>Cara Dapat & Pakai POSK</b></div><div class="body muted" style="font-size:13px">
      Dapat: bonus warga baru +20 · bikin topik +5 · balasan (min. 10 karakter) +2 — reward aktivitas dibatasi maks 20 POSK/hari biar nggak difarming.<br>
      Pakai: kasih tip ke penulis topik/balasan yang kamu suka lewat tombol "Kasih POSK". POSK bersifat internal, tidak bisa dicairkan jadi uang.
    </div></div>
    <div class="box"><div class="head"><b>Riwayat Transaksi</b></div>
      ${rows || '<div class="cell">Belum ada transaksi.</div>'}</div>`;
}
async function pageSearch(q, page = 1) {
  const r = await topicList({q}, page);
  const topics = r.topics;
  $view.innerHTML = `<div class="box"><div class="head">Hasil pencarian: <b>${esc(q)}</b></div>
    ${topics.map(topicRow).join("") || '<div class="cell">Tidak ada topik yang cocok.</div>'}${pagerHTML(r, "#/search/" + encodeURIComponent(q))}</div>`;
}

/* ---------- router ---------- */

async function pageKoleksi() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya buat lihat Koleksi Tema."); return; }
  let topics = [];
  if (DEMO) topics = demoDB.topics.filter(t => (demoDB.favs || []).includes(t.id));
  else { const r = await api("/fav"); topics = r.topics || []; }
  $view.innerHTML = `<div class="box"><div class="head"><b>Koleksi Tema</b><div class="muted">Topik yang kamu simpan. Buka sebuah topik lalu tap tombol Koleksi buat menambah.</div></div>
    ${topics.map(topicRow).join("") || '<div class="cell">Belum ada topik di koleksimu.</div>'}</div>`;
}
function demoTimeline() {
  const me = store.me, ev = [];
  const tById = id => demoDB.topics.find(x => x.id === id);
  demoDB.topics.filter(t => t.author === me.username).forEach(t => ev.push({kind: "topic", ts: t.created, topic: t.id, title: t.title}));
  demoDB.replies.filter(r => r.author === me.username).forEach(r => { const t = tById(r.topic); ev.push({kind: "reply", ts: r.created, topic: r.topic, title: t ? t.title : "", snippet: (r.content || "").slice(0, 90)}); });
  const mine = demoDB.topics.filter(t => t.author === me.username).map(t => t.id);
  demoDB.replies.filter(r => mine.includes(r.topic) && r.author !== me.username).forEach(r => { const t = tById(r.topic); ev.push({kind: "reply_in", ts: r.created, topic: r.topic, title: t ? t.title : "", author: r.author, snippet: (r.content || "").slice(0, 90)}); });
  (demoDB.coinTx || []).filter(x => x.from === me.username || x.to === me.username).forEach(x => ev.push({kind: "coin", ts: x.created, amount: x.amount, type: x.type, note: x.note || "", from: x.from, to: x.to}));
  return ev.sort((a, b) => (a.ts < b.ts ? 1 : -1)).slice(0, 60);
}
async function pageTimeline() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya buat lihat Garis Waktu."); return; }
  let events = [];
  if (DEMO) events = demoTimeline();
  else { const r = await api("/timeline"); events = r.events || []; }
  const labels = {welcome: "Bonus warga baru", reward: "Reward aktivitas", tip: "Tip warga", grant: "Grant admin", shop: "Belanja avatar", node: "Buka Pos Jaga", unlock: "Buka konten berbayar", fee: "Biaya pos"};
  const row = e => {
    let html = "";
    if (e.kind === "topic") html = `kamu membuat topik <a href="#/topic/${esc(e.topic)}"><b>${esc(e.title)}</b></a>`;
    else if (e.kind === "reply") html = `kamu membalas di <a href="#/topic/${esc(e.topic)}"><b>${esc(e.title)}</b></a>${e.snippet ? `<div class="muted">&ldquo;${esc(e.snippet)}&rdquo;</div>` : ""}`;
    else if (e.kind === "reply_in") html = `<a href="#/member/${esc(e.author)}"><b>${esc(e.author)}</b></a> membalas topikmu <a href="#/topic/${esc(e.topic)}"><b>${esc(e.title)}</b></a>${e.snippet ? `<div class="muted">&ldquo;${esc(e.snippet)}&rdquo;</div>` : ""}`;
    else if (e.kind === "coin") {
      const masuk = e.to === me.username;
      let s = labels[e.type] || e.type;
      if (e.type === "tip") s += masuk ? " dari " + (e.from || "") : " ke " + (e.to || "");
      if (e.note) s += " — " + e.note;
      html = `POSKOIN ${masuk ? "masuk" : "keluar"} <b>${masuk ? "+" : "-"}${e.amount} POSK</b> · ${esc(s)}`;
    }
    return `<div class="cell"><div style="min-width:0">${html}<div class="meta">${ago(e.ts)}</div></div></div>`;
  };
  $view.innerHTML = `<div class="box"><div class="head"><b>Garis Waktu</b><div class="muted">Aktivitasmu di POSKO.</div></div>
    ${events.map(row).join("") || '<div class="cell">Belum ada aktivitas. Buat topik atau balas topik buat memulai.</div>'}</div>`;
}

/* ---------- Editor Avatar Aset ---------- */
let avState = null;
let _avaManifest = null;
async function loadAvaManifest() {
  if (_avaManifest) return _avaManifest;
  const r = await fetch(AVA_CDN + "manifest.json?v=4");
  if (!r.ok) throw new Error("Gagal memuat katalog avatar (HTTP " + r.status + ")");
  const man = await r.json();
  try {
    const rt = await fetch("https://api.github.com/repos/xhamzar/posko-stickers/git/trees/main?recursive=1");
    if (rt.ok) {
      const j = await rt.json();
      const have = new Set();
      Object.entries(man.items || {}).forEach(([c, arr]) => arr.forEach(it => have.add(c + "/" + it.id)));
      for (const x of (j.tree || [])) {
        if (x.type !== "blob") continue;
        const m = x.path.match(/^avatar\/([a-z]+)\/([a-z0-9_]+)\.png$/);
        if (m && man.items[m[1]] && !have.has(m[1] + "/" + m[2])) {
          man.items[m[1]].push({id: m[2], file: m[1] + "/" + m[2] + ".png", price: 0});
          have.add(m[1] + "/" + m[2]);
        }
      }
    }
  } catch (e) {}
  _avaManifest = man;
  return man;
}
async function pageAvatar() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya buat ganti avatar."); return; }
  document.title = "Avatar — POSKO";
  $view.innerHTML = `<div class="box"><div class="body muted">Memuat katalog avatar…</div></div>`;
  let man;
  try { man = await loadAvaManifest(); }
  catch (e) { $view.innerHTML = `<div class="flash error">${esc(e.message)}</div>`; return; }
  let cfg = avaParse(me.avatar);
  if (!DEMO) {
    try { const p = await api("/profile?user=" + encodeURIComponent(me.username)); cfg = avaParse(p.avatar); } catch (e) {}
  }
  avState = {cfg, man, tab: "hair"};
  renderAvatarEditor();
}
function avaStageHtml(cfg) {
  return cfg.border
    ? `<span class="avt-cardbox">${avaCard(cfg)}</span>`
    : `<span class="avt-stagebox">${avaChar(cfg)}</span>`;
}
function renderAvatarEditor() {
  const st = avState, me = store.me;
  if (!st) return;
  const cats = ((st.man.categories && st.man.categories.length)
    ? st.man.categories : AVA_CATS.map(([key, label]) => ({key, label})))
    .filter(c => !AVA_DISABLED.includes(c.key));
  for (const dc of AVA_DISABLED) delete st.cfg[dc];
  if (!cats.some(c => c.key === st.tab)) st.tab = cats.length ? cats[0].key : "body";
  const items = (st.man.items[st.tab] || []).slice()
    .sort((a, b) => a.id.localeCompare(b.id, undefined, {numeric: true}));
  const cur = st.cfg[st.tab];
  const optional = !AVA_CORE.includes(st.tab);
  $view.innerHTML = `<div class="box"><div class="head"><b>Avatar</b>
    <div class="muted">Rakit avatarmu dari potongan aset POSKO — badan, wajah, rambut, pakaian, sampai peliharaan &amp; bingkai kartu profil. Tab <b>Model</b> berisi karakter jadi siap pakai. Semua item masih <b>GRATIS</b> selama masa tes; nanti sebagian bisa jadi item POSKOIN. Saldo kamu: <b>${me.coins ?? 0} POSK</b>.</div></div>
    <div class="body">
      <div class="av-stage">${avaStageHtml(st.cfg)}</div>
      <div class="av-actions">
        <button class="btn" id="av-random" type="button">Acak</button>
        <button class="btn primary" id="av-save" type="button">Simpan Avatar</button>
        <a class="btn" href="#/member/${esc(me.username)}">Profil Saya</a>
      </div>
      <div class="av-tabs">${cats.map(c => `<button type="button" class="btn ${st.tab === c.key ? "primary" : ""}" data-avtab="${esc(c.key)}">${esc(c.label)}</button>`).join("")}</div>
      <div class="av-grid">
        ${optional ? `<button type="button" class="av-opt${!cur ? " sel" : ""}" data-avid=""><span class="av-none">Tidak<br>pakai</span></button>` : ""}
        ${items.map(it => `<button type="button" class="av-opt${cur === it.id ? " sel" : ""}" data-avid="${esc(it.id)}" title="${esc(it.id)}">
          <span class="av-thumbwrap"><img src="${avaImg(st.tab, it.id)}" alt="${esc(it.id)}" loading="lazy"></span>
          <span class="av-opt-name">${esc(it.id.replace(/_/g, " "))}</span>
          ${it.price > 0 ? `<span class="av-price">${it.price} POSK</span>` : ""}
        </button>`).join("")}
      </div>
      <div class="muted" style="margin-top:8px">${items.length} pilihan di kategori ini.</div>
    </div></div>`;
  $view.querySelectorAll("[data-avtab]").forEach(b => b.onclick = () => { st.tab = b.dataset.avtab; renderAvatarEditor(); });
  $view.querySelectorAll("[data-avid]").forEach(b => b.onclick = () => {
    const id = b.dataset.avid;
    if (st.tab === "model") { st.cfg = id ? {model: id} : {}; }
    else { delete st.cfg.model; if (id) st.cfg[st.tab] = id; else delete st.cfg[st.tab]; }
    renderAvatarEditor();
  });
  $view.querySelector("#av-random").onclick = () => {
    const pick = arr => arr[Math.floor(Math.random() * arr.length)];
    delete st.cfg.model;
    for (const c of cats) {
      if (c.key === "model") continue;
      const arr = st.man.items[c.key] || [];
      if (!arr.length) continue;
      if (AVA_CORE.includes(c.key)) st.cfg[c.key] = pick(arr).id;
      else if (Math.random() < 0.5) st.cfg[c.key] = pick(arr).id;
      else delete st.cfg[c.key];
    }
    renderAvatarEditor();
  };
  $view.querySelector("#av-save").onclick = async () => {
    try {
      if (DEMO) {
        store.me = {...store.me, avatar: "a:" + JSON.stringify(st.cfg)};
      } else {
        const p = await api("/profile", {method: "POST", body: {action: "custom", config: st.cfg}});
        store.me = {...store.me, avatar: p.avatar, coins: p.coins};
      }
      renderNav(); renderSide();
      flash("Avatar tersimpan.");
    } catch (err) { flash(err.message, true); }
  };
}
async function pageNotif() {
  const me = store.me;
  if (!me) { location.hash = "#/login"; flash("Masuk dulu ya buat lihat Notifikasi."); return; }
  let items = [];
  if (DEMO) {
    const tag = "@" + me.username;
    const scan = (author, topic, title, content, created) => { if (author !== me.username && (content || "").includes(tag)) items.push({from: author, topic, title, snippet: (content || "").slice(0, 90), created, read: false}); };
    demoDB.topics.forEach(t => scan(t.author, t.id, t.title, t.content, t.created));
    demoDB.replies.forEach(r => { const t = demoDB.topics.find(x => x.id === r.topic); scan(r.author, r.topic, t ? t.title : "", r.content, r.created); });
    items.sort((a, b) => (a.created < b.created ? 1 : -1));
  } else {
    const r = await api("/notif");
    items = r.items || [];
  }
  $view.innerHTML = `<div class="box"><div class="head"><b>Notifikasi</b><div class="muted">Siapa yang menyebutmu (@${esc(me.username)}) di topik atau balasan.</div></div>
    ${items.map(n => `<div class="cell${n.read ? "" : " notif-unread"}"><div style="min-width:0">
      <a href="#/member/${esc(n.from)}"><b>${esc(n.from)}</b></a> menyebutmu${n.title ? ` di <a href="#/topic/${esc(n.topic)}"><b>${esc(n.title)}</b></a>` : ""}
      ${n.snippet ? `<div class="muted">&ldquo;${esc(n.snippet)}&rdquo;</div>` : ""}
      <div class="meta">${ago(n.created)}${n.read ? "" : " · baru"}</div></div></div>`).join("") || '<div class="cell">Belum ada notifikasi. Santai, pos aman.</div>'}</div>`;
  if (!DEMO) {
    try { const r2 = await api("/notif", {method: "POST", body: {all: true}}); store.unread = r2.unread ?? 0; renderNav(); } catch (e) {}
  }
}
function pageAbout() {
  document.title = "Tentang — POSKO";
  $view.innerHTML = `<div class="box doc">
    <div class="cell" style="font-size:16px"><b>Tentang POSKO</b></div>
    <div class="doc-body">
      <p>POSKO adalah komunitas warga internet Indonesia yang suka ngobrol, berbagi, dan bikin sesuatu.</p>

      <p>POSKO (Pusat Obrolan &amp; Sharing Komunitas Online) adalah forum ala V2EX: obrolan dibagi ke dalam <b>Pos Jaga</b> (node) sesuai topik — dari teknologi, AI, sampai obrolan santai. POSKO dibuka pada <b>22 Oktober 2026</b> dan masih muda, masih tumbuh bersama warganya.</p>

      <p>Harapannya, POSKO bisa jadi bagian dari keseharian warga: tempat berbagi hal menarik yang sedang dikerjakan, bertukar pikiran, menemukan teman, bahkan peluang baru. Dan yang paling penting, dalam semua itu, tetap baik kepada sesama warga.</p>

      <h3>Yang kami jaga di sini</h3>
      <p>Supaya suasananya tetap enak, POSKO punya nilai-nilai yang dipegang warganya:</p>
      <ul>
        <li>Di sini kami menghargai karya orang lain — kalau membagikan tulisan orang, cukup tautannya, jangan disalin utuh. Pengecualiannya cuma kalau itu karyamu sendiri.</li>
        <li>Di sini kami tidak membagikan cara mendapatkan konten bajakan.</li>
        <li>Di sini kami tidak membahas cara mengakali sistem atau celah buat curang.</li>
        <li>Di sini kami senang sama hal-hal yang indah dan rapi — dari tulisan sampai karya visual.</li>
        <li>Di sini kami menghormati karya orisinal.</li>
        <li>Di sini kami menolak balasan tanpa isi seperti “up”, “first”, “hadir”, atau “nyimak” doang — kalau nimbrung, bawa isi.</li>
        <li>Di sini dilarang serangan pribadi, ujaran kebencian, kekerasan, penghinaan, dan membongkar privasi orang lain.</li>
        <li>Kalau menulis di sini, ingat bahwa tulisanmu tunduk pada hukum yang berlaku di tempatmu.</li>
        <li>Kalau memakai AI, pastikan isinya benar dan bermanfaat, bukan asal tempel — dan jangan mengaku-ngaku karya orang sebagai karyamu.</li>
        <li>Kalau mengajari orang lain, pastikan hal itu memang sudah kamu lakukan sendiri dan kamu kuasai.</li>
      </ul>

      <h3>Apa yang bisa dilakukan di POSKO</h3>
      <ul>
        <li><b>Ngobrol di Pos Jaga:</b> pilih pos sesuai topik, atau buka Pos Jaga sendiri dan jadi Penjaganya.</li>
        <li><b>Berbagi topik &amp; balasan</b> dengan tag, mention, stiker, dan unggah gambar langsung dari formulir.</li>
        <li><b>POSKOIN (POSK):</b> koin warga buat reward aktivitas, tip ke warga lain, dan membuka konten berbayar <code>[jual]</code>.</li>
        <li><b>Avatar aset &amp; stiker:</b> berdandan dengan koleksi aset dan stiker resmi POSKO.</li>
        <li><b>Koleksi, Garis Waktu, dan Notifikasi</b> buat mengikuti topik, aktivitasmu, dan sapaan dari warga lain.</li>
      </ul>
      <p>Panduan lengkapnya ada di halaman <a href="#/dokumen"><b>Dokumen</b></a>.</p>

      <hr>
      <p class="muted">POSKO dibangun dan dijaga oleh admin <a href="#/member/driyan"><b>driyan</b></a> bersama para warganya. Selalu siaga, selalu ada obrolan.</p>
      <p class="muted">Terakhir diperbarui 24 Oktober 2026.</p>
    </div>
  </div>`;
}
function pageDokumen() {
  document.title = "Dokumen — POSKO";
  $view.innerHTML = `<div class="box doc">
    <div class="cell" style="font-size:16px"><b>Panduan POSKO</b></div>
    <div class="doc-body">
      <p>POSKO (Pusat Obrolan &amp; Sharing Komunitas Online) adalah forum tempat warga ngobrol, berbagi, dan bertransaksi memakai koin internal bernama <b>POSKOIN (POSK)</b>. Halaman ini merangkum semua cara memakai POSKO.</p>

      <h3>1. POSKOIN — Koin Warga</h3>
      <ul>
        <li><b>Bonus pendaftaran +20 POSK</b> untuk setiap warga baru.</li>
        <li><b>Reward aktivitas:</b> membuat topik <b>+5 POSK</b>, menulis balasan (min. 10 karakter) <b>+2 POSK</b>. Total reward aktivitas dibatasi <b>20 POSK per hari</b>.</li>
        <li><b>Tip:</b> kirim POSK ke warga lain dari tombol Kasih POSK di topiknya (1–1.000 POSK per kirim).</li>
        <li>Saldo, riwayat, dan pemberian tip bisa dilihat di halaman <a href="#/koin"><b>POSKOIN Saya</b></a>. Aktivitasmu juga tercatat di <a href="#/timeline"><b>Garis Waktu</b></a>.</li>
      </ul>

      <h3>2. Menulis Topik &amp; Balasan</h3>
      <ul>
        <li>Tempel tautan <b>YouTube</b> — otomatis jadi thumbnail video yang bisa diputar.</li>
        <li>Tempel tautan <b>gambar</b> (diakhiri .jpg/.png/.gif/.webp) — otomatis tampil sebagai gambar. Atau pakai tombol <b>Gambar</b> di formulir untuk mengunggah langsung (otomatis dikompres).</li>
        <li>Tombol <b>Stiker</b> di formulir membuka pack stiker resmi POSKO (dari CDN stiker POSKO di GitHub) — klik satu stiker dan ia masuk ke tulisanmu, tampil kecil khas stiker. Pack terdeteksi otomatis dari repo stiker: file gambar (GIF/PNG/JPG/WebP) baru di folder pack langsung muncul di picker.</li>
        <li>Tulis <code>@username</code> untuk menyebut warga — yang disebut menerima <b>notifikasi</b> (angka merah di avatar).</li>
        <li>Tulisanmu bisa <b>diedit / dihapus</b> lewat ikon di bawahnya. Tulisan orang lain tidak bisa diubah siapa pun.</li>
      </ul>

      <h3>3. Konten Berbayar — Kode [jual]</h3>
      <p>Sebagian isi tulisan bisa dijual: kurung bagian yang berbayar dengan kode <code>[jual=HARGA]</code> … <code>[/jual]</code>. Contoh:</p>
      <div class="doc-pre">Bagian ini gratis, bisa dibaca semua orang.
[jual=50]
Isi rahasia ada di sini: tautan unduhan, kode,
atau kalimat khusus buat pembeli.
[/jual]
Penutup juga gratis.</div>
      <ul>
        <li>Harga bebas <b>1 – 100.000 POSK</b> per blok. Satu tulisan boleh punya beberapa blok dengan harga berbeda; tiap blok dibeli terpisah.</li>
        <li>Yang belum membeli hanya melihat kotak <b>Konten Berbayar</b> — isinya <b>tidak dikirim sama sekali</b> ke browser mereka dan tidak muncul di daftar topik maupun pencarian.</li>
        <li>Sekali dibeli, konten <b>terbuka selamanya</b> untuk pembeli itu.</li>
        <li>Penulis menerima <b>90%</b> harga; <b>10%</b> menjadi biaya pos untuk POSKO (hangus, menjaga ekonomi koin tetap sehat).</li>
        <li>Penjualan dan pembelian tercatat di riwayat POSKOIN kedua pihak.</li>
      </ul>

      <h3>4. Pos &amp; Penjaga Pos</h3>
      <ul>
        <li>Topik dikelompokkan dalam <b>Pos</b> (seperti kategori). Lihat semua pos di <a href="#/pos"><b>Peta Pos</b></a> dan tekan <b>Ikuti</b> agar pos favoritmu muncul di sidebar "Pos Saya".</li>
        <li>Warga bisa <b>membuka Pos sendiri seharga 200 POSK</b> (admin gratis) dan otomatis menjadi <b>Penjaga</b> pos itu.</li>
        <li>Penjaga berhak <b>pin / kunci / hapus topik</b> dan <b>hapus balasan</b> di posnya sendiri — tapi tidak bisa mengedit tulisan orang lain.</li>
      </ul>

      <h3>5. Avatar</h3>
      <ul>
        <li><b>Avatar</b> dirakit dari potongan aset (badan, wajah, rambut, pakaian, peliharaan, bingkai) lewat menu Profil → Edit Profil → <b>Ganti Avatar</b>. Semua potongan masih gratis selama masa tes.</li>
        <li>Sebagian gaya rambut, pakaian, aksesoris, hewan peliharaan, dan bingkai bersifat premium dan dibeli permanen memakai POSK (mulai 30 POSK).</li>
      </ul>

      <h3>6. Koleksi &amp; Notifikasi</h3>
      <ul>
        <li>Ikon <b>penanda buku</b> di topik menyimpannya ke <a href="#/koleksi"><b>Koleksi Tema</b></a> untuk dibaca lagi nanti.</li>
        <li><b>Notifikasi</b> muncul saat kamu disebut (@mention) — buka lewat menu avatar.</li>
      </ul>

      <h3>7. Aturan Main</h3>
      <ul>
        <li>Jaga obrolan tetap sopan; dilarang spam, SARA, dan pornografi.</li>
        <li>Admin &amp; Penjaga Pos berhak mengunci / menghapus tulisan yang melanggar.</li>
        <li>Isi konten berbayar adalah tanggung jawab penulisnya. Jual hanya konten yang memang hakmu untuk dijual.</li>
      </ul>
      <p class="muted" style="margin-top:16px">Selamat bergabung di POSKO — semoga betah di pos!</p>
    </div>
  </div>`;
  window.scrollTo(0, 0);
}

/* Kerangka "Memuat…" selama halaman baru diambil — cuma saat rutenya benar-benar
   ganti; render ulang halaman yang sama (mis. buka konten berbayar) tidak diganggu. */
let _curRoute = "";
function skeletonHtml() {
  const row = `<div class="cell"><div class="skl skl-av"></div><div style="flex:1;min-width:0"><div class="skl skl-line" style="width:65%"></div><div class="skl skl-line" style="width:40%"></div></div></div>`;
  return `<div class="box"><div class="head"><span class="skl skl-line" style="width:30%;margin:2px 0"></span></div>${row.repeat(3)}</div><div class="muted" style="text-align:center;font-size:12px;margin-top:8px">Memuat…</div>`;
}
async function route() {
  document.getElementById("flash").innerHTML = "";
  const h = location.hash.replace(/^#\/?/, "");
  const [hpath, hquery] = h.split("?");
  const [page, arg] = hpath.split("/");
  const pg = Math.max(1, parseInt(new URLSearchParams(hquery || "").get("page"), 10) || 1);
  const rkey = page + "/" + (arg || "") + "/p" + pg;
  if (rkey !== _curRoute) { _curRoute = rkey; $view.innerHTML = skeletonHtml(); }
  try {
    if (!page) await pageHome(pg);
    else if (page === "node") await pageNode(decodeURIComponent(arg || ""), pg);
    else if (page === "topic") await pageTopic(decodeURIComponent(arg || ""));
    else if (page === "new") await pageNew();
    else if (page === "login") pageLogin();
    else if (page === "register") pageRegister();
    else if (page === "member") await pageMember(decodeURIComponent(arg || ""), pg);
    else if (page === "koin") await pageKoin();
    else if (page === "koleksi") await pageKoleksi();
    else if (page === "timeline") await pageTimeline();
    else if (page === "notif") await pageNotif();
    else if (page === "avatar") await pageAvatar();
    else if (page === "pos") await pagePos();
    else if (page === "dokumen") pageDokumen();
    else if (page === "about") pageAbout();
    else if (page === "search") await pageSearch(decodeURIComponent(arg || ""), pg);
    else if (page === "tag") await pageTag(decodeURIComponent(arg || ""), pg);
    else await pageHome(pg);
  } catch (e) { $view.innerHTML = `<div class="flash error">${esc(e.message)}</div>`; }
  if (window.__flash) { flash(window.__flash); window.__flash = null; }
  renderSide();
  refreshCoins();
  refreshUnread();
}
document.getElementById("search-form").onsubmit = e => {
  e.preventDefault();
  location.hash = "#/search/" + encodeURIComponent(document.getElementById("search-input").value.trim());
};
document.getElementById("search-toggle").onclick = () => {
  const f = document.getElementById("search-form");
  f.classList.toggle("open");
  if (f.classList.contains("open")) document.getElementById("search-input").focus();
};
document.addEventListener("click", e => {
  const m = document.getElementById("user-menu");
  if (m && !m.hidden && !e.target.closest("#nav-user")) m.hidden = true;
});
window.addEventListener("hashchange", () => {
  const m = document.getElementById("user-menu");
  if (m) m.hidden = true;
  document.getElementById("search-form").classList.remove("open");
  window.scrollTo(0, 0);
});
document.addEventListener("click", async e => {
  const b = e.target.closest("[data-unlock]");
  if (!b) return;
  const [kind, ref, idx, price] = b.dataset.unlock.split(":");
  if (!confirm("Buka konten berbayar ini seharga " + price + " POSK? (Penulis menerima " + (price - Math.floor(price / 10)) + " POSK, biaya pos 10%)")) return;
  try {
    const r = await api("/coin", {method: "POST", body: {action: "unlock", kind, id: ref, idx: +idx}});
    if (store.me && r.balance !== undefined) { store.me = {...store.me, coins: r.balance}; renderNav(); }
    flash("Konten terbuka. Selamat menikmati!");
    route();
  } catch (err) { flash(err.message, true); }
});
window.addEventListener("hashchange", route);
renderNav();
route();
