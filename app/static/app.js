const API = "/api/equipos";
let equipoEditandoId = null;

// ---------------------------------------------------------------
// Utilidades
// ---------------------------------------------------------------
function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2600);
}

function badgeEstado(estado) {
  if (!estado) return `<span class="badge badge-neutral">Sin registrar</span>`;
  const up = estado.toUpperCase();
  if (up.includes("FUNCIONAL")) return `<span class="badge badge-ok">${estado}</span>`;
  if (up.includes("LENTO") || up.includes("REVISI")) return `<span class="badge badge-warn">${estado}</span>`;
  if (up.includes("CHATARR") || up.includes("DONAD")) return `<span class="badge badge-danger">${estado}</span>`;
  return `<span class="badge badge-neutral">${estado}</span>`;
}

function money(n) {
  if (!n) return "$ 0";
  return "$ " + Number(n).toLocaleString("es-CO", { maximumFractionDigits: 0 });
}

// ---------------------------------------------------------------
// Carga inicial
// ---------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  cargarFiltros();
  cargarTabla();
  cargarDashboard();

  document.getElementById("btnNuevo").addEventListener("click", () => abrirDrawer());
  document.getElementById("btnCerrarDrawer").addEventListener("click", cerrarDrawer);
  document.getElementById("btnCancelar").addEventListener("click", cerrarDrawer);
  document.getElementById("drawerOverlay").addEventListener("click", (e) => {
    if (e.target.id === "drawerOverlay") cerrarDrawer();
  });
  document.getElementById("formEquipo").addEventListener("submit", guardarEquipo);
  document.getElementById("btnEliminar").addEventListener("click", eliminarEquipo);
  document.getElementById("btnExport").addEventListener("click", () => {
    window.location.href = `${API}/exportar/csv`;
  });
  document.getElementById("btnLimpiarFiltros").addEventListener("click", () => {
    document.getElementById("fBuscar").value = "";
    document.getElementById("fEmpresa").value = "";
    document.getElementById("fArea").value = "";
    document.getElementById("fTipo").value = "";
    document.getElementById("fEstado").value = "";
    cargarTabla();
  });

  ["fBuscar", "fEmpresa", "fArea", "fTipo", "fEstado"].forEach((id) => {
    document.getElementById(id).addEventListener("input", debounce(cargarTabla, 300));
  });
});

function debounce(fn, delay) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ---------------------------------------------------------------
// Filtros dinámicos
// ---------------------------------------------------------------
async function cargarFiltros() {
  const res = await fetch(`${API}/meta/filtros`);
  const data = await res.json();
  llenarSelect("fEmpresa", data.empresas);
  llenarSelect("fArea", data.areas);
  llenarSelect("fTipo", data.tipos_equipo);
  llenarSelect("fEstado", data.estados_equipo);
}

function llenarSelect(id, valores) {
  const sel = document.getElementById(id);
  const actual = sel.value;
  const primero = sel.options[0].outerHTML;
  sel.innerHTML = primero + valores.map(v => `<option value="${v}">${v}</option>`).join("");
  sel.value = actual;
}

// ---------------------------------------------------------------
// Tabla principal
// ---------------------------------------------------------------
async function cargarTabla() {
  const params = new URLSearchParams();
  const q = document.getElementById("fBuscar").value.trim();
  const empresa = document.getElementById("fEmpresa").value;
  const area = document.getElementById("fArea").value;
  const tipo = document.getElementById("fTipo").value;
  const estado = document.getElementById("fEstado").value;

  if (q) params.set("q", q);
  if (empresa) params.set("empresa", empresa);
  if (area) params.set("area", area);
  if (tipo) params.set("tipo_equipo", tipo);
  if (estado) params.set("estado_equipo", estado);

  const res = await fetch(`${API}?${params.toString()}`);
  const equipos = await res.json();
  const tbody = document.getElementById("tablaBody");

  if (!equipos.length) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No se encontraron equipos con esos filtros.</td></tr>`;
    return;
  }

  tbody.innerHTML = equipos.map(e => `
    <tr>
      <td>${e.equipo || ""}</td>
      <td>${e.empresa || ""}</td>
      <td>${e.area || ""}</td>
      <td>${e.usuario_asignado || "—"}</td>
      <td>${e.tipo_equipo || "—"}</td>
      <td>${e.ip || "—"}</td>
      <td>${badgeEstado(e.estado_equipo)}</td>
      <td><button class="row-btn" onclick="abrirDrawer(${e.id})">Ver / editar</button></td>
    </tr>
  `).join("");
}

// ---------------------------------------------------------------
// Dashboard / analítica
// ---------------------------------------------------------------
async function cargarDashboard() {
  const res = await fetch("/api/dashboard/resumen");
  const data = await res.json();

  document.getElementById("statTotal").textContent = data.total_equipos;
  document.getElementById("statRiesgo").textContent = data.total_en_riesgo;
  document.getElementById("statSinMtto").textContent = data.equipos_sin_mantenimiento_registrado;
  document.getElementById("statValor").textContent = money(data.valor_estimado_parque_equipos);

  renderBarChart("chartArea", data.por_area);
  renderBarChart("chartEstado", data.por_estado);
}

function renderBarChart(containerId, dict) {
  const entries = Object.entries(dict);
  const max = Math.max(...entries.map(([, v]) => v), 1);
  const el = document.getElementById(containerId);
  if (!entries.length) { el.innerHTML = `<p style="color:var(--text-faint);font-size:13px">Sin datos aún.</p>`; return; }
  el.innerHTML = entries.map(([label, count]) => `
    <div class="bar-row">
      <span class="label" title="${label}">${label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(count / max) * 100}%"></div></div>
      <span class="count">${count}</span>
    </div>
  `).join("");
}

// ---------------------------------------------------------------
// Drawer: crear / editar
// ---------------------------------------------------------------
async function abrirDrawer(id = null) {
  equipoEditandoId = id;
  document.getElementById("formEquipo").reset();
  document.getElementById("btnEliminar").style.display = id ? "inline-block" : "none";
  document.getElementById("drawerTitle").textContent = id ? "Editar hoja de vida" : "Nueva hoja de vida";

  if (id) {
    const res = await fetch(`${API}/${id}`);
    const e = await res.json();
    Object.keys(e).forEach(campo => {
      const input = document.getElementById(`f_${campo}`);
      if (input) input.value = e[campo] ?? "";
    });
  }

  document.getElementById("drawerOverlay").classList.add("open");
}

function cerrarDrawer() {
  document.getElementById("drawerOverlay").classList.remove("open");
}

function recolectarDatosFormulario() {
  const campos = [
    "empresa", "equipo", "codigo", "area", "nombre_equipo", "tipo_equipo", "usuario_asignado",
    "estado_equipo", "cpu", "procesador", "memoria", "mainboard", "tipo_disco", "tamano_disco",
    "marca", "serial", "ip", "mac", "anydesk_id", "dominio", "sistema_operativo", "antivirus",
    "antivirus_vigencia", "office", "fecha_ultimo_mantenimiento", "observacion_estado",
    "observaciones_finales",
  ];
  const datos = {};
  campos.forEach(c => {
    const el = document.getElementById(`f_${c}`);
    if (el && el.value !== "") datos[c] = el.value;
  });
  return datos;
}

async function guardarEquipo(evt) {
  evt.preventDefault();
  const datos = recolectarDatosFormulario();

  try {
    let res;
    if (equipoEditandoId) {
      res = await fetch(`${API}/${equipoEditandoId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
    } else {
      res = await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      });
    }

    if (!res.ok) {
      const err = await res.json();
      toast(err.detail || "No se pudo guardar el registro");
      return;
    }

    toast(equipoEditandoId ? "Hoja de vida actualizada" : "Hoja de vida creada correctamente");
    cerrarDrawer();
    cargarTabla();
    cargarDashboard();
    cargarFiltros();
  } catch (e) {
    toast("Error de conexión con el servidor");
  }
}

async function eliminarEquipo() {
  if (!equipoEditandoId) return;
  if (!confirm("¿Eliminar esta hoja de vida? Esta acción no se puede deshacer.")) return;

  const res = await fetch(`${API}/${equipoEditandoId}`, { method: "DELETE" });
  if (res.ok) {
    toast("Equipo eliminado");
    cerrarDrawer();
    cargarTabla();
    cargarDashboard();
  } else {
    toast("No se pudo eliminar el registro");
  }
}
