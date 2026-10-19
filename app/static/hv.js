var API_HV = "/api/hv/equipos";
var HV_DATA = [];
var VIEW = 'dash';
var FILTRO_TIPO = 'COMPUTO';

function ge(id) { return document.getElementById(id); }
function ce(t, c) { var e = document.createElement(t); if (c) e.className = c; return e; }
function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function toast(m, ok) { var t = ge('toast'); if(!t) return; t.textContent = m; t.style.borderColor = (ok === false) ? 'var(--danger)' : 'var(--accent)'; t.classList.add('show'); setTimeout(function () { t.classList.remove('show'); }, 3200); }

async function apiGet(url) { var r = await fetch(url); return r.json(); }
async function apiPost(url, body) { var r = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); return r.json(); }
async function apiPut(url, body) { var r = await fetch(url, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }); return r.json(); }
async function apiDelete(url) { var r = await fetch(url, { method: 'DELETE' }); return r.json(); }

document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('#hvSubNav .nav-item.sub').forEach(function (b) {
    b.onclick = function () { VIEW = b.getAttribute('data-v'); marcarSubNav(); render(); };
  });
  cargarDatos();
});

function marcarSubNav() {
  document.querySelectorAll('#hvSubNav .nav-item.sub').forEach(function (b) {
    b.classList.toggle('on', b.getAttribute('data-v') === VIEW);
  });
}

async function cargarDatos() {
  try { HV_DATA = await apiGet(API_HV); } catch (e) { toast('Error cargando BD', false); }
  render();
}

function render() {
  var app = ge('hvApp'); if(!app) return; app.innerHTML = '';
  if (VIEW === 'dash') app.appendChild(vDash());
  if (VIEW === 'pc') { FILTRO_TIPO = 'COMPUTO'; app.appendChild(vListado()); }
  if (VIEW === 'cel') { FILTRO_TIPO = 'CELULAR'; app.appendChild(vListado()); }
  if (VIEW === 'mto') app.appendChild(vMantenimientos());
}

function vDash() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">📊 Panel de Hojas de Vida Técnicas</p>';
  var pcs = HV_DATA.filter(x => x.tipo_activo !== 'CELULAR');
  var cels = HV_DATA.filter(x => x.tipo_activo === 'CELULAR');
  var mtos = HV_DATA.filter(x => x.estado === 'Mantenimiento').length;

  var sg = ce('section', 'dashboard-grid');
  sg.innerHTML = 
    '<div class="stat-card"><span class="stat-label">💻 Total Computadores</span><span class="stat-value">' + pcs.length + '</span></div>' +
    '<div class="stat-card"><span class="stat-label">📱 Total Celulares/Líneas</span><span class="stat-value">' + cels.length + '</span></div>' +
    '<div class="stat-card stat-warning"><span class="stat-label">🔧 En Mantenimiento</span><span class="stat-value">' + mtos + '</span></div>';
  el.appendChild(sg);
  return el;
}

function vListado() {
  var el = ce('div'); 
  var esPC = FILTRO_TIPO === 'COMPUTO';
  el.innerHTML = '<p class="gh-title">' + (esPC ? '💻 Equipos de Cómputo' : '📱 Líneas Corporativas y Celulares') + '</p>';
  
  var bN = ce('button', 'btn btn-primary'); bN.textContent = '+ Registrar Nuevo ' + (esPC ? 'Equipo' : 'Celular');
  bN.onclick = function() { showFormularioHV(el, esPC); };
  el.appendChild(bN);

  var fb = ce('div', 'hv-filter-bar');
  if (esPC) {
    fb.innerHTML = '<input id="f-gen" placeholder="🔍 Buscar Código, Usuario, Marca...">' +
                   '<input id="f-ram" placeholder="Filtrar por RAM (Ej: 8GB)">' +
                   '<input id="f-cpu" placeholder="Filtrar Procesador (Ej: Core i5)">';
  } else {
    fb.innerHTML = '<input id="f-gen" placeholder="🔍 Buscar Línea, Usuario, IMEI...">' +
                   '<select id="f-tipo"><option value="">Todas las líneas</option><option>Corporativa</option><option>Personal</option></select>';
  }
  el.appendChild(fb);
  var lc = ce('div'); el.appendChild(lc);

  function refrescarLista() {
    var fg = fb.querySelector('#f-gen') ? fb.querySelector('#f-gen').value.toLowerCase() : '';
    var data = HV_DATA.filter(x => esPC ? x.tipo_activo !== 'CELULAR' : x.tipo_activo === 'CELULAR');
    
    data = data.filter(function(i) {
      var txt = JSON.stringify(i).toLowerCase();
      if (fg && txt.indexOf(fg) === -1) return false;
      if (esPC) {
        var fr = fb.querySelector('#f-ram').value.toLowerCase();
        var fc = fb.querySelector('#f-cpu').value.toLowerCase();
        if (fr && (i.memoria||'').toLowerCase().indexOf(fr) === -1) return false;
        if (fc && (i.procesador||'').toLowerCase().indexOf(fc) === -1) return false;
      } else {
        var ft = fb.querySelector('#f-tipo').value;
        if (ft && i.tipo_linea !== ft) return false;
      }
      return true;
    });

    var rows = data.map(function(i) {
      var desc = esPC ? `RAM: ${i.memoria || 'N/A'} | CPU: ${i.procesador || 'N/A'} | Disco: ${i.disco || 'N/A'}` : `IMEI: ${i.imei || 'N/A'} | Plan: ${i.plan_datos || 'N/A'} | Línea: ${i.tipo_linea}`;
      var ident = esPC ? i.nombre_equipo : `Línea: ${i.linea_numero}`;
      return `<tr><td style="font-family:var(--font-mono);font-size:11px">${i.codigo}</td>
              <td><b>${ident}</b></td><td>${i.marca||''} ${i.modelo||''}</td>
              <td style="font-size:11px;color:var(--text-dim)">${desc}</td>
              <td>${i.usuario_asignado||'N/A'}</td>
              <td><span class="badge ${i.estado==='Activo'?'badge-ok':(i.estado==='Baja'?'badge-neutral':'badge-warn')}">${i.estado}</span></td>
              <td style="display:flex;gap:5px;">
                <button class="row-btn" onclick="editarRegistro(${i.id}, ${esPC})">Editar</button>
                <button class="row-btn danger" onclick="eliminarRegistro(${i.id})">🗑️</button>
              </td></tr>`;
    }).join('');

    lc.innerHTML = '<div class="table-panel"><table class="data-table"><thead><tr><th>Código</th><th>Identificador</th><th>Equipo</th><th>Especificaciones</th><th>Usuario</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>' + (rows || '<tr><td colspan="7" class="empty-state">No hay registros</td></tr>') + '</tbody></table></div>';
  }

  fb.addEventListener('input', refrescarLista);
  refrescarLista();
  return el;
}

window.eliminarRegistro = async function(id) {
  if (!confirm("⚠️ ¿Estás seguro de eliminar permanentemente este registro?")) return;
  try {
    await apiDelete(API_HV + '/' + id);
    toast("Registro eliminado ✓");
    cargarDatos();
  } catch(e) { toast("Error al eliminar", false); }
};

window.editarRegistro = function(id, esPC) {
  var item = HV_DATA.find(x => x.id === id);
  if(item) { showFormularioHV(ge('hvApp').querySelector('div'), esPC, item); }
};

function showFormularioHV(parent, esPC, item = null) {
  var ex = parent.querySelector('.hv-form'); if (ex) ex.remove();
  var w = ce('div', 'gh-card hv-form'); w.style.marginTop = '20px';
  w.style.border = '2px solid var(--accent)';

  var i = item || {};
  var iden = i.nombre_equipo || i.linea_numero || '';

  var html = '<div class="sh"><div class="sn">✏️</div>' + (item ? 'Editar' : 'Registrar') + ' ' + (esPC ? 'Equipo de Cómputo' : 'Celular / Línea') + '</div>';
  
  html += '<div class="sect-title">Información General</div><div class="g4">' +
          '<label class="lbl-field">Código Interno *<input id="h-cod" value="' + esc(i.codigo) + '"></label>' +
          '<label class="lbl-field">' + (esPC ? 'Nombre Equipo *' : 'Número de Línea *') + '<input id="h-nom" value="' + esc(iden) + '"></label>' +
          '<label class="lbl-field">Usuario Asignado<input id="h-usu" value="' + esc(i.usuario_asignado) + '"></label>' +
          '<label class="lbl-field">Área<input id="h-are" value="' + esc(i.area) + '"></label>' +
          '<label class="lbl-field">Marca<input id="h-mar" value="' + esc(i.marca) + '"></label>' +
          '<label class="lbl-field">Modelo<input id="h-mod" value="' + esc(i.modelo) + '"></label>' +
          '<label class="lbl-field">' + (esPC ? 'Serial' : 'IMEI *') + '<input id="h-ser" value="' + esc(esPC?i.serial:i.imei) + '"></label>' +
          '<label class="lbl-field">Estado<select id="h-est"><option '+(i.estado==='Activo'?'selected':'')+'>Activo</option><option '+(i.estado==='Mantenimiento'?'selected':'')+'>Mantenimiento</option><option '+(i.estado==='Baja'?'selected':'')+'>Baja</option></select></label>' +
          '</div>';

  if (esPC) {
    html += '<div class="sect-title">Especificaciones Técnicas</div><div class="g4">' +
            '<label class="lbl-field">Procesador (CPU)<input id="h-cpu" value="' + esc(i.procesador) + '"></label>' +
            '<label class="lbl-field">Memoria RAM<input id="h-ram" value="' + esc(i.memoria) + '"></label>' +
            '<label class="lbl-field">Disco Duro<input id="h-hdd" value="' + esc(i.disco) + '"></label>' +
            '<label class="lbl-field">Sistema Operativo<input id="h-so" value="' + esc(i.sistema_operativo) + '"></label>' +
            '<label class="lbl-field">Dirección IP<input id="h-ip" value="' + esc(i.ip) + '"></label>' +
            '<label class="lbl-field">Dirección MAC<input id="h-mac" value="' + esc(i.mac) + '"></label>' +
            '<label class="lbl-field">Licencia Office<input id="h-off" value="' + esc(i.licencia_office) + '"></label>' +
            '<label class="lbl-field">Antivirus<input id="h-av" value="' + esc(i.antivirus) + '"></label>' +
            '</div>';
  } else {
    html += '<div class="sect-title">Datos del Plan y Línea</div><div class="g2">' +
            '<label class="lbl-field">Plan de Datos / Operador<input id="h-pla" value="' + esc(i.plan_datos) + '"></label>' +
            '<label class="lbl-field">Tipo de Línea<select id="h-tpl"><option '+(i.tipo_linea==='Corporativa'?'selected':'')+'>Corporativa</option><option '+(i.tipo_linea==='Personal'?'selected':'')+'>Personal</option></select></label>' +
            '</div>';
  }

  html += '<div class="sect-title">Programación y Observaciones</div><div class="g2">' +
          '<label class="lbl-field">Programar Mantenimiento<input type="date" id="h-mto" value="' + esc(i.mantenimiento_programado) + '"></label>' +
          '<label class="lbl-field">Observaciones Generales<textarea id="h-obs" rows="2">' + esc(i.observaciones) + '</textarea></label>' +
          '</div><div style="margin-top:16px;display:flex;gap:10px;"><button class="btn btn-primary" id="btn-sav-hv">💾 ' + (item ? 'Actualizar' : 'Guardar') + ' Registro</button><button class="btn btn-ghost" onclick="this.parentElement.parentElement.remove()">Cancelar</button></div>';

  w.innerHTML = html;
  
  w.querySelector('#btn-sav-hv').onclick = async function() {
    var cod = w.querySelector('#h-cod').value.trim();
    var nom = w.querySelector('#h-nom').value.trim();
    if (!cod || !nom) return toast('Código y Nombre/Línea son obligatorios', false);

    var payload = {
      tipo_activo: esPC ? 'COMPUTO' : 'CELULAR',
      codigo: cod,
      nombre_equipo: esPC ? nom : 'CELULAR ' + nom,
      linea_numero: esPC ? '' : nom,
      usuario_asignado: w.querySelector('#h-usu').value,
      area: w.querySelector('#h-are').value,
      marca: w.querySelector('#h-mar').value,
      modelo: w.querySelector('#h-mod').value,
      serial: esPC ? w.querySelector('#h-ser').value : '',
      imei: esPC ? '' : w.querySelector('#h-ser').value,
      estado: w.querySelector('#h-est').value,
      procesador: esPC ? w.querySelector('#h-cpu').value : '',
      memoria: esPC ? w.querySelector('#h-ram').value : '',
      disco: esPC ? w.querySelector('#h-hdd').value : '',
      sistema_operativo: esPC ? w.querySelector('#h-so').value : '',
      ip: esPC ? w.querySelector('#h-ip').value : '',
      mac: esPC ? w.querySelector('#h-mac').value : '',
      licencia_office: esPC ? w.querySelector('#h-off').value : '',
      antivirus: esPC ? w.querySelector('#h-av').value : '',
      plan_datos: esPC ? '' : w.querySelector('#h-pla').value,
      tipo_linea: esPC ? '' : w.querySelector('#h-tpl').value,
      mantenimiento_programado: w.querySelector('#h-mto').value,
      observaciones: w.querySelector('#h-obs').value
    };

    try {
      if(item) {
        await apiPut(API_HV + '/' + item.id, payload);
        toast('Actualizado correctamente ✓');
      } else {
        await apiPost(API_HV, payload);
        toast('Creado y sincronizado ✓');
      }
      cargarDatos();
    } catch(e) { toast('Error al guardar', false); }
  };

  parent.insertBefore(w, parent.children[2]);
}

function vMantenimientos() {
  var el = ce('div'); el.innerHTML = '<p class="gh-title">🔧 Control de Mantenimientos Programados</p>';
  var mtos = HV_DATA.filter(x => x.mantenimiento_programado || x.estado === 'Mantenimiento');
  
  var rows = mtos.map(function(i) {
    var esP = i.estado === 'Mantenimiento';
    return `<tr>
              <td><b>${i.codigo}</b></td>
              <td>${i.nombre_equipo || i.linea_numero}</td>
              <td>${i.usuario_asignado || 'N/A'}</td>
              <td style="color:${esP ? 'var(--danger)' : 'var(--accent)'}; font-weight:700">${i.mantenimiento_programado || 'En Taller'}</td>
              <td><span class="badge ${esP ? 'badge-warn' : 'badge-neutral'}">${i.estado}</span></td>
            </tr>`;
  }).join('');

  var tw = ce('div', 'panel table-panel');
  tw.innerHTML = '<table class="data-table"><thead><tr><th>Código</th><th>Activo</th><th>Usuario</th><th>Fecha Programada</th><th>Estado</th></tr></thead><tbody>' + (rows || '<tr><td colspan="5" class="empty-state">No hay mantenimientos programados.</td></tr>') + '</tbody></table>';
  el.appendChild(tw);
  return el;
}