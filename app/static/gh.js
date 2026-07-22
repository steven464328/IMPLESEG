// ═══════════════════════════════════════════════════════════════
// EJ Soluciones · Gestión Humana (F-SGI-GH-12)
// Misma lógica y mismos formatos de PDF del sistema original,
// ahora hablando con la API propia en vez de Google Apps Script.
// ═══════════════════════════════════════════════════════════════

var API_INV = "/api/gh/inventario";
var API_ASN = "/api/gh/asignaciones";
var API_BAJ = "/api/gh/bajas";

var CATS = ['AIO', 'DESKTOP', 'LAPTOP', 'Portátil/Laptop', 'Teclado', 'Mouse', 'Pantalla/Monitor', 'Base refrigerante', 'Auriculares/Diadema', 'EPP - Casco', 'Herramienta manual', 'Otro'];
var ESTADOS = ['Nuevo', 'Bueno', 'Regular', 'Deteriorado', 'Dañado/Inservible'];
var AREAS = ['Comercial/Ventas', 'Operaciones', 'SST/HSEQ', 'Administración', 'Recursos Humanos', 'Tecnología', 'Logística', 'Dirección/Gerencia', 'Producción'];
var MOTIVOS = ['Deterioro / Daño irreparable', 'Obsolescencia tecnológica', 'Pérdida / Robo', 'Donación a entidad', 'Chatarrización', 'Fin de vida útil'];
var DISPS = ['Chatarrización', 'Donación a entidad externa', 'Destrucción controlada', 'Traslado interno', 'Venta como chatarra'];
var SW_LIST = ['Windows', 'Office', 'Antivirus', 'Lector PDF', 'CRM', 'VPN', 'ERP', 'Otros'];

var INV = [], ASN = [], BAJAS = [];
var VIEW = 'dash', LIST_F = 'todos', SEL = null;
var nE = {}, nItems = [], sigR = null, sigE = null;

function ge(id) { return document.getElementById(id); }
function ce(t, c) { var e = document.createElement(t); if (c) e.className = c; return e; }
function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function toast(m, ok) { var t = ge('toast'); t.textContent = m; t.style.borderColor = (ok === false) ? 'var(--danger)' : 'var(--accent)'; t.classList.add('show'); setTimeout(function () { t.classList.remove('show'); }, 3200); }
function todayISO() { var d = new Date(), m = d.getMonth() + 1, dd = d.getDate(); return d.getFullYear() + '-' + (m < 10 ? '0' + m : m) + '-' + (dd < 10 ? '0' + dd : dd); }
function resetNew() { nE = { nombre: '', cedula: '', cargo: '', area: AREAS[0] }; nItems = [{ herramienta: '', marca: '', serialOriginal: '', cantidad: 1, estado: 'Bueno', obs: '', fecha: todayISO() }]; sigR = null; sigE = null; }

async function apiGet(url) { var r = await fetch(url); if (!r.ok) throw new Error((await r.json()).detail || 'Error'); return r.json(); }
async function apiPost(url, body) { var r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); if (!r.ok) throw new Error((await r.json()).detail || 'Error'); return r.json(); }
async function apiPut(url, body) { var r = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); if (!r.ok) throw new Error((await r.json()).detail || 'Error'); return r.json(); }

// ---------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {
  resetNew();
  document.querySelectorAll('#ghSubNav .nav-item.sub').forEach(function (b) {
    b.onclick = function () { VIEW = b.getAttribute('data-v'); marcarSubNav(); render(); };
  });
  cargarTodo();
});

function marcarSubNav() {
  document.querySelectorAll('#ghSubNav .nav-item.sub').forEach(function (b) {
    b.classList.toggle('on', b.getAttribute('data-v') === (VIEW === 'detail' || VIEW === 'edit' ? 'list' : VIEW));
  });
}

async function cargarTodo(gotoView) {
  try {
    var [inv, asn, baj] = await Promise.all([apiGet(API_INV), apiGet(API_ASN), apiGet(API_BAJ)]);
    INV = inv; ASN = asn; BAJAS = baj;
  } catch (e) {
    toast('Error de conexión con el servidor', false);
  }
  if (gotoView) VIEW = gotoView;
  resetNew();
  marcarSubNav();
  render();
}

function render() {
  var app = ge('ghApp'); app.innerHTML = '';
  if (VIEW === 'dash') app.appendChild(vDash());
  if (VIEW === 'inv') app.appendChild(vInv());
  if (VIEW === 'new') app.appendChild(vNew());
  if (VIEW === 'list') app.appendChild(vList());
  if (VIEW === 'rec') app.appendChild(vRec());
  if (VIEW === 'detail') app.appendChild(vDetail());
  if (VIEW === 'baja') app.appendChild(vBajas());
  if (VIEW === 'edit') app.appendChild(vEdit());
}

// ---------------------------------------------------------------
// DASHBOARD
// ---------------------------------------------------------------
function vDash() {
  var el = ce('div');
  el.innerHTML = '<p class="gh-title">📊 Panel · Gestión Humana</p>';

  var total = ASN.length, act = ASN.filter(function (x) { return x.status !== 'devuelto'; }).length, dev = total - act;
  var empM = {}; ASN.filter(function (a) { return a.status !== 'devuelto'; }).forEach(function (a) { empM[a.cedula] = true; });

  var sg = ce('section', 'dashboard-grid');
  sg.innerHTML = statCard(total, 'Total actas') + statCard(act, 'Activas', 'ok') + statCard(dev, 'Devueltas', 'warn') + statCard(INV.length, 'Ítems en inventario') + statCard(Object.keys(empM).length, 'Colaboradores activos');
  el.appendChild(sg);

  var cr = ce('section', 'charts-row');
  var aM = {}; ASN.forEach(function (a) { aM[a.area || 'SIN ÁREA'] = (aM[a.area || 'SIN ÁREA'] || 0) + 1; });
  var p1 = ce('div', 'gh-card'); p1.innerHTML = '<div class="sh"><div class="sn">📍</div>Asignaciones por área</div>' + barChart(aM);
  var eM = {}; INV.forEach(function (i) { eM[i.categoria || 'SIN CATEGORÍA'] = (eM[i.categoria || 'SIN CATEGORÍA'] || 0) + 1; });
  var p2 = ce('div', 'gh-card'); p2.innerHTML = '<div class="sh"><div class="sn">📦</div>Inventario por categoría</div>' + barChart(eM);
  cr.appendChild(p1); cr.appendChild(p2); el.appendChild(cr);

  if (ASN.length) {
    var rc = ce('div', 'gh-card'); rc.innerHTML = '<div class="sh"><div class="sn">📌</div>Actividad reciente</div>';
    var rows = '';
    ASN.slice().reverse().slice(0, 8).forEach(function (a) {
      rows += '<tr><td><b>' + esc(a.nombre) + '</b><br><span style="color:var(--text-faint);font-size:10.5px">CC ' + esc(a.cedula) + '</span></td><td>' + esc(a.area || '—') + '</td><td style="text-align:center">' + (a.items || []).length + '</td><td style="font-size:11px;color:var(--text-dim)">' + esc(a.fecha) + '</td><td>' + badgeEstadoAsn(a.status) + '</td></tr>';
    });
    rc.innerHTML += '<table class="data-table"><thead><tr><th>Colaborador</th><th>Área</th><th>Equipos</th><th>Fecha</th><th>Estado</th></tr></thead><tbody>' + rows + '</tbody></table>';
    el.appendChild(rc);
  }
  return el;
}
function statCard(v, l, tone) { return '<div class="stat-card ' + (tone === 'ok' ? '' : tone === 'warn' ? 'stat-warning' : '') + '"><span class="stat-label">' + l + '</span><span class="stat-value">' + v + '</span></div>'; }
function barChart(dict) {
  var entries = Object.entries(dict); if (!entries.length) return '<p style="color:var(--text-faint);font-size:13px">Sin datos aún.</p>';
  var max = Math.max.apply(null, entries.map(function (e) { return e[1]; }));
  return '<div class="bar-chart">' + entries.map(function (e) {
    return '<div class="bar-row"><span class="label" title="' + esc(e[0]) + '">' + esc(e[0]) + '</span><div class="bar-track"><div class="bar-fill" style="width:' + (e[1] / max * 100) + '%"></div></div><span class="count">' + e[1] + '</span></div>';
  }).join('') + '</div>';
}
function badgeEstadoAsn(status) { return status === 'devuelto' ? '<span class="badge badge-neutral">DEVUELTO</span>' : '<span class="badge badge-ok">ACTIVO</span>'; }

// ---------------------------------------------------------------
// INVENTARIO
// ---------------------------------------------------------------
function vInv() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">📦 Inventario de herramientas</p>';
  var bA = ce('button', 'btn btn-primary'); bA.style.marginBottom = '16px'; bA.textContent = '+ Nuevo ítem';
  bA.onclick = function () { showInvForm(el); }; el.appendChild(bA);

  var rows = INV.map(function (it) {
    var color = it.cantidad_stock > 0 ? 'var(--accent)' : 'var(--danger)';
    return '<tr><td><b>' + esc(it.nombre) + '</b></td><td>' + esc(it.categoria || '—') + '</td><td>' + esc(it.marca || '—') + '</td><td>' + esc(it.modelo || '—') + '</td><td style="font-family:var(--font-mono);font-size:11.5px">' + esc(it.serial || '—') + '</td><td style="text-align:center;font-weight:700;color:' + color + '">' + it.cantidad_stock + '</td><td>' + esc(it.colaborador || '—') + '</td><td><button class="row-btn" onclick="showInvForm(document.getElementById(\'ghApp\'),' + it.id + ')">Editar</button></td></tr>';
  }).join('');

  var tw = ce('div', 'panel table-panel');
  tw.innerHTML = '<table class="data-table"><thead><tr><th>Nombre</th><th>Categoría</th><th>Marca</th><th>Modelo</th><th>Serial</th><th>Stock</th><th>Colaborador</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="8" class="empty-state">Sin ítems en inventario</td></tr>') + '</tbody></table>';
  el.appendChild(tw);
  return el;
}

function showInvForm(parent, itemId) {
  var ex = parent.querySelector('.inv-fc'); if (ex) ex.remove();
  var item = itemId ? INV.find(function (i) { return i.id === itemId; }) : null;
  var f = ce('div', 'gh-card inv-fc');
  f.innerHTML = '<div class="sh"><div class="sn">' + (item ? '✏️' : '+') + '</div>' + (item ? 'Editar' : 'Agregar') + ' equipo/herramienta</div>' +
    '<div class="g4" style="margin-bottom:16px">' +
    '<label class="lbl-field">Nombre *<input id="fi-n" value="' + esc(item ? item.nombre : '') + '" placeholder="Ej: LAPTOP LENOVO 05"></label>' +
    '<label class="lbl-field">Categoría<select id="fi-c">' + CATS.map(function (c) { return '<option' + (item && item.categoria === c ? ' selected' : '') + '>' + esc(c) + '</option>'; }).join('') + '</select></label>' +
    '<label class="lbl-field">Marca<input id="fi-ma" value="' + esc(item ? item.marca : '') + '"></label>' +
    '<label class="lbl-field">Modelo<input id="fi-mo" value="' + esc(item ? item.modelo : '') + '"></label>' +
    '<label class="lbl-field">Serial<input id="fi-s" value="' + esc(item ? item.serial : '') + '"></label>' +
    '<label class="lbl-field">Descripción<input id="fi-d" value="' + esc(item ? item.descripcion : 'Equipo Impleseg') + '"></label>' +
    '<label class="lbl-field">Cantidad stock *<input type="number" id="fi-q" value="' + (item ? item.cantidad_stock : 1) + '" min="0"></label>' +
    '<label class="lbl-field">Colaborador asignado<input id="fi-co" value="' + esc(item ? item.colaborador : '') + '"></label>' +
    '</div><div style="display:flex;gap:10px"><button class="btn btn-primary" id="btn-sav-inv">Guardar</button><button class="btn btn-ghost" id="btn-can-inv">Cancelar</button></div>';
  f.querySelector('#btn-can-inv').onclick = function () { f.remove(); };
  f.querySelector('#btn-sav-inv').onclick = async function () {
    var payload = {
      nombre: ge('fi-n').value.trim(), categoria: ge('fi-c').value, marca: ge('fi-ma').value.trim(),
      modelo: ge('fi-mo').value.trim(), serial: ge('fi-s').value.trim(), descripcion: ge('fi-d').value.trim(),
      cantidad_stock: parseInt(ge('fi-q').value) || 0, colaborador: ge('fi-co').value.trim(),
    };
    if (!payload.nombre) return toast('El nombre es obligatorio', false);
    try {
      if (item) await apiPut(API_INV + '/' + item.id, payload);
      else await apiPost(API_INV, payload);
      toast('Ítem guardado ✓'); await cargarTodo('inv');
    } catch (e) { toast(e.message, false); }
  };
  var tw = parent.querySelector('.table-panel');
  parent.insertBefore(f, tw);
}

// ---------------------------------------------------------------
// NUEVA ASIGNACIÓN
// ---------------------------------------------------------------
function vNew() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">➕ Nueva acta de asignación (F-SGI-GH-12)</p>';

  var c1 = ce('div', 'gh-card');
  c1.innerHTML = '<div class="sh"><div class="sn">1</div>Datos del colaborador</div><div class="g2">' +
    '<label class="lbl-field">Nombre completo *<input id="n-nm" value="' + esc(nE.nombre) + '"></label>' +
    '<label class="lbl-field">Cédula *<input id="n-cc" value="' + esc(nE.cedula) + '"></label>' +
    '<label class="lbl-field">Cargo<input id="n-ca" value="' + esc(nE.cargo) + '"></label>' +
    '<label class="lbl-field">Área<select id="n-ar">' + AREAS.map(function (a) { return '<option' + (a === nE.area ? ' selected' : '') + '>' + esc(a) + '</option>'; }).join('') + '</select></label></div>';
  el.appendChild(c1);
  setTimeout(function () {
    ge('n-nm').oninput = function () { nE.nombre = this.value; };
    ge('n-cc').oninput = function () { nE.cedula = this.value; };
    ge('n-ca').oninput = function () { nE.cargo = this.value; };
    ge('n-ar').onchange = function () { nE.area = this.value; };
  }, 0);

  var c2 = ce('div', 'gh-card'); c2.innerHTML = '<div class="sh"><div class="sn">2</div>Herramientas y equipos</div>';
  var bAI = ce('button', 'btn btn-ghost'); bAI.style.marginBottom = '14px'; bAI.textContent = '+ Agregar herramienta';
  var iCont = ce('div'); c2.appendChild(bAI); c2.appendChild(iCont); el.appendChild(c2);
  bAI.onclick = function () { nItems.push({ herramienta: '', marca: '', serialOriginal: '', cantidad: 1, estado: 'Bueno', obs: '', fecha: todayISO() }); renderItems(iCont); };

  var c3 = ce('div', 'gh-card'); c3.innerHTML = '<div class="sh"><div class="sn">3</div>Firmas de conformidad</div>';
  var sg = ce('div', 'sig-grid');
  var sp1 = mkSig('🖊️ Firma de quien recibe (colaborador) *'); var sp2 = mkSig('🖊️ Firma de quien entrega (empresa)');
  sp1.on(function (d) { sigR = d; }); sp2.on(function (d) { sigE = d; });
  sg.appendChild(sp1.el); sg.appendChild(sp2.el); c3.appendChild(sg); el.appendChild(c3);

  var ff = ce('div', 'gh-ffooter');
  var bCl = ce('button', 'btn btn-ghost'); bCl.textContent = 'Limpiar todo';
  bCl.onclick = function () { resetNew(); render(); };
  var bSv = ce('button', 'btn btn-primary'); bSv.textContent = 'Guardar y generar PDF';
  bSv.onclick = async function () {
    nE.nombre = ge('n-nm').value.trim(); nE.cedula = ge('n-cc').value.trim(); nE.cargo = ge('n-ca').value.trim(); nE.area = ge('n-ar').value;
    if (!nE.nombre) return toast('El nombre es obligatorio', false);
    if (!nE.cedula) return toast('La cédula es obligatoria', false);
    var valid = nItems.filter(function (it) { return it.herramienta.trim(); });
    if (!valid.length) return toast('Agrega al menos un equipo', false);
    if (!sigR && !confirm('No has capturado la firma del colaborador.\n\n¿Guardar de todas formas como pendiente de firma?')) return;

    try {
      var r = await apiPost(API_ASN, { nombre: nE.nombre, cedula: nE.cedula, cargo: nE.cargo, area: nE.area, items: valid, firmaRecibe: sigR || '', firmaEntrega: sigE || '' });
      toast('Acta guardada: ' + r.codigo + ' ✓');
      printPDF(r);
      await cargarTodo('list');
    } catch (e) { toast(e.message, false); }
  };
  ff.appendChild(bCl); ff.appendChild(bSv); el.appendChild(ff);
  setTimeout(function () { renderItems(iCont); }, 0);
  return el;
}

function renderItems(cont, onChange) {
  cont.innerHTML = '';
  if (!nItems.length) nItems.push({ herramienta: '', marca: '', serialOriginal: '', cantidad: 1, estado: 'Bueno', obs: '', fecha: todayISO() });
  nItems.forEach(function (it, idx) {
    var box = ce('div', 'ibox');
    var hdr = ce('div', 'ibox-hdr'); hdr.innerHTML = '<b>Herramienta #' + (idx + 1) + '</b>';
    if (nItems.length > 1) {
      var del = ce('button', 'row-btn danger'); del.textContent = 'Quitar';
      del.onclick = function (e) { e.stopPropagation(); nItems.splice(idx, 1); renderItems(cont, onChange); if (onChange) onChange(); };
      hdr.appendChild(del);
    }
    box.appendChild(hdr);

    var invOptions = '<option value="">-- Vincular desde inventario (opcional) --</option>';
    INV.forEach(function (inv) {
      var key = inv.nombre + '|||' + (inv.serial || '');
      var sel = (inv.nombre === it.herramienta && (inv.serial || '') === (it.serialOriginal || '')) ? ' selected' : '';
      var stxt = inv.cantidad_stock > 0 ? 'Stock: ' + inv.cantidad_stock : '⚠ Sin stock';
      invOptions += '<option value="' + esc(key) + '"' + sel + '>' + esc(inv.nombre) + ' · ' + esc(inv.marca || '') + ' ' + esc(inv.modelo || '') + ' [S/N: ' + esc(inv.serial || 'N/A') + '] — ' + stxt + '</option>';
    });
    var selWrap = ce('div'); selWrap.style.marginBottom = '12px';
    selWrap.innerHTML = '<label class="lbl-field">🔗 Vincular desde inventario<select class="sel-i">' + invOptions + '</select></label>';
    box.appendChild(selWrap);

    var grid = ce('div', 'g2');
    grid.innerHTML =
      '<label class="lbl-field">Fecha *<input type="date" class="i-dt" value="' + esc(it.fecha || todayISO()) + '"></label>' +
      '<label class="lbl-field">Herramienta/equipo *<input class="i-hr" value="' + esc(it.herramienta) + '"></label>' +
      '<label class="lbl-field span-2">Marca / modelo / serial<input class="i-mr" value="' + esc(it.marca) + '"></label>' +
      '<label class="lbl-field">Cantidad<input type="number" class="i-qt" value="' + esc(it.cantidad) + '" min="1"></label>' +
      '<label class="lbl-field">Estado inicial<select class="i-es">' + ESTADOS.map(function (e) { return '<option' + (e === it.estado ? ' selected' : '') + '>' + e + '</option>'; }).join('') + '</select></label>' +
      '<label class="lbl-field span-2">Observaciones<input class="i-ob" value="' + esc(it.obs) + '"></label>';
    box.appendChild(grid);

    box.querySelector('.sel-i').onchange = function (ev) {
      var pts = ev.target.value.split('|||'), n = pts[0], s = pts[1] || ''; if (!n) return;
      var m = INV.find(function (i) { return i.nombre === n && (i.serial || '') === s; });
      if (m) { it.herramienta = m.nombre; it.serialOriginal = m.serial || ''; it.marca = (m.marca || '') + ' / ' + (m.modelo || '') + ' / S/N: ' + (m.serial || 'N/A'); box.querySelector('.i-hr').value = it.herramienta; box.querySelector('.i-mr').value = it.marca; if (onChange) onChange(); }
    };
    box.querySelector('.i-dt').onchange = function (ev) { it.fecha = ev.target.value; if (onChange) onChange(); };
    box.querySelector('.i-hr').onchange = function (ev) { it.herramienta = ev.target.value; if (onChange) onChange(); };
    box.querySelector('.i-mr').oninput = function (ev) { it.marca = ev.target.value; if (onChange) onChange(); };
    box.querySelector('.i-qt').onchange = function (ev) { it.cantidad = parseInt(ev.target.value) || 1; if (onChange) onChange(); };
    box.querySelector('.i-es').onchange = function (ev) { it.estado = ev.target.value; if (onChange) onChange(); };
    box.querySelector('.i-ob').oninput = function (ev) { it.obs = ev.target.value; if (onChange) onChange(); };
    cont.appendChild(box);
  });
}

// ---------------------------------------------------------------
// REGISTROS (listar / ver / editar)
// ---------------------------------------------------------------
function vList() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">📋 Registros de asignaciones</p>';
  var sb = ce('div', 'sbar');
  sb.innerHTML = '<input id="sl-src" placeholder="🔍 Buscar por nombre, cédula, área o código..."><div class="ftabs">' +
    '<button class="ftab' + (LIST_F === 'todos' ? ' on' : '') + '" data-f="todos">Todos</button>' +
    '<button class="ftab' + (LIST_F === 'activo' ? ' on' : '') + '" data-f="activo">Activas</button>' +
    '<button class="ftab' + (LIST_F === 'devuelto' ? ' on' : '') + '" data-f="devuelto">Recepciones</button></div>';
  el.appendChild(sb);
  var src = sb.querySelector('#sl-src'); var lc = ce('div'); el.appendChild(lc);

  function rl(f) {
    lc.innerHTML = ''; var flt = (f || '').toLowerCase();
    var fil = ASN.filter(function (a) {
      if (LIST_F === 'activo' && a.status === 'devuelto') return false;
      if (LIST_F === 'devuelto' && a.status !== 'devuelto') return false;
      if (!flt) return true;
      return (a.nombre || '').toLowerCase().indexOf(flt) > -1 || (a.cedula || '').indexOf(flt) > -1 || (a.area || '').toLowerCase().indexOf(flt) > -1 || (a.codigo || '').toLowerCase().indexOf(flt) > -1;
    }).slice().reverse();
    if (!fil.length) { lc.innerHTML = '<div class="empty-block">No encontramos resultados.</div>'; return; }
    fil.forEach(function (a) {
      var act = a.status !== 'devuelto';
      var ini = (a.nombre || '?').split(' ').slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase();
      var missingSig = !a.firma_recibe ? '<span class="badge badge-warn">Pendiente firma</span>' : '';
      var edited = (a.historial && a.historial.length) ? '<span class="badge badge-neutral">Editado</span>' : '';
      var card = ce('div', 'lcard');
      card.innerHTML = '<div class="lcard-l"><div class="avt">' + esc(ini) + '</div><div><div class="lcname">' + esc(a.nombre) + ' ' + badgeEstadoAsn(a.status) + ' ' + edited + ' ' + missingSig + '</div><div class="lcmeta">CC: ' + esc(a.cedula) + ' · ' + esc(a.area || '—') + ' · ' + esc(a.cargo || '—') + '</div><div class="lcmeta">📅 ' + esc(a.fecha) + (a.fecha_dev ? ' · 🔄 Devuelto: ' + esc(a.fecha_dev) : '') + ' · 🔧 ' + (a.items || []).length + ' equipo(s)</div><div class="lcmeta" style="font-family:var(--font-mono);font-size:10px">' + esc(a.codigo) + '</div></div></div><div class="lcard-a"><button class="btn btn-ghost">Ver</button><button class="btn btn-ghost">Editar/Firmar</button><button class="btn btn-primary">PDF</button></div>';
      var btns = card.querySelectorAll('button');
      btns[0].onclick = function () { SEL = a; VIEW = 'detail'; render(); };
      btns[1].onclick = function () { SEL = a; VIEW = 'edit'; render(); };
      btns[2].onclick = function () { printPDF(a); };
      lc.appendChild(card);
    });
  }
  sb.querySelectorAll('.ftab').forEach(function (btn) {
    btn.onclick = function () { LIST_F = btn.getAttribute('data-f'); sb.querySelectorAll('.ftab').forEach(function (b) { b.classList.remove('on'); }); btn.classList.add('on'); rl(src.value); };
  });
  rl(''); src.oninput = function () { rl(this.value); };
  return el;
}

function vDetail() {
  var el = ce('div'); var a = SEL;
  if (!a) { VIEW = 'list'; render(); return ce('div'); }
  var bB = ce('button', 'btn btn-ghost'); bB.style.marginBottom = '16px'; bB.textContent = '← Volver'; bB.onclick = function () { VIEW = 'list'; render(); }; el.appendChild(bB);

  var act = a.status !== 'devuelto';
  var info = ce('div', 'gh-card');
  info.innerHTML = '<div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:16px"><div><p style="font-size:20px;font-weight:700;font-family:var(--font-display)">' + esc(a.nombre) + '</p><p style="color:var(--text-dim);margin-top:4px">CC: ' + esc(a.cedula) + ' · ' + esc(a.cargo || '—') + ' · ' + esc(a.area || '—') + '</p><p style="font-size:11px;color:var(--text-faint);margin-top:6px;font-family:var(--font-mono)">' + esc(a.codigo) + ' · ' + esc(a.fecha) + '</p></div>' + badgeEstadoAsn(a.status) + '</div>';

  var rows = (a.items || []).map(function (it, idx) {
    return '<tr><td style="text-align:center">' + (idx + 1) + '</td><td><b>' + esc(it.herramienta) + '</b></td><td>' + esc(it.marca || '—') + '</td><td style="text-align:center">' + esc(it.cantidad) + '</td><td>' + esc(it.estado) + '</td><td>' + esc(it.observaciones || it.obs || '—') + '</td></tr>';
  }).join('');
  info.innerHTML += '<p style="font-weight:700;margin-bottom:10px">🔧 Equipos asignados</p><table class="data-table"><thead><tr><th>#</th><th>Herramienta</th><th>Marca/Serial</th><th>Cant.</th><th>Estado</th><th>Observaciones</th></tr></thead><tbody>' + rows + '</tbody></table>';

  if (!act && a.items_dev && a.items_dev.length) {
    var rowsDev = a.items_dev.map(function (it, idx) {
      return '<tr><td style="text-align:center">' + (idx + 1) + '</td><td><b>' + esc(it.herramienta) + '</b></td><td>' + esc(it.estado || '—') + '</td><td>' + esc(it.observaciones || '—') + '</td></tr>';
    }).join('');
    info.innerHTML += '<p style="font-weight:700;margin:18px 0 10px">📥 Devolución (' + esc(a.fecha_dev) + ')</p><table class="data-table"><thead><tr><th>#</th><th>Herramienta</th><th>Estado final</th><th>Observaciones</th></tr></thead><tbody>' + rowsDev + '</tbody></table>';
  }

  if (a.historial && a.historial.length) {
    info.innerHTML += '<p style="font-weight:700;margin:18px 0 10px">✏️ Historial de cambios</p>';
    a.historial.slice().reverse().forEach(function (h) {
      info.innerHTML += '<div class="hist-item"><div style="font-weight:700">🔧 ' + esc(h.herramienta || 'N/A') + '</div><div style="font-size:11.5px;color:var(--text-dim);margin-top:2px">' + esc(h.nota || '—') + '</div><div class="hist-fecha">' + esc(h.fecha || '') + '</div></div>';
    });
  }
  el.appendChild(info);

  var bP = ce('button', 'btn btn-primary'); bP.textContent = '🖨️ Imprimir / Guardar PDF'; bP.onclick = function () { printPDF(a); };
  var bEd = ce('button', 'btn btn-ghost'); bEd.style.marginLeft = '10px'; bEd.textContent = '✏️ Registrar novedad'; bEd.onclick = function () { VIEW = 'edit'; render(); };
  el.appendChild(bP); el.appendChild(bEd);
  return el;
}

function vEdit() {
  var a = SEL; if (!a) { VIEW = 'list'; render(); return ce('div'); }
  var el = ce('div');
  var bB = ce('button', 'btn btn-ghost'); bB.style.marginBottom = '16px'; bB.textContent = '← Volver al historial'; bB.onclick = function () { VIEW = 'list'; render(); }; el.appendChild(bB);

  var title = ce('p', 'gh-title'); title.innerHTML = '✏️ Editar acta: <b>' + esc(a.nombre) + '</b> <span style="font-family:var(--font-mono);font-size:14px;color:var(--text-dim)">' + esc(a.codigo) + '</span>'; el.appendChild(title);

  var alert = ce('div', 'gh-alert gh-alert-purple');
  alert.innerHTML = 'ℹ️ <b>Modo edición:</b> los equipos que retires se reintegran al inventario; los nuevos se descuentan automáticamente.'; el.appendChild(alert);

  var isMissingBaseSig = !a.firma_recibe;
  var sR_base = null, sE_base = null;
  if (isMissingBaseSig) {
    var cSigBase = ce('div', 'gh-card'); cSigBase.style.border = '2px dashed var(--warning)';
    cSigBase.innerHTML = '<div class="gh-alert gh-alert-orange">⏳ <b>Pendiente de firma inicial:</b> esta acta se guardó sin firma del colaborador. Captúrala aquí.</div><div class="sig-grid" id="base-sigs"></div>';
    var sgB = cSigBase.querySelector('#base-sigs');
    var bsp1 = mkSig('🖊️ Firma inicial colaborador *'); var bsp2 = mkSig('🖊️ Firma inicial empresa');
    bsp1.on(function (d) { sR_base = d; }); bsp2.on(function (d) { sE_base = d; });
    sgB.appendChild(bsp1.el); sgB.appendChild(bsp2.el);
    el.appendChild(cSigBase);
  }

  nItems = JSON.parse(JSON.stringify(a.items || [])).map(function (it) { return { herramienta: it.herramienta || '', marca: it.marca || '', serialOriginal: it.serialOriginal || '', cantidad: it.cantidad || 1, estado: it.estado || 'Bueno', obs: it.observaciones || it.obs || '', fecha: it.fecha || todayISO() }; });
  var originalItems = JSON.parse(JSON.stringify(nItems));
  var editE = { nombre: a.nombre, cedula: a.cedula, cargo: a.cargo, area: a.area };

  var c1 = ce('div', 'gh-card');
  c1.innerHTML = '<div class="sh"><div class="sn">1</div>Datos del colaborador</div><div class="g2">' +
    '<label class="lbl-field">Nombre *<input id="ed-nm" value="' + esc(editE.nombre) + '"></label>' +
    '<label class="lbl-field">Cédula *<input id="ed-cc" value="' + esc(editE.cedula) + '"></label>' +
    '<label class="lbl-field">Cargo<input id="ed-ca" value="' + esc(editE.cargo) + '"></label>' +
    '<label class="lbl-field">Área<select id="ed-ar">' + AREAS.map(function (ar) { return '<option' + (ar === editE.area ? ' selected' : '') + '>' + esc(ar) + '</option>'; }).join('') + '</select></label></div>';
  el.appendChild(c1);

  var c2 = ce('div', 'gh-card'); c2.innerHTML = '<div class="sh"><div class="sn">2</div>Herramientas (actualiza lo necesario)</div>';
  var bAI2 = ce('button', 'btn btn-ghost'); bAI2.style.marginBottom = '14px'; bAI2.textContent = '+ Agregar herramienta';
  var eCont = ce('div'); c2.appendChild(bAI2); c2.appendChild(eCont); el.appendChild(c2);
  bAI2.onclick = function () { nItems.push({ herramienta: '', marca: '', serialOriginal: '', cantidad: 1, estado: 'Bueno', obs: '', fecha: todayISO() }); renderItems(eCont, updateReasonsUI); updateReasonsUI(); };

  var c3 = ce('div', 'gh-card'); c3.id = 'reasons-container'; el.appendChild(c3);
  var tempReasons = {};
  function updateReasonsUI() {
    var rc = ge('reasons-container'); if (!rc) return;
    rc.querySelectorAll('.dyn-nota').forEach(function (ta) { tempReasons[ta.getAttribute('data-herr')] = ta.value; });
    var validEdits = nItems.filter(function (i) { return i.herramienta.trim(); });
    var removed = originalItems.filter(function (o) { return !validEdits.some(function (e) { return e.herramienta === o.herramienta; }); });
    var added = validEdits.filter(function (e) { return !originalItems.some(function (o) { return o.herramienta === e.herramienta; }); });
    var html = '<div class="sh"><div class="sn">3</div>Novedades y cambios</div>';
    if (!removed.length && !added.length) {
      html += '<div class="gh-alert" style="background:#0d9488;color:#a7f3d0">No se detectan retiros ni nuevos equipos. Si solo editas datos, justifica abajo (opcional si solo vas a firmar).</div><label class="lbl-field">Razón de la modificación<textarea class="dyn-nota" data-herr="Modificación General" rows="2"></textarea></label>';
    } else {
      removed.forEach(function (r) { html += '<div style="margin-bottom:12px;padding:12px;background:var(--danger-dim);border-left:3px solid var(--danger);border-radius:8px"><label class="lbl-field" style="color:var(--danger)">🔴 Equipo retirado: ' + esc(r.herramienta) + '<textarea class="dyn-nota" data-herr="' + esc(r.herramienta) + ' (Retirado)" rows="2" placeholder="Razón del retiro (obligatorio)"></textarea></label></div>'; });
      added.forEach(function (a2) { html += '<div style="margin-bottom:12px;padding:12px;background:var(--accent-dim);border-left:3px solid var(--accent);border-radius:8px"><label class="lbl-field" style="color:var(--accent)">🟢 Equipo asignado: ' + esc(a2.herramienta) + '<textarea class="dyn-nota" data-herr="' + esc(a2.herramienta) + ' (Asignado)" rows="2">Se asigna nuevo equipo.</textarea></label></div>'; });
    }
    rc.innerHTML = html;
    rc.querySelectorAll('.dyn-nota').forEach(function (ta) { if (tempReasons[ta.getAttribute('data-herr')]) ta.value = tempReasons[ta.getAttribute('data-herr')]; });
  }

  var c5 = ce('div', 'gh-card'); c5.innerHTML = '<div class="sh"><div class="sn">4</div>Firmas de constancia del cambio</div>';
  var sgE = ce('div', 'sig-grid'); var sER = null, sEE = null;
  var spE1 = mkSig('🖊️ Firma colaborador *'); var spE2 = mkSig('🖊️ Firma empresa *');
  spE1.on(function (d) { sER = d; }); spE2.on(function (d) { sEE = d; });
  sgE.appendChild(spE1.el); sgE.appendChild(spE2.el); c5.appendChild(sgE); el.appendChild(c5);

  if (a.historial && a.historial.length) {
    var c4 = ce('div', 'gh-card'); c4.innerHTML = '<div class="sh"><div class="sn">📋</div>Historial de cambios previos</div>';
    a.historial.slice().reverse().forEach(function (h) { var hi = ce('div', 'hist-item'); hi.innerHTML = '<div style="font-weight:700">🔧 ' + esc(h.herramienta || 'N/A') + '</div><div style="font-size:11.5px;color:var(--text-dim);margin-top:2px">' + esc(h.nota || '—') + '</div><div class="hist-fecha">' + esc(h.fecha || '') + '</div>'; c4.appendChild(hi); });
    el.appendChild(c4);
  }

  var ff = ce('div', 'gh-ffooter');
  var bCan = ce('button', 'btn btn-ghost'); bCan.textContent = 'Cancelar'; bCan.onclick = function () { VIEW = 'list'; render(); };
  var bSv = ce('button', 'btn btn-primary'); bSv.textContent = 'Guardar cambio y PDF';
  bSv.onclick = async function () {
    var nom = ge('ed-nm').value.trim(), ced = ge('ed-cc').value.trim(), car = ge('ed-ca').value.trim(), area = ge('ed-ar').value;
    if (!nom) return toast('El nombre es obligatorio', false);
    if (!ced) return toast('La cédula es obligatoria', false);
    var valid = nItems.filter(function (it) { return it.herramienta.trim(); });
    if (!valid.length) return toast('Debe haber al menos una herramienta', false);

    var notasNuevas = []; var missingReasons = false;
    ge('reasons-container').querySelectorAll('.dyn-nota').forEach(function (ta) {
      var val = ta.value.trim(); var herr = ta.getAttribute('data-herr');
      if (!val) missingReasons = true;
      notasNuevas.push({ herramienta: herr, nota: val });
    });
    var isGeneralMod = (notasNuevas.length === 1 && notasNuevas[0].herramienta === 'Modificación General');
    var hasNotes = notasNuevas.some(function (n) { return n.nota !== ''; });
    if (isGeneralMod && !hasNotes) missingReasons = false;
    if (missingReasons) return toast('Debes llenar todas las razones de cambio/retiro solicitadas', false);

    if (isMissingBaseSig && !sR_base && !confirm('Aún no registras la firma inicial. ¿Continuar sin ella?')) return;
    var hasChanges = (!isGeneralMod || hasNotes);
    if (hasChanges && !sER) return toast('La firma del colaborador es obligatoria para certificar este cambio', false);

    var payload = {
      nombre: nom, cedula: ced, cargo: car, area: area, items: valid,
      nuevosHistoriales: hasChanges ? notasNuevas.filter(function (n) { return n.nota !== ''; }).map(function (n) { return { herramienta: n.herramienta, nota: n.nota, firmaR: sER, firmaE: sEE }; }) : [],
    };
    if (isMissingBaseSig) { payload.firmaR_base = sR_base || ''; payload.firmaE_base = sE_base || ''; }

    try {
      var r = await apiPut(API_ASN + '/' + a.id, payload);
      toast('Cambio registrado ✓');
      printPDF(r);
      await cargarTodo('list');
    } catch (e) { toast(e.message, false); }
  };
  ff.appendChild(bCan); ff.appendChild(bSv); el.appendChild(ff);
  renderItems(eCont, updateReasonsUI); updateReasonsUI();
  return el;
}

// ---------------------------------------------------------------
// RECEPCIÓN / DEVOLUCIÓN
// ---------------------------------------------------------------
function vRec() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">🔄 Recepción / devolución</p>';
  var act = ASN.filter(function (x) { return x.status !== 'devuelto'; });
  if (!act.length) {
    var ok = ce('div', 'gh-card'); ok.style.textAlign = 'center'; ok.style.padding = '50px';
    ok.innerHTML = '<div style="font-size:50px;margin-bottom:16px">✅</div><p style="font-weight:700;font-size:17px;color:var(--accent)">¡Todos están a paz y salvo!</p><p style="color:var(--text-dim);margin-top:8px">No hay herramientas pendientes por devolver.</p>';
    el.appendChild(ok); return el;
  }
  var sw = ce('div', 'sbar'); sw.innerHTML = '<input id="rc-src" placeholder="🔍 Buscar por nombre o cédula...">'; el.appendChild(sw);
  var src = sw.querySelector('#rc-src'); var lc = ce('div'); el.appendChild(lc);
  function rrl(f) {
    lc.innerHTML = ''; var flt = (f || '').toLowerCase();
    var fil = act.filter(function (a) { if (!flt) return true; return (a.nombre || '').toLowerCase().indexOf(flt) > -1 || (a.cedula || '').indexOf(flt) > -1; });
    if (!fil.length) { lc.innerHTML = '<div class="empty-block">Sin resultados.</div>'; return; }
    fil.forEach(function (a) {
      var ini = (a.nombre || '?').split(' ').slice(0, 2).map(function (w) { return w[0] || ''; }).join('').toUpperCase();
      var card = ce('div', 'lcard');
      card.innerHTML = '<div class="lcard-l"><div class="avt" style="background:var(--warning);color:#3a2a04">' + esc(ini) + '</div><div><div class="lcname">' + esc(a.nombre) + '</div><div class="lcmeta">CC: ' + esc(a.cedula) + ' · ' + esc(a.area || '—') + '</div><div class="lcmeta">🔧 ' + (a.items || []).map(function (i) { return esc(i.herramienta); }).join(', ') + '</div></div></div><button class="btn btn-primary">Procesar retorno</button>';
      card.querySelector('button').onclick = function () { showRecForm(el, a); };
      lc.appendChild(card);
    });
  }
  rrl(''); src.oninput = function () { rrl(this.value); };
  return el;
}

function showRecForm(parent, a) {
  parent.innerHTML = '';
  var bB = ce('button', 'btn btn-ghost'); bB.style.marginBottom = '16px'; bB.textContent = '← Volver'; bB.onclick = function () { VIEW = 'rec'; render(); }; parent.appendChild(bB);
  var tt = ce('p', 'gh-title'); tt.innerHTML = '📥 Devolución de: <b>' + esc(a.nombre) + '</b>'; parent.appendChild(tt);

  var ri = JSON.parse(JSON.stringify(a.items || []));
  var c1 = ce('div', 'gh-card'); c1.innerHTML = '<div class="sh"><div class="sn">1</div>Herramientas a devolver</div>';
  ri.forEach(function (it, idx) {
    var row = ce('div', 'ibox');
    row.innerHTML = '<p style="font-weight:700;margin-bottom:12px">🔧 ' + esc(it.herramienta) + '<span style="font-weight:400;color:var(--text-dim);font-size:12px"> — ' + esc(it.marca || '') + '</span></p><div class="g2">' +
      '<label class="lbl-field">Fecha devolución<input type="date" class="r-dt" value="' + (it.fechaDevolucion || todayISO()) + '"></label>' +
      '<label class="lbl-field">Estado final<select class="r-es">' + ESTADOS.map(function (e) { return '<option' + (it.estado === e ? ' selected' : '') + '>' + e + '</option>'; }).join('') + '</select></label>' +
      '<label class="lbl-field span-2">Novedades/daños<input class="r-ob" value="' + (it.observaciones || 'Todo conforme') + '"></label></div>';
    row.querySelector('.r-dt').onchange = function (ev) { ri[idx].fechaDevolucion = ev.target.value; };
    row.querySelector('.r-es').onchange = function (ev) { ri[idx].estado = ev.target.value; };
    row.querySelector('.r-ob').oninput = function (ev) { ri[idx].observaciones = ev.target.value; };
    c1.appendChild(row);
  });
  parent.appendChild(c1);

  var c2 = ce('div', 'gh-card'); c2.innerHTML = '<div class="sh"><div class="sn">2</div>Firmas de devolución</div>';
  var sg2 = ce('div', 'sig-grid'); var sDevR = null, sDevE = null;
  var sp1 = mkSig('🖊️ Quien entrega (colaborador) *'); var sp2 = mkSig('🖊️ Quien recibe (empresa)');
  sp1.on(function (d) { sDevR = d; }); sp2.on(function (d) { sDevE = d; });
  sg2.appendChild(sp1.el); sg2.appendChild(sp2.el); c2.appendChild(sg2); parent.appendChild(c2);

  var bC = ce('button', 'btn btn-primary'); bC.style.marginTop = '12px'; bC.textContent = '✅ Confirmar reingreso al almacén';
  bC.onclick = async function () {
    if (!sDevR) return toast('La firma del colaborador es obligatoria', false);
    try {
      var r = await apiPost(API_ASN + '/' + a.id + '/recepcion', { items: ri, firmaRecibe: sDevR, firmaEntrega: sDevE || '' });
      toast('Devolución registrada ✓');
      var pdfDev = JSON.parse(JSON.stringify(a));
      pdfDev.status = 'devuelto'; pdfDev.items_dev = ri; pdfDev.fecha_dev = r.fecha_dev; pdfDev.firma_recibe_dev = sDevR; pdfDev.firma_entrega_dev = sDevE || '';
      printPDF(pdfDev);
      await cargarTodo('rec');
    } catch (e) { toast(e.message, false); }
  };
  parent.appendChild(bC);
}

// ---------------------------------------------------------------
// BAJAS
// ---------------------------------------------------------------
function vBajas() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">🗑️ Baja de activos</p><div class="gh-alert gh-alert-orange">⚠️ <b>Importante:</b> la baja reduce el stock definitivamente y genera un acta oficial. No se puede deshacer.</div>';
  var bN = ce('button', 'btn btn-primary'); bN.style.marginBottom = '16px'; bN.textContent = '🗑️ Registrar nueva baja'; bN.onclick = function () { showBajaForm(el); }; el.appendChild(bN);

  var rows = BAJAS.slice().reverse().map(function (b) {
    return '<tr><td style="font-family:var(--font-mono);font-size:11px">' + esc(b.codigo) + '</td><td><b>' + esc(b.nombre) + '</b></td><td>' + esc(b.categoria || '—') + '</td><td>' + esc(b.marca || '') + ' ' + esc(b.modelo || '') + '</td><td style="text-align:center">' + b.cantidad + '</td><td>' + esc(b.motivo || '—') + '</td><td>' + esc(b.responsable_nombre || '—') + '</td><td style="font-size:10.5px">' + esc(b.fecha) + '</td><td><button class="row-btn" onclick="printActaBajaById(' + b.id + ')">Acta</button></td></tr>';
  }).join('');

  var tw = ce('div', 'panel table-panel');
  tw.innerHTML = '<table class="data-table"><thead><tr><th>Código</th><th>Equipo</th><th>Categoría</th><th>Marca/Modelo</th><th>Cant.</th><th>Motivo</th><th>Responsable</th><th>Fecha</th><th></th></tr></thead><tbody>' + (rows || '<tr><td colspan="9" class="empty-state">No hay bajas registradas</td></tr>') + '</tbody></table>';
  el.appendChild(tw);
  return el;
}

function printActaBajaById(id) { var b = BAJAS.find(function (x) { return x.id === id; }); if (b) printActaBaja(b); }

function showBajaForm(parent) {
  var ex = parent.querySelector('.bj-fw'); if (ex) { ex.remove(); return; }
  var wrap = ce('div', 'bj-fw'); wrap.style.marginBottom = '20px';

  var c1 = ce('div', 'gh-card');
  var sh = '<option value="">-- Selecciona un equipo con stock disponible --</option>';
  INV.filter(function (i) { return i.cantidad_stock > 0; }).forEach(function (inv) { sh += '<option value="' + inv.id + '">' + esc(inv.nombre) + ' | ' + esc(inv.marca || '') + ' ' + esc(inv.modelo || '') + ' [S/N: ' + esc(inv.serial || 'N/A') + '] — Stock: ' + inv.cantidad_stock + '</option>'; });
  c1.innerHTML = '<div class="sh"><div class="sn">1</div>Equipo a dar de baja</div><label class="lbl-field">Seleccionar equipo *<select id="bj-s">' + sh + '</select></label><div id="bj-inf" style="display:none;margin:12px 0"></div><div class="g2"><label class="lbl-field">Cantidad a dar de baja *<input type="number" id="bj-q" value="1" min="1"></label><label class="lbl-field">Fecha de baja *<input type="date" id="bj-f" value="' + todayISO() + '"></label></div>';
  wrap.appendChild(c1);

  var c2 = ce('div', 'gh-card');
  c2.innerHTML = '<div class="sh"><div class="sn">2</div>Motivo y disposición final</div><div class="g2"><label class="lbl-field">Motivo *<select id="bj-m">' + MOTIVOS.map(function (m) { return '<option>' + esc(m) + '</option>'; }).join('') + '</select></label><label class="lbl-field">Disposición final *<select id="bj-dp">' + DISPS.map(function (d) { return '<option>' + esc(d) + '</option>'; }).join('') + '</select></label><label class="lbl-field span-2">Entidad/persona receptora<input id="bj-ent"></label></div>';
  wrap.appendChild(c2);

  var c3 = ce('div', 'gh-card');
  c3.innerHTML = '<div class="sh"><div class="sn">3</div>Datos del responsable</div><div class="g3"><label class="lbl-field">Nombre completo *<input id="bj-rn"></label><label class="lbl-field">Cargo<input id="bj-rc"></label><label class="lbl-field">Área<select id="bj-ra">' + AREAS.map(function (a) { return '<option>' + esc(a) + '</option>'; }).join('') + '</select></label></div>';
  wrap.appendChild(c3);

  var c4 = ce('div', 'gh-card');
  c4.innerHTML = '<div class="sh"><div class="sn">4</div>Especificaciones técnicas</div><div class="g4" style="margin-bottom:12px">' +
    '<label class="lbl-field">Hostname<input id="bj-hn"></label><label class="lbl-field">Disco duro<input id="bj-dk"></label><label class="lbl-field">RAM<input id="bj-rm"></label><label class="lbl-field">Procesador<input id="bj-cp"></label>' +
    '<label class="lbl-field">Impresora asignada<input id="bj-ip"></label><label class="lbl-field">Jefe inmediato<input id="bj-ji"></label><label class="lbl-field">Ext./celular<input id="bj-ex"></label><label class="lbl-field">E-mail<input id="bj-em"></label></div>' +
    '<label class="lbl-field">Software instalado<div class="chkgrp" id="bj-sw">' + SW_LIST.map(function (s) { return '<label class="chkitem"><input type="checkbox" value="' + esc(s) + '">' + esc(s) + '</label>'; }).join('') + '</div></label>' +
    '<label class="lbl-field" style="margin-top:12px">Observaciones<textarea id="bj-ob" rows="3"></textarea></label>';
  wrap.appendChild(c4);

  var c5 = ce('div', 'gh-card'); c5.innerHTML = '<div class="sh"><div class="sn">5</div>Firma del responsable</div>';
  var firmaBj = null; var spBj = mkSig('🖊️ Firma del responsable *'); spBj.on(function (d) { firmaBj = d; }); c5.appendChild(spBj.el); wrap.appendChild(c5);

  var ff = ce('div', 'gh-ffooter');
  var bCa = ce('button', 'btn btn-ghost'); bCa.textContent = 'Cancelar'; bCa.onclick = function () { wrap.remove(); };
  var bSv = ce('button', 'btn btn-primary'); bSv.textContent = '🗑️ Registrar baja y generar acta';
  bSv.onclick = async function () {
    var selEl = ge('bj-s'); if (!selEl.value) return toast('Selecciona un equipo', false);
    var si = INV.find(function (i) { return String(i.id) === selEl.value; }); if (!si) return toast('Equipo no encontrado', false);
    var rn = ge('bj-rn').value.trim(); if (!rn) return toast('El nombre del responsable es obligatorio', false);
    if (!firmaBj) return toast('La firma del responsable es obligatoria', false);
    var cnt = parseInt(ge('bj-q').value) || 1; if (cnt > si.cantidad_stock) return toast('Cantidad supera el stock (' + si.cantidad_stock + ')', false);
    var sw = []; c4.querySelectorAll('#bj-sw input:checked').forEach(function (cb) { sw.push(cb.value); });

    var payload = {
      itemId: String(si.id), nombre: si.nombre, categoria: si.categoria, marca: si.marca, modelo: si.modelo, serial: si.serial,
      cantidad: cnt, motivo: ge('bj-m').value, disposicion: ge('bj-dp').value, entidad: ge('bj-ent').value.trim(),
      responsNombre: rn, responsCargo: ge('bj-rc').value.trim(), area: ge('bj-ra').value, observaciones: ge('bj-ob').value.trim(), firma: firmaBj,
      config: { hostname: ge('bj-hn').value.trim(), disco: ge('bj-dk').value.trim(), ram: ge('bj-rm').value.trim(), cpu: ge('bj-cp').value.trim(), impresora: ge('bj-ip').value.trim(), jefe: ge('bj-ji').value.trim(), ext: ge('bj-ex').value.trim(), email: ge('bj-em').value.trim(), software: sw, fechaBaja: ge('bj-f').value },
    };
    try {
      var r = await apiPost(API_BAJ, payload);
      toast('Baja registrada: ' + r.codigo + ' ✓');
      printActaBaja(r);
      await cargarTodo('baja');
    } catch (e) { toast(e.message, false); }
  };
  ff.appendChild(bCa); ff.appendChild(bSv); wrap.appendChild(ff);

  ge('bj-s').onchange = function () {
    var inf = ge('bj-inf'); var m = INV.find(function (i) { return String(i.id) === this.value; }, this);
    m = INV.find(function (i) { return String(i.id) === ge('bj-s').value; });
    if (m) { inf.style.display = 'block'; inf.innerHTML = '<div class="g4"><div><span class="lbl-field" style="display:block">Categoría</span><b>' + esc(m.categoria || '') + '</b></div><div><span class="lbl-field" style="display:block">Marca</span><b>' + esc(m.marca || '') + '</b></div><div><span class="lbl-field" style="display:block">Modelo</span><b>' + esc(m.modelo || '') + '</b></div><div><span class="lbl-field" style="display:block">Stock actual</span><b style="color:var(--accent)">' + m.cantidad_stock + '</b></div></div>'; ge('bj-hn').value = m.nombre; ge('bj-q').max = m.cantidad_stock; }
    else { inf.style.display = 'none'; }
  };
  var tw2 = parent.querySelector('.table-panel'); parent.insertBefore(wrap, tw2);
}

// ---------------------------------------------------------------
// FIRMA (canvas)
// ---------------------------------------------------------------
function mkSig(label) {
  var wrap = ce('div', 'sigw'); var lbl = ce('span', 'sig-lbl'); lbl.textContent = label; wrap.appendChild(lbl);
  var cv = ce('canvas', 'sig-cv'); cv.width = 250; cv.height = 75; cv.style.height = '75px'; wrap.appendChild(cv);
  var ctx = cv.getContext('2d'), draw = false, has = false, cbs = [];
  ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, cv.width, cv.height);
  function pos(e) { var r = cv.getBoundingClientRect(), sx = cv.width / r.width, sy = cv.height / r.height, s = e.touches ? e.touches[0] : e; return { x: (s.clientX - r.left) * sx, y: (s.clientY - r.top) * sy }; }
  function start(e) { e.preventDefault(); draw = true; cv.classList.add('on'); var p = pos(e); ctx.beginPath(); ctx.moveTo(p.x, p.y); }
  function move(e) { if (!draw) return; e.preventDefault(); var p = pos(e); ctx.lineTo(p.x, p.y); ctx.strokeStyle = '#0b2d5e'; ctx.lineWidth = 2.5; ctx.lineCap = 'round'; ctx.lineJoin = 'round'; ctx.stroke(); has = true; }
  function end() { if (!draw) return; draw = false; if (has) { var d = cv.toDataURL('image/jpeg', 0.6); cbs.forEach(function (f) { f(d); }); } }
  cv.addEventListener('mousedown', start); cv.addEventListener('touchstart', start, { passive: false });
  cv.addEventListener('mousemove', move); cv.addEventListener('touchmove', move, { passive: false });
  cv.addEventListener('mouseup', end); cv.addEventListener('mouseleave', end); cv.addEventListener('touchend', end);
  var clr = ce('button', 'sig-clr'); clr.type = 'button'; clr.textContent = '🗑️ Limpiar firma';
  clr.onclick = function () { ctx.clearRect(0, 0, cv.width, cv.height); ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, cv.width, cv.height); has = false; cv.classList.remove('on'); cbs.forEach(function (f) { f(null); }); };
  wrap.appendChild(clr);
  return { el: wrap, on: function (fn) { cbs.push(fn); } };
}

// ---------------------------------------------------------------
// IMPRESIÓN — se conserva EXACTAMENTE el formato original F-SGI-GH-12
// ---------------------------------------------------------------
function printPDF(a) { ge('pz').innerHTML = buildPDF(a); window.print(); }

function buildPDF(a) {
  var hasHist = (a.historial && a.historial.length > 0);
  var isRet = (a.status === 'devuelto');
  var totalPages = 1; if (hasHist) totalPages++; if (isRet) totalPages++;
  var currPg = 1;

  function hdr(tit, pg, ofpg) { return '<table class="ph"><tr><td style="width:18%;text-align:center"><div style="font-weight:900;font-size:16px;letter-spacing:1px">IMPLESEG</div><div style="font-size:7px">Seguridad Industrial</div></td><td style="text-align:center"><div style="font-weight:700;font-size:9px">IMPLESEG SAS</div><div style="font-weight:700;font-size:8px">SISTEMA DE GESTIÓN INTEGRAL</div><div style="font-weight:800;font-size:10px;margin-top:2px">' + tit + '</div></td><td style="width:20%;font-size:8px;line-height:1.8"><b>Código:</b> F-SGI-GH-12<br><b>Revisión:</b> 01<br><b>Fecha:</b> 05/03/2024<br><b>Página:</b> ' + pg + ' de ' + ofpg + '</td></tr></table>'; }
  function meta(n, c, ca, ar) { return '<table class="pm"><tr><td style="width:55%"><b>Nombre del Servidor:</b> ' + esc(n) + '</td><td><b>Documento:</b> ' + esc(c) + '</td></tr><tr><td><b>Cargo Funcional:</b> ' + esc(ca || '—') + '</td><td><b>Área de Operación:</b> ' + esc(ar) + '</td></tr></table>'; }
  function sigCell(b64) { if (b64 && String(b64).indexOf('data:image') === 0) return '<img src="' + b64 + '" style="max-height:26px;max-width:72px;display:block;margin:0 auto">'; return ''; }
  function clause(t) { return '<div class="pcl">' + t + '</div>'; }
  function footer(lbl1, nom1, lbl2, nom2) { return '<table class="pf"><tr><td><br><hr style="margin:2px 0"><small>' + lbl1 + '<br><b>Elaboró</b></small></td><td><br><hr style="margin:2px 0"><small>' + lbl2 + ': ' + esc(nom2) + '<br><b>Coordinador GGRH</b></small></td><td><br><hr style="margin:2px 0"><small><b>Revisó</b></small></td><td><br><hr style="margin:2px 0"><small>Gerencia<br><b>Aprobó</b></small></td></tr></table>'; }

  var TH = '<thead><tr><th style="width:4%;text-align:center">N°</th><th style="width:11%;text-align:center">Fecha<br>Asig.</th><th style="width:19%">Herramienta / Equipo</th><th style="width:22%">Marca / Modelo / Serial</th><th style="width:5%;text-align:center">Cant.</th><th style="width:8%;text-align:center">Estado</th><th style="width:10%;text-align:center">Firma<br>Recibe</th><th style="width:10%;text-align:center">Firma<br>Entrega</th><th>Observaciones</th></tr></thead>';
  var rows1 = ''; var items = a.items || [];
  for (var i = 0; i < items.length; i++) { var it = items[i]; rows1 += '<tr><td style="text-align:center">' + (i + 1) + '</td><td style="text-align:center;font-size:7px">' + esc(it.fecha || a.fecha) + '</td><td style="font-weight:700">' + esc(it.herramienta) + '</td><td>' + esc(it.marca || '—') + '</td><td style="text-align:center">' + esc(it.cantidad) + '</td><td style="text-align:center">' + esc(it.estado) + '</td><td class="sig-cell">' + sigCell(a.firma_recibe) + '</td><td class="sig-cell">' + sigCell(a.firma_entrega) + '</td><td>' + esc(it.observaciones || it.obs || '') + '</td></tr>'; }
  for (var k = items.length; k < 18; k++) { rows1 += '<tr style="height:22px"><td style="text-align:center">' + (k + 1) + '</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>'; }
  var pg1 = '<div class="pp">' + hdr('ASIGNACIÓN EQUIPOS Y HERRAMIENTAS DE TRABAJO', currPg++, totalPages) + meta(a.nombre, a.cedula, a.cargo, a.area) + '<table class="pit">' + TH + '<tbody>' + rows1 + '</tbody></table>' + clause('Al firmar este documento, me comprometo a utilizar los equipos y herramientas de trabajo de manera responsable y segura, siguiendo las instrucciones del fabricante y las normas de seguridad de la empresa. Asimismo, me comprometo a velar por el cuidado y la custodia de los equipos y herramientas de trabajo, reportando cualquier daño o anomalía de manera oportuna. Entiendo y acepto que debo devolver la herramienta una vez termine la relación laboral por cualquier causa y autorizo el descuento por nómina de cualquier daño o pérdida no atribuible al desgaste normal de la herramienta asignada.') + footer('Coordinador SGI', 'Elaboró', 'Custodio', a.nombre) + '<div class="pconf">CLÁUSULA DE CONFIDENCIALIDAD: Esta información es propiedad Intelectual de IMPLESEG S.A.S.</div></div>';

  var pgHist = '';
  if (hasHist) {
    var rH = '';
    a.historial.forEach(function (h, idx) { rH += '<tr><td style="text-align:center">' + (idx + 1) + '</td><td style="text-align:center;font-size:7px">' + esc(h.fecha) + '</td><td style="font-size:7px;font-weight:700">' + esc(h.herramienta || 'N/A') + '</td><td style="font-size:7px;padding:3px">' + esc(h.nota) + '</td><td class="sig-cell">' + sigCell(h.firmaR) + '</td><td class="sig-cell">' + sigCell(h.firmaE) + '</td></tr>'; });
    for (var kh = a.historial.length; kh < 18; kh++) { rH += '<tr style="height:26px"><td style="text-align:center">' + (kh + 1) + '</td><td></td><td></td><td></td><td></td><td></td></tr>'; }
    var thH = '<thead><tr><th style="width:4%;text-align:center">N°</th><th style="width:10%;text-align:center">Fecha</th><th style="width:16%">Equipo / Herramienta</th><th style="width:24%">Detalle de Novedad / Cambio</th><th style="width:23%;text-align:center">Firma Colaborador</th><th style="width:23%;text-align:center">Firma Empresa</th></tr></thead>';
    pgHist = '<div class="pp pgbr">' + hdr('ANEXO: REGISTRO DE CAMBIOS Y NOVEDADES', currPg++, totalPages) + meta(a.nombre, a.cedula, a.cargo, a.area) + '<table class="pit">' + thH + '<tbody>' + rH + '</tbody></table>' + clause('Con las firmas plasmadas en este anexo, las partes certifican el conocimiento, entrega y/o retiro de los equipos descritos en las novedades, actualizando formalmente el inventario a cargo del colaborador.') + '<div class="pconf" style="margin-top:10px">CLÁUSULA DE CONFIDENCIALIDAD: Esta información es propiedad Intelectual de IMPLESEG S.A.S.</div></div>';
  }

  var pgDev = '';
  if (isRet) {
    var di = (a.items_dev && a.items_dev.length) ? a.items_dev : items.map(function (it) { return { herramienta: it.herramienta, marca: it.marca || '', cantidad: it.cantidad || 1, estado: 'Bueno', observaciones: '', fechaDevolucion: a.fecha_dev || '' }; });
    var rows2 = '';
    for (var d2 = 0; d2 < di.length; d2++) { var dit = di[d2]; rows2 += '<tr><td style="text-align:center">' + (d2 + 1) + '</td><td style="text-align:center;font-size:7px">' + esc(dit.fechaDevolucion || a.fecha_dev || '') + '</td><td style="font-weight:700">' + esc(dit.herramienta) + '</td><td>' + esc(dit.marca || '—') + '</td><td style="text-align:center">' + esc(dit.cantidad || 1) + '</td><td style="text-align:center">' + esc(dit.estado || 'Bueno') + '</td><td class="sig-cell">' + sigCell(a.firma_recibe_dev) + '</td><td class="sig-cell">' + sigCell(a.firma_entrega_dev) + '</td><td>' + esc(dit.observaciones || '') + '</td></tr>'; }
    for (var dk = di.length; dk < 18; dk++) { rows2 += '<tr style="height:22px"><td style="text-align:center">' + (dk + 1) + '</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>'; }
    pgDev = '<div class="pp pgbr">' + hdr('RECEPCIÓN EQUIPOS Y HERRAMIENTAS DE TRABAJO', currPg++, totalPages) + meta(a.nombre, a.cedula, a.cargo, a.area) + '<table class="pit">' + TH + '<tbody>' + rows2 + '</tbody></table>' + clause('Al firmar este documento, el colaborador certifica la devolución conforme de los equipos asignados y la empresa certifica haberlos recibido y verificado. El colaborador queda a paz y salvo respecto a los equipos aquí relacionados.') + footer('Quien Entrega', a.nombre, 'Quien Recibe', 'Coordinador GGRH') + '<div class="pconf">CLÁUSULA DE CONFIDENCIALIDAD: Esta información es propiedad Intelectual de IMPLESEG S.A.S.</div></div>';
  }
  return pg1 + pgHist + pgDev;
}

function printActaBaja(b) { ge('pz').innerHTML = buildActaBaja(b); window.print(); }

function buildActaBaja(b) {
  var cfg = b.config || {}, sw = cfg.software || [];
  function chk(l) { var on = sw.indexOf(l) > -1; return '<span class="chkb">' + (on ? '✓' : '') + '</span>' + l; }
  function sig(b64) { return (b64 && String(b64).indexOf('data:image') === 0) ? '<img src="' + b64 + '" style="max-height:40px;max-width:100px;display:block;margin:0 auto 2px">' : ''; }
  return '<div class="pp"><table class="pb-hdr"><tr><td style="width:20%;text-align:center;border-right:2px solid #000"><div style="font-weight:900;font-size:20px;letter-spacing:2px;color:#15803d">IMPLESEG</div><div style="font-size:7px">Seguridad Industrial</div></td><td style="text-align:center"><div style="font-weight:900;font-size:13px">IMPLESEG SAS</div><div style="font-weight:800;font-size:12px;text-transform:uppercase;margin-top:2px">Acta Baja de Activos Informáticos</div><div style="font-size:7px;color:#666;margin-top:2px">Sistema de Gestión Integral · F-GT-BAJA-01</div></td><td style="width:20%;font-size:7.5px;line-height:1.8;border-left:2px solid #000;padding-left:8px"><b>Código:</b> F-GT-BAJA-01<br><b>Revisión:</b> 01<br><b>Fecha:</b> ' + esc(b.fecha || '') + '<br><b>ID:</b> ' + esc(b.codigo || '') + '</td></tr></table><table class="pb-tbl" style="width:35%;margin-bottom:6px"><tr><td class="lc" style="width:25%">FECHA</td><td>' + esc(cfg.fechaBaja || b.fecha || '') + '</td></tr></table><div class="pb-sec">Datos del Usuario y Ubicación</div><table class="pb-tbl"><tr><td class="lc">NOMBRES Y APELLIDOS</td><td>' + esc(b.responsable_nombre || '') + '</td><td class="lc">ÁREA</td><td>' + esc(b.area || '') + '</td><td class="lc">CENTRO DE COSTO</td><td></td></tr><tr><td class="lc">IDENTIFICACIÓN</td><td></td><td class="lc">PROCESO</td><td></td><td class="lc">EXT / CEL</td><td>' + esc(cfg.ext || '') + '</td></tr><tr><td class="lc">CARGO</td><td>' + esc(b.responsable_cargo || '') + '</td><td class="lc">JEFE INMEDIATO</td><td>' + esc(cfg.jefe || '') + '</td><td class="lc">E-MAIL</td><td>' + esc(cfg.email || '') + '</td></tr></table><div class="pb-sec">Descripción de Hardware</div><table class="pb-tbl"><thead><tr><th style="width:18%">TIPO DE EQUIPO</th><th style="width:30%">SERIAL</th><th>MARCA</th><th>MODELO</th></tr></thead><tbody><tr><td style="font-weight:700">' + esc(b.categoria || '—') + '</td><td><code>' + esc(b.serial || '—') + '</code></td><td>' + esc(b.marca || '—') + '</td><td>' + esc(b.modelo || '—') + '</td></tr><tr style="height:16px"><td></td><td></td><td></td><td></td></tr><tr style="height:16px"><td></td><td></td><td></td><td></td></tr></tbody></table><div class="pb-sec">Configuración y Capacidades</div><table class="pb-tbl"><tr><td class="lc">NOMBRE DEL EQUIPO</td><td>' + esc(cfg.hostname || b.nombre || '') + '</td><td class="lc">DISCO DURO</td><td>' + esc(cfg.disco || '') + '</td><td class="lc">RAM</td><td>' + esc(cfg.ram || '') + '</td><td class="lc">PROCESADOR</td><td>' + esc(cfg.cpu || '') + '</td></tr><tr><td class="lc">IMPRESORA ASIGNADA</td><td colspan="7">' + esc(cfg.impresora || '') + '</td></tr></table><div class="pb-sec">Software</div><table class="pb-tbl"><tr><td>' + chk('Windows') + '</td><td>' + chk('Lector PDF') + '</td><td>' + chk('CRM') + '</td><td>' + chk('VPN') + '</td><td colspan="4"><b>OTROS:</b> ' + esc(sw.filter(function (s) { return ['Windows', 'Office', 'Antivirus', 'Lector PDF', 'CRM', 'VPN', 'ERP'].indexOf(s) === -1; }).join(', ') || '—') + '</td></tr><tr><td>' + chk('Office') + '</td><td>' + chk('Antivirus') + '</td><td colspan="2">' + chk('ERP') + '</td><td colspan="4"></td></tr></table><div class="pb-sec">Motivo de Baja y Disposición Final</div><table class="pb-tbl"><tr><td class="lc">MOTIVO DE BAJA</td><td colspan="3"><b>' + esc(b.motivo || '') + '</b></td><td class="lc">CANTIDAD</td><td><b>' + esc(b.cantidad || 1) + '</b></td></tr><tr><td class="lc">DISPOSICIÓN FINAL</td><td colspan="3"><b>' + esc(b.disposicion || '') + '</b></td><td class="lc">ENTIDAD RECEPTORA</td><td>' + esc(b.entidad || 'N/A') + '</td></tr></table><div class="pb-sec">Observaciones</div><div class="pb-obs">' + esc(b.observaciones || 'Sin observaciones adicionales.') + '</div><table class="pb-sigs"><tr><td>' + sig(b.firma) + '<hr style="margin:2px 0"><small>Responsable<br><b>' + esc(b.responsable_nombre || '') + '</b><br>' + esc(b.responsable_cargo || '') + '</small></td><td><hr style="margin:2px 0"><small>Jefe Inmediato<br><b>' + esc(cfg.jefe || '') + '</b></small></td><td><hr style="margin:2px 0"><small>Coordinador TI<br><b>Vo.Bo.</b></small></td><td><hr style="margin:2px 0"><small>Gerencia<br><b>Aprobó</b></small></td></tr></table><div class="pconf" style="margin-top:5px">CLÁUSULA DE CONFIDENCIALIDAD: Esta información es propiedad Intelectual de IMPLESEG S.A.S.</div></div>';
}
