function showBajaForm(parent) {
  var ex = parent.querySelector('.bj-fw'); if (ex) { ex.remove(); return; }
  var wrap = ce('div', 'bj-fw'); wrap.style.marginBottom = '20px';

  var c1 = ce('div', 'gh-card');
  var sh = '<option value="">-- Selecciona un equipo disponible --</option>';
  INV.forEach(function (inv) { sh += '<option value="' + inv.id + '">' + esc(inv.nombre) + ' | ' + esc(inv.marca || '') + ' ' + esc(inv.modelo || '') + ' [S/N: ' + esc(inv.serial || 'N/A') + '] — Stock: ' + inv.cantidad_stock + '</option>'; });
  c1.innerHTML = '<div class="sh"><div class="sn">1</div>Equipo a dar de baja</div><label class="lbl-field">Seleccionar equipo *<select id="bj-s">' + sh + '</select></label><div id="bj-inf" style="display:none;margin:12px 0"></div><div class="g2"><label class="lbl-field">Cantidad a dar de baja *<input type="number" id="bj-q" value="1" min="1"></label><label class="lbl-field">Fecha de baja *<input type="text" id="bj-f" value="' + fechaHoraActual() + '" readonly></label></div>';
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
  var spBj = mkSig('🖊️ Firma del responsable *'); c5.appendChild(spBj.el); wrap.appendChild(c5);

  var ff = ce('div', 'gh-ffooter');
  var bCa = ce('button', 'btn btn-ghost'); bCa.textContent = 'Cancelar'; bCa.onclick = function () { wrap.remove(); };
  var bSv = ce('button', 'btn btn-primary'); bSv.textContent = '🗑️ Registrar baja y generar acta';
  
  bSv.onclick = async function () {
    var selEl = ge('bj-s');
    var rn = ge('bj-rn').value.trim(); 
    if (!rn) return toast('El nombre del responsable es obligatorio', false);
    
    var firmaBj = spBj.getImg();
    if (!firmaBj) return toast('La firma del responsable es obligatoria', false);
    
    var cnt = parseInt(ge('bj-q').value) || 1;
    var sw = []; c4.querySelectorAll('#bj-sw input:checked').forEach(function (cb) { sw.push(cb.value); });
    
    // Captura segura de Inventario
    var itemIdVal = null, nomEq = "Equipo dado de baja", catEq = "", marEq = "", modEq = "", serEq = "";
    if (selEl && selEl.value) {
      var si = INV.find(function (i) { return String(i.id) === selEl.value; });
      if (si) {
        if (cnt > si.cantidad_stock) return toast('Cantidad supera el stock actual (' + si.cantidad_stock + ')', false);
        itemIdVal = String(si.id); nomEq = si.nombre; catEq = si.categoria; marEq = si.marca; modEq = si.modelo; serEq = si.serial;
      }
    } else {
      nomEq = ge('bj-hn').value.trim() || 'Activo no inventariado';
    }

    var payload = {
      itemId: itemIdVal, nombre: nomEq, categoria: catEq, marca: marEq, modelo: modEq, serial: serEq,
      cantidad: cnt, motivo: ge('bj-m').value, disposicion: ge('bj-dp').value, entidad: ge('bj-ent').value.trim(),
      responsNombre: rn, responsCargo: ge('bj-rc').value.trim(), area: ge('bj-ra').value, observaciones: ge('bj-ob').value.trim(), firma: firmaBj,
      config: { hostname: ge('bj-hn').value.trim(), disco: ge('bj-dk').value.trim(), ram: ge('bj-rm').value.trim(), cpu: ge('bj-cp').value.trim(), impresora: ge('bj-ip').value.trim(), jefe: ge('bj-ji').value.trim(), ext: ge('bj-ex').value.trim(), email: ge('bj-em').value.trim(), software: sw, fechaBaja: fechaHoraActual() },
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
    var inf = ge('bj-inf');
    var m = INV.find(function (i) { return String(i.id) === ge('bj-s').value; });
    if (m) { inf.style.display = 'block'; inf.innerHTML = '<div class="g4"><div><span class="lbl-field" style="display:block">Categoría</span><b>' + esc(m.categoria || '') + '</b></div><div><span class="lbl-field" style="display:block">Marca</span><b>' + esc(m.marca || '') + '</b></div><div><span class="lbl-field" style="display:block">Modelo</span><b>' + esc(m.modelo || '') + '</b></div><div><span class="lbl-field" style="display:block">Stock actual</span><b style="color:var(--accent)">' + m.cantidad_stock + '</b></div></div>'; ge('bj-hn').value = m.nombre; }
    else { inf.style.display = 'none'; }
  };
  var tw2 = parent.querySelector('.table-panel'); parent.insertBefore(wrap, tw2);
}