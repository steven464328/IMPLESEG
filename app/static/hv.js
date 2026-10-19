// ═══════════════════════════════════════════════════════════════
// IMPLESEG SAS · Módulo Hojas de Vida (Equipos y Celulares)
// Incluye Importador Masivo de Excel (Copiar y Pegar)
// ═══════════════════════════════════════════════════════════════

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
  
  var topBar = ce('div'); topBar.style.display = 'flex'; topBar.style.gap = '10px'; topBar.style.marginBottom = '16px';
  var bN = ce('button', 'btn btn-primary'); bN.textContent = '+ Registrar Nuevo ' + (esPC ? 'Equipo' : 'Celular');
  bN.onclick = function() { showFormularioHV(el, esPC); };
  
  var bI = ce('button', 'btn btn-ghost'); bI.textContent = '📥 Importar desde Excel';
  bI.onclick = function() { showImportador(el, esPC); };

  topBar.appendChild(bN); topBar.appendChild(bI);
  el.appendChild(topBar);

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

// ========================================================
// IMPORTADOR MASIVO
// ========================================================
function showImportador(parent, esPC) {
  var ex = parent.querySelector('.hv-form'); if (ex) ex.remove();
  var w = ce('div', 'gh-card hv-form'); w.style.marginTop = '20px';
  w.style.border = '2px dashed var(--accent)';

  var tipoStr = esPC ? 'Computadores (Hoja: Empresas EJ)' : 'Celulares (Hoja: Líneas)';
  
  w.innerHTML = `
    <div class="sh"><div class="sn">📥</div>Importación Masiva de Excel</div>
    <div class="gh-alert gh-alert-purple" style="margin-bottom:15px">
      <b>Instrucciones:</b> Ve a tu archivo de Excel, selecciona TODAS las filas de la hoja de <b>${tipoStr}</b> (incluyendo la fila de arriba que tiene los nombres de las columnas), presiona <b>Ctrl+C</b> para copiarlas, y luego pégalas aquí abajo presionando <b>Ctrl+V</b>.
    </div>
    <textarea id="imp-data" rows="8" style="width:100%; background:#0f172a; color:#fff; border:1px solid #334155; border-radius:6px; padding:10px; font-family:monospace;" placeholder="Pega los datos aquí..."></textarea>
    <div id="imp-status" style="margin-top:10px; font-size:14px; font-weight:bold; color:var(--accent);"></div>
    <div style="margin-top:16px;display:flex;gap:10px;">
      <button class="btn btn-primary" id="btn-procesar-imp">🚀 Procesar e Importar</button>
      <button class="btn btn-ghost" onclick="this.parentElement.parentElement.remove()">Cancelar</button>
    </div>
  `;
  
  w.querySelector('#btn-procesar-imp').onclick = async function() {
    var btn = this;
    var text = w.querySelector('#imp-data').value.trim();
    if(!text) return toast('Pega los datos primero', false);
    
    var lines = text.split('\n');
    if(lines.length < 2) return toast('Faltan datos (asegúrate de incluir los encabezados)', false);
    
    var headers = lines[0].split('\t').map(h => h.trim().toUpperCase());
    var statusEl = w.querySelector('#imp-status');
    
    btn.disabled = true;
    var procesados = 0; var errores = 0;
    
    for(var i = 1; i < lines.length; i++) {
      var rowData = lines[i].split('\t');
      if(rowData.length < 2) continue; // Saltar lineas en blanco
      
      var row = {};
      for(var j = 0; j < headers.length; j++) { row[headers[j]] = (rowData[j] || '').trim(); }
      
      var cod = row['CODIGO'] || row['CODIGO CELULAR'] || ('IMP'+Math.floor(Math.random()*10000));
      var ident = row['NOMBRE EQUIPO'] || row['EQUIPO'] || row['LINEA'] || row['NUMERO'] || '';
      if (!ident) continue;

      var payload;
      if (esPC) {
          payload = {
              tipo_activo: 'COMPUTO', codigo: cod, nombre_equipo: ident, empresa: row['EMPRESA'] || 'IMPLESEG',
              area: row['AREA'] || '', usuario_asignado: row['USUARIO ASIGNADO'] || row['USUARIO'] || '',
              marca: row['MARCA'] || '', modelo: row['MODELO'] || row['MODEL'] || '',
              serial: row['SERIAL NUMBER / SERVICE TAG'] || row['SERIAL'] || '', procesador: row['PROCESADOR'] || row['CPU'] || '',
              memoria: row['MEMORIA'] || row['RAM'] || '', disco: row['HDD/SSD'] || '', mac: row['MAC'] || '',
              ip: row['IP'] || '', sistema_operativo: row['SISTEMA OPERATIVO'] || '',
              licencia_office: row['OFICCE'] || row['OFFICE'] || '', antivirus: row['ANTIVIRUS'] || '',
              precio: parseFloat(row['PRECIO']) || 0, observaciones: row['OBSERVACION'] || row['OBSERVACIONES'] || '', estado: 'Activo',
              config: {
                  tipo: row['TIPO'] || row['EQUIPO'] || '', usuario_servidor: row['USUARIO SERVIDOR'] || '',
                  mainboard: row['MAINBOARD'] || '', tamano_disco: row['TAMAÑO DISCO'] || '', anydesk: row['ANYDESK'] || '',
                  diadema: row['DIADEMA'] || '', teclado: row['TECLADO'] || '', mouse: row['MOUSE'] || '',
                  base_refrigerante: row['BASE REFRIGERANTE'] || '', fecha_vencimiento_av: row['FECHA VENCIMIENTO'] || '',
                  observaciones_so: row['OBSERVACIONES SO'] || '', licencia: row['LICENCIA'] || '',
                  correo_licencia: row['SERIAL / CORREO'] || '', programas: row['PROGRAMAS'] || '',
                  formula: row['FORMULA'] || '', etiqueta: row['ETIQUETA'] || '', pantalla_auxiliar: row['PANTALLA AUXILIAR'] || '',
                  numero_factura: row['NUMERO FACTURA'] || '', fecha_factura: row['FECHA FACTURA'] || '',
                  productos_factura: row['PRODUCTOS'] || '', revision_drive: row['REVISION DRIVE'] || '',
                  seriales: row['SERIALES'] || '', office_funciones: row['OFFICE FUNCIONES'] || ''
              }
          };
      } else {
          payload = {
              tipo_activo: 'CELULAR', codigo: cod, linea_numero: ident, nombre_equipo: 'CELULAR ' + ident,
              usuario_asignado: row['NOMBRE USUARIO'] || row['NOMBRE'] || '', area: row['AREA'] || '',
              marca: row['MARCA'] || '', modelo: row['MODELO'] || '', imei: row['IMEI'] || '',
              procesador: row['CPU'] || '', memoria: row['RAM'] || '', mac: row['MAC'] || '',
              plan_datos: row['COMBRE DEL PLAN ACTUAL'] || row['PLAN ACTUAL'] || '',
              tipo_linea: row['PROPIEDAD LINEA'] || 'Corporativa', precio: parseFloat(row['PRECIO']) || 0,
              observaciones: row['OBSERVACIONES'] || '', estado: 'Activo',
              config: {
                  cuenta: row['CUENTA'] || '', detalle_plan: row['DETALLE DEL PLAN ACTUAL'] || '',
                  cfm: row['CFM'] || '', equipo_propiedad: row['EQUIPO CELULAR / PROPIETARIO'] || '',
                  fecha_activacion: row['FECHA ACTIVACION'] || '', cedula_usuario: row['NIT / CEDULA'] || '',
                  referencia: row['REFERENCIA'] || '', rom: row['ROOM'] || row['ROM'] || '',
                  serial_adicional: row['SERIAL'] || '', revision: row['REVISION'] || '',
                  observacion_1: row['OBSERVACION 1'] || '', formula: row['FORMULA'] || '',
                  etiqueta: row['ETIQUETA'] || '', numero_factura: row['NUMERO FACTURA'] || '',
                  fecha_factura: row['FECHA FACTURA'] || '', productos_factura: row['PRODUCTOS'] || ''
              }
          };
      }

      statusEl.textContent = 'Importando registro ' + procesados + ' de ' + (lines.length - 1) + '...';
      try { await apiPost(API_HV, payload); procesados++; } catch(e) { errores++; }
    }
    
    toast('Importación: ' + procesados + ' correctos, ' + errores + ' errores.', (errores === 0));
    cargarDatos();
    w.remove();
  };
  
  parent.insertBefore(w, parent.children[2]);
}

// ========================================================
// FORMULARIOS DE REGISTRO
// ========================================================
function showFormularioHV(parent, esPC, item = null) {
  var ex = parent.querySelector('.hv-form'); if (ex) ex.remove();
  var w = ce('div', 'gh-card hv-form'); w.style.marginTop = '20px';
  w.style.border = '2px solid var(--accent)';

  var i = item || {};
  var c = i.config || {};
  var iden = i.nombre_equipo || i.linea_numero || '';

  var html = '<div class="sh"><div class="sn">✏️</div>' + (item ? 'Editar' : 'Registrar') + ' ' + (esPC ? 'Equipo de Cómputo' : 'Celular / Línea') + '</div>';
  
  if (esPC) {
    // ---- FORMULARIO ORDENADO PARA PC ----
    html += '<div class="sect-title">Información Principal</div><div class="g4">';
    html += '<label class="lbl-field">Empresa<input id="h-emp" value="' + esc(i.empresa) + '"></label>';
    html += '<label class="lbl-field">Equipo (Tipo)<input id="c-tip" value="' + esc(c.tipo) + '"></label>';
    html += '<label class="lbl-field">Código Interno *<input id="h-cod" value="' + esc(i.codigo) + '"></label>';
    html += '<label class="lbl-field">Área<input id="h-are" value="' + esc(i.area) + '"></label>';
    html += '<label class="lbl-field">Nombre Equipo *<input id="h-nom" value="' + esc(iden) + '"></label>';
    html += '<label class="lbl-field">Usuario Servidor<input id="c-ususer" value="' + esc(c.usuario_servidor) + '"></label>';
    html += '<label class="lbl-field">Usuario Asignado<input id="h-usu" value="' + esc(i.usuario_asignado) + '"></label>';
    html += '<label class="lbl-field">Estado<select id="h-est"><option '+(i.estado==='Activo'?'selected':'')+'>Activo</option><option '+(i.estado==='Mantenimiento'?'selected':'')+'>Mantenimiento</option><option '+(i.estado==='Baja'?'selected':'')+'>Baja</option></select></label>';
    html += '</div>';

    html += '<div class="sect-title">Hardware y Componentes</div><div class="g4">';
    html += '<label class="lbl-field">Marca<input id="h-mar" value="' + esc(i.marca) + '"></label>';
    html += '<label class="lbl-field">Modelo<input id="h-mod" value="' + esc(i.modelo) + '"></label>';
    html += '<label class="lbl-field">CPU / Procesador<input id="h-cpu" value="' + esc(i.procesador) + '"></label>';
    html += '<label class="lbl-field">Memoria RAM<input id="h-ram" value="' + esc(i.memoria) + '"></label>';
    html += '<label class="lbl-field">Mainboard<input id="c-main" value="' + esc(c.mainboard) + '"></label>';
    html += '<label class="lbl-field">HDD / SSD<input id="h-hdd" value="' + esc(i.disco) + '"></label>';
    html += '<label class="lbl-field">Tamaño Disco<input id="c-tamdis" value="' + esc(c.tamano_disco) + '"></label>';
    html += '<label class="lbl-field">Serial / Service Tag<input id="h-ser" value="' + esc(i.serial) + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Redes y Periféricos</div><div class="g4">';
    html += '<label class="lbl-field">MAC Address<input id="h-mac" value="' + esc(i.mac) + '"></label>';
    html += '<label class="lbl-field">Dirección IP<input id="h-ip" value="' + esc(i.ip) + '"></label>';
    html += '<label class="lbl-field">Pantalla Auxiliar<input id="c-pau" value="' + esc(c.pantalla_auxiliar) + '"></label>';
    html += '<label class="lbl-field">Teclado<input id="c-tec" value="' + esc(c.teclado) + '"></label>';
    html += '<label class="lbl-field">Mouse<input id="c-mou" value="' + esc(c.mouse) + '"></label>';
    html += '<label class="lbl-field">Diadema<input id="c-dia" value="' + esc(c.diadema) + '"></label>';
    html += '<label class="lbl-field">Base Refrigerante<input id="c-bas" value="' + esc(c.base_refrigerante) + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Software, Office y Licencias</div><div class="g4">';
    html += '<label class="lbl-field">Sistema Operativo<input id="h-so" value="' + esc(i.sistema_operativo) + '"></label>';
    html += '<label class="lbl-field">Antivirus<input id="h-av" value="' + esc(i.antivirus) + '"></label>';
    html += '<label class="lbl-field">Fecha Venc. Antivirus<input id="c-fvenav" type="date" value="' + esc(c.fecha_vencimiento_av) + '"></label>';
    html += '<label class="lbl-field">Anydesk ID<input id="c-any" value="' + esc(c.anydesk) + '"></label>';
    html += '<label class="lbl-field">Office<input id="h-off" value="' + esc(i.licencia_office) + '"></label>';
    html += '<label class="lbl-field">Licencia Office<input id="c-lic" value="' + esc(c.licencia) + '"></label>';
    html += '<label class="lbl-field">Serial / Correo Licencia<input id="c-corlic" value="' + esc(c.correo_licencia) + '"></label>';
    html += '<label class="lbl-field">Programas Adicionales<input id="c-prog" value="' + esc(c.programas) + '"></label>';
    html += '<label class="lbl-field">Office Funciones<input id="c-ofun" value="' + esc(c.office_funciones) + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Control y Facturación</div><div class="g4">';
    html += '<label class="lbl-field">Fórmula<input id="c-for" value="' + esc(c.formula) + '"></label>';
    html += '<label class="lbl-field">Etiqueta<input id="c-eti" value="' + esc(c.etiqueta) + '"></label>';
    html += '<label class="lbl-field">Número Factura<input id="c-numfac" value="' + esc(c.numero_factura) + '"></label>';
    html += '<label class="lbl-field">Fecha Factura<input type="date" id="c-fecfac" value="' + esc(c.fecha_factura) + '"></label>';
    html += '<label class="lbl-field">Productos Factura<input id="c-profac" value="' + esc(c.productos_factura) + '"></label>';
    html += '<label class="lbl-field">Precio / Valor<input type="number" id="c-pre" value="' + esc(i.precio || '') + '"></label>';
    html += '<label class="lbl-field">Seriales Adicionales<input id="c-sers" value="' + esc(c.seriales) + '"></label>';
    html += '<label class="lbl-field">Mantenimiento (Fecha)<input type="date" id="h-mto" value="' + esc(i.mantenimiento_programado) + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Observaciones y Notas</div><div class="g3">';
    html += '<label class="lbl-field">Observaciones Generales<textarea id="h-obs" rows="2">' + esc(i.observaciones) + '</textarea></label>';
    html += '<label class="lbl-field">Observaciones S.O.<textarea id="c-obsso" rows="2">' + esc(c.observaciones_so) + '</textarea></label>';
    html += '<label class="lbl-field">Revisión Drive<textarea id="c-revd" rows="2">' + esc(c.revision_drive) + '</textarea></label>';
    html += '</div>';

  } else {
    // ---- FORMULARIO ORDENADO PARA CELULAR ----
    html += '<div class="sect-title">Información de la Línea y Plan</div><div class="g4">';
    html += '<label class="lbl-field">Número de Línea *<input id="h-nom" value="' + esc(iden) + '"></label>';
    html += '<label class="lbl-field">Cuenta<input id="c-cta" value="' + esc(c.cuenta) + '"></label>';
    html += '<label class="lbl-field">Nombre del Plan Actual<input id="h-pla" value="' + esc(i.plan_datos) + '"></label>';
    html += '<label class="lbl-field">Detalle del Plan<input id="c-detpla" value="' + esc(c.detalle_plan) + '"></label>';
    html += '<label class="lbl-field">CFM (Cargo Fijo)<input id="c-cfm" value="' + esc(c.cfm) + '"></label>';
    html += '<label class="lbl-field">Nombre Usuario<input id="h-usu" value="' + esc(i.usuario_asignado) + '"></label>';
    html += '<label class="lbl-field">Propiedad Línea<select id="h-tpl"><option '+(i.tipo_linea==='Corporativa'?'selected':'')+'>Corporativa</option><option '+(i.tipo_linea==='Personal'?'selected':'')+'>Personal</option></select></label>';
    html += '<label class="lbl-field">Cédula / NIT<input id="c-ced" value="' + esc(c.cedula_usuario) + '"></label>';
    html += '<label class="lbl-field">Fecha Activación<input type="date" id="c-fecact" value="' + esc(c.fecha_activacion) + '"></label>';
    html += '<label class="lbl-field">Área<input id="h-are" value="' + esc(i.area) + '"></label>';
    html += '<label class="lbl-field">Código Celular<input id="h-cod" value="' + esc(i.codigo) + '"></label>';
    html += '<label class="lbl-field">Estado<select id="h-est"><option '+(i.estado==='Activo'?'selected':'')+'>Activo</option><option '+(i.estado==='Mantenimiento'?'selected':'')+'>Mantenimiento</option><option '+(i.estado==='Baja'?'selected':'')+'>Baja</option></select></label>';
    html += '</div>';

    html += '<div class="sect-title">Equipo Físico (Hardware Celular)</div><div class="g4">';
    html += '<label class="lbl-field">Equipo / Propietario<input id="c-eqpro" value="' + esc(c.equipo_propiedad) + '"></label>';
    html += '<label class="lbl-field">IMEI *<input id="h-ser" value="' + esc(i.imei || i.serial) + '"></label>';
    html += '<label class="lbl-field">Serial Celular<input id="c-ser" value="' + esc(c.serial_adicional) + '"></label>';
    html += '<label class="lbl-field">Marca<input id="h-mar" value="' + esc(i.marca) + '"></label>';
    html += '<label class="lbl-field">Modelo<input id="h-mod" value="' + esc(i.modelo) + '"></label>';
    html += '<label class="lbl-field">Referencia<input id="c-ref" value="' + esc(c.referencia) + '"></label>';
    html += '<label class="lbl-field">CPU<input id="h-cpu" value="' + esc(i.procesador) + '"></label>';
    html += '<label class="lbl-field">MAC<input id="h-mac" value="' + esc(i.mac) + '"></label>';
    html += '<label class="lbl-field">Almacenamiento (ROM)<input id="c-rom" value="' + esc(c.rom) + '"></label>';
    html += '<label class="lbl-field">Memoria RAM<input id="h-ram" value="' + esc(i.memoria) + '"></label>';
    html += '<label class="lbl-field">Mantenimiento (Fecha)<input type="date" id="h-mto" value="' + esc(i.mantenimiento_programado) + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Facturación y Otros Datos</div><div class="g4">';
    html += '<label class="lbl-field">Fórmula<input id="c-for" value="' + esc(c.formula) + '"></label>';
    html += '<label class="lbl-field">Etiqueta<input id="c-eti" value="' + esc(c.etiqueta) + '"></label>';
    html += '<label class="lbl-field">Revisión<input id="c-rev" value="' + esc(c.revision) + '"></label>';
    html += '<label class="lbl-field">Número Factura<input id="c-numfac" value="' + esc(c.numero_factura) + '"></label>';
    html += '<label class="lbl-field">Fecha Factura<input type="date" id="c-fecfac" value="' + esc(c.fecha_factura) + '"></label>';
    html += '<label class="lbl-field">Productos Factura<input id="c-profac" value="' + esc(c.productos_factura) + '"></label>';
    html += '<label class="lbl-field">Precio / Valor<input type="number" id="c-pre" value="' + esc(i.precio || '') + '"></label>';
    html += '</div>';

    html += '<div class="sect-title">Observaciones</div><div class="g2">';
    html += '<label class="lbl-field">Observaciones Generales<textarea id="h-obs" rows="2">' + esc(i.observaciones) + '</textarea></label>';
    html += '<label class="lbl-field">Observación 1<textarea id="c-obs1" rows="2">' + esc(c.observacion_1) + '</textarea></label>';
    html += '</div>';
  }

  html += '<div style="margin-top:16px;display:flex;gap:10px;"><button class="btn btn-primary" id="btn-sav-hv">💾 ' + (item ? 'Actualizar Registro' : 'Guardar Nuevo Registro') + '</button><button class="btn btn-ghost" onclick="this.parentElement.parentElement.remove()">Cancelar</button></div>';

  w.innerHTML = html;
  
  w.querySelector('#btn-sav-hv').onclick = async function() {
    var val = (id) => { var e = w.querySelector('#'+id); return e ? e.value.trim() : ''; };
    
    var cod = val('h-cod');
    var nom = val('h-nom');
    if (!cod || !nom) return toast('Código y Nombre/Línea son obligatorios', false);

    var payload = {
      tipo_activo: esPC ? 'COMPUTO' : 'CELULAR', empresa: val('h-emp'), codigo: cod, nombre_equipo: esPC ? nom : 'CELULAR ' + nom,
      linea_numero: esPC ? '' : nom, usuario_asignado: val('h-usu'), area: val('h-are'), marca: val('h-mar'),
      modelo: val('h-mod'), serial: esPC ? val('h-ser') : '', imei: esPC ? '' : val('h-ser'), estado: val('h-est'),
      procesador: val('h-cpu'), memoria: val('h-ram'), disco: val('h-hdd'), sistema_operativo: val('h-so'),
      ip: val('h-ip'), mac: val('h-mac'), licencia_office: val('h-off'), antivirus: val('h-av'),
      plan_datos: val('h-pla'), tipo_linea: val('h-tpl'), mantenimiento_programado: val('h-mto'),
      observaciones: val('h-obs'), precio: parseFloat(val('c-pre')) || 0,
      config: {
        tipo: val('c-tip'), usuario_servidor: val('c-ususer'), mainboard: val('c-main'), tamano_disco: val('c-tamdis'),
        anydesk: val('c-any'), diadema: val('c-dia'), teclado: val('c-tec'), mouse: val('c-mou'), base_refrigerante: val('c-bas'),
        fecha_vencimiento_av: val('c-fvenav'), observaciones_so: val('c-obsso'), licencia: val('c-lic'), correo_licencia: val('c-corlic'),
        programas: val('c-prog'), formula: val('c-for'), etiqueta: val('c-eti'), pantalla_auxiliar: val('c-pau'),
        numero_factura: val('c-numfac'), fecha_factura: val('c-fecfac'), productos_factura: val('c-profac'), revision_drive: val('c-revd'),
        cuenta: val('c-cta'), detalle_plan: val('c-detpla'), cfm: val('c-cfm'), equipo_propiedad: val('c-eqpro'),
        fecha_activacion: val('c-fecact'), cedula_usuario: val('c-ced'), referencia: val('c-ref'), rom: val('c-rom'),
        serial_adicional: val('c-ser'), revision: val('c-rev'), observacion_1: val('c-obs1'), seriales: val('c-sers'), office_funciones: val('c-ofun')
      }
    };

    try {
      if(item) { await apiPut(API_HV + '/' + item.id, payload); toast('Actualizado correctamente ✓'); } 
      else { await apiPost(API_HV, payload); toast('Creado y sincronizado ✓'); }
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
    return `<tr><td><b>${i.codigo}</b></td><td>${i.nombre_equipo || i.linea_numero}</td><td>${i.usuario_asignado || 'N/A'}</td><td style="color:${esP ? 'var(--danger)' : 'var(--accent)'}; font-weight:700">${i.mantenimiento_programado || 'En Taller'}</td><td><span class="badge ${esP ? 'badge-warn' : 'badge-neutral'}">${i.estado}</span></td></tr>`;
  }).join('');
  var tw = ce('div', 'panel table-panel');
  tw.innerHTML = '<table class="data-table"><thead><tr><th>Código</th><th>Activo</th><th>Usuario</th><th>Fecha Programada</th><th>Estado</th></tr></thead><tbody>' + (rows || '<tr><td colspan="5" class="empty-state">No hay mantenimientos programados.</td></tr>') + '</tbody></table>';
  el.appendChild(tw);
  return el;
}