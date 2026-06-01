// HTMX response transformers for server-rendered fragments

// Render /api/status response as the status badge in the sidebar
document.body.addEventListener("htmx:beforeSwap", function (evt) {
  const target = evt.detail.target;
  if (!target) return;

  const id = target.id;
  const raw = evt.detail.xhr ? evt.detail.xhr.responseText : null;
  if (!raw) return;

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return;
  }

  if (id === "status-badge") {
    const color = data.running ? "bg-green-500" : "bg-red-500";
    const label = data.running ? "Running" : "Stopped";
    const host =
      data.host && data.port
        ? ` ${formatHostPort(data.host, data.port)}`
        : "";
    evt.detail.serverResponse = `
      <div id="status-badge"
           hx-get="/api/status" hx-trigger="every 5s" hx-swap="outerHTML"
           class="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-700 text-xs">
        <span class="w-2 h-2 rounded-full ${color}"></span>
        <span class="${data.running ? "text-green-400" : "text-red-400"}">${label}</span>
        <span class="text-gray-500">${host}</span>
      </div>`;
  }

  if (id === "stats-grid") {
    // Swapped with innerHTML into #stats-grid: return ONLY the cards (no wrapper
    // with the same id, which would otherwise nest a grid inside the grid).
    const cards = [
      { label: "Server", value: data.running ? "Running" : "Stopped", color: data.running ? "text-green-400" : "text-red-400" },
      { label: "ECUs", value: data.ecu_count ?? "—" },
      { label: "Services", value: data.service_count ?? "—" },
    ];
    evt.detail.serverResponse = cards.map(c => `
        <div class="bg-gray-800 rounded p-4 border border-gray-700">
          <div class="text-gray-400 text-xs mb-1">${c.label}</div>
          <div class="text-lg ${c.color ?? "text-white"}">${c.value}</div>
        </div>`).join("");
  }

  if (id === "gateway-data") {
    // Swapped with innerHTML into #gateway-data: return ONLY the inner content.
    // Re-emitting a #gateway-data wrapper with hx-trigger="load" caused infinite
    // recursive nesting of the panel.
    evt.detail.serverResponse = renderGateway(data);
  }

  if (id === "ecu-list" || id === "ecu-table") {
    const ecus = Array.isArray(data) ? data : [];
    // #ecu-list (dashboard) is swapped with innerHTML -> return inner content only.
    // #ecu-table (ECUs page) is swapped with outerHTML -> return the full element.
    const wrap = (inner) =>
      id === "ecu-table"
        ? `<div id="ecu-table" class="overflow-x-auto">${inner}</div>`
        : inner;

    if (ecus.length === 0) {
      evt.detail.serverResponse = wrap(`<div class="text-gray-500 text-xs">No ECUs configured.</div>`);
      return;
    }
    const onEcusPage = id === "ecu-table";
    const rows = ecus.map(e => `
      <tr class="border-b border-gray-700 hover:bg-gray-700/40">
        <td class="px-3 py-2">${e.target_address_hex}</td>
        <td class="px-3 py-2">${e.name}</td>
        <td class="px-3 py-2">${e.service_count}</td>
        <td class="px-3 py-2">
          <a href="/ecus/${e.target_address}/services"
             class="text-amber-400 hover:underline">Services →</a>
        </td>
        ${onEcusPage ? `<td class="px-3 py-2 text-right whitespace-nowrap">
          <button class="text-blue-400 hover:text-blue-300 text-xs mr-3"
                  onclick="editEcu(${e.target_address})">Edit</button>
          <button class="text-red-500 hover:text-red-400 text-xs"
                  onclick="deleteEcu(${e.target_address}, '${e.target_address_hex}')">Delete</button>
        </td>` : ""}
      </tr>`).join("");
    evt.detail.serverResponse = wrap(`
        <table class="w-full text-xs">
          <thead class="text-gray-400 border-b border-gray-700">
            <tr>
              <th class="px-3 py-2 text-left">Address</th>
              <th class="px-3 py-2 text-left">Name</th>
              <th class="px-3 py-2 text-left">Services</th>
              <th class="px-3 py-2"></th>
              ${onEcusPage ? `<th class="px-3 py-2"></th>` : ""}
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>`);
  }

  if (id === "service-table") {
    const services = Array.isArray(data) ? data : [];
    if (services.length === 0) {
      evt.detail.serverResponse = `<div id="service-table" class="text-gray-500 text-xs">No services configured.</div>`;
      return;
    }
    const ecuAddress = window.__ecuAddress;
    const rows = services.map(s => `
      <tr class="border-b border-gray-700 hover:bg-gray-700/40">
        <td class="px-3 py-2 font-bold">${s.name}</td>
        <td class="px-3 py-2 text-gray-400">${s.request ?? "—"}</td>
        <td class="px-3 py-2">${(s.responses || []).length} response(s)</td>
        <td class="px-3 py-2">${s.supports_functional ? "✓" : ""}</td>
        <td class="px-3 py-2 text-right whitespace-nowrap">
          <button class="text-blue-400 hover:text-blue-300 text-xs mr-3"
                  onclick="editService(${ecuAddress}, '${esc(s.name)}')">Edit</button>
          <button class="text-red-500 hover:text-red-400 text-xs"
                  onclick="deleteService(${ecuAddress}, '${esc(s.name)}')">Delete</button>
        </td>
      </tr>`).join("");
    evt.detail.serverResponse = `
      <div id="service-table" class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead class="text-gray-400 border-b border-gray-700">
            <tr>
              <th class="px-3 py-2 text-left">Name</th>
              <th class="px-3 py-2 text-left">Request</th>
              <th class="px-3 py-2 text-left">Responses</th>
              <th class="px-3 py-2 text-left">Functional</th>
              <th class="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }
});

// ── Gateway readable renderer ────────────────────────────────────────────────

function renderGateway(data) {
  const gw = (data && data.gateway) || {};
  const net = (data && data.network) || {};
  const proto = (data && data.protocol) || {};
  const veh = (data && data.vehicle) || {};

  const hex = (v, pad = 2) =>
    typeof v === "number" ? `0x${v.toString(16).toUpperCase().padStart(pad, "0")}` : (v ?? "—");

  const section = (title, rows) => `
    <div class="mb-4 last:mb-0">
      <div class="text-amber-400/80 uppercase tracking-wide text-[10px] mb-1">${title}</div>
      <dl class="grid grid-cols-2 gap-x-4 gap-y-1">
        ${rows.map(([k, v]) => `
          <dt class="text-gray-500">${k}</dt>
          <dd class="text-gray-200 break-all">${v ?? "—"}</dd>`).join("")}
      </dl>
    </div>`;

  return (
    section("Gateway", [
      ["Name", gw.name],
      ["Description", gw.description],
      ["Logical Address", hex(gw.logical_address, 4)],
    ]) +
    section("Network", [
      ["Host", net.host],
      ["Port", net.port],
      ["Max Connections", net.max_connections],
      ["Timeout", net.timeout],
    ]) +
    section("Protocol", [
      ["Version", hex(proto.version)],
      ["Inverse Version", hex(proto.inverse_version)],
    ]) +
    section("Vehicle", [
      ["VIN", veh.vin],
      ["EID", veh.eid],
      ["GID", veh.gid],
    ])
  );
}

// ── Shared UI helpers ─────────────────────────────────────────────────────────

function formatHostPort(host, port) {
  if (typeof host === "string" && host.includes(":") && !host.startsWith("[")) {
    return `[${host}]:${port}`;
  }
  return `${host}:${port}`;
}

const INP =
  "bg-gray-900 border border-gray-600 rounded px-2 py-1 text-white w-full";
const BTN_PRIMARY =
  "px-4 py-1.5 bg-amber-600 hover:bg-amber-500 rounded text-xs font-bold";
const BTN_SECONDARY =
  "px-4 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-xs";

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// Whether mutations should be written to YAML files (read from the sidebar toggle)
function doipPersist() {
  const el = document.getElementById("persist-toggle");
  return !!(el && el.checked);
}

function persistLabel() {
  return doipPersist()
    ? "permanently (written to file)"
    : "for this session only";
}

async function apiSend(method, path, body) {
  const url = new URL(path, location.origin);
  url.searchParams.set("persist", doipPersist() ? "true" : "false");
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(url, opts);
  let data = null;
  try {
    data = await res.json();
  } catch {
    /* no body */
  }
  if (!res.ok) {
    const msg = data && data.detail ? data.detail : `${res.status} ${res.statusText}`;
    throw new Error(msg);
  }
  return data;
}

async function apiGet(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

function toast(message, ok = true) {
  const t = document.createElement("div");
  t.className =
    "fixed bottom-4 right-4 z-[60] px-4 py-2 rounded text-xs shadow-lg text-white " +
    (ok ? "bg-green-700" : "bg-red-700");
  t.textContent = message;
  document.body.appendChild(t);
  setTimeout(() => t.remove(), 4000);
}

// ── Modal ──────────────────────────────────────────────────────────────────────

function openModal(title, html) {
  document.getElementById("modal-title").textContent = title;
  document.getElementById("modal-body").innerHTML = html;
  document.getElementById("modal-overlay").classList.remove("hidden");
  updatePersistNotes();
}

function closeModal() {
  const overlay = document.getElementById("modal-overlay");
  if (overlay) overlay.classList.add("hidden");
  const body = document.getElementById("modal-body");
  if (body) body.innerHTML = "";
}

function updatePersistNotes() {
  document
    .querySelectorAll(".persist-note")
    .forEach((el) => (el.textContent = persistLabel()));
}

// Keep any open form's persistence note in sync with the sidebar toggle.
document.addEventListener("change", (e) => {
  if (e.target && e.target.id === "persist-toggle") {
    const hint = document.getElementById("persist-hint");
    if (hint)
      hint.textContent = doipPersist()
        ? "Permanent (written to files)"
        : "Session only (temporary)";
    updatePersistNotes();
  }
});

function persistNoteHtml() {
  return `<div class="pt-2 text-[11px] text-gray-500">This change will be saved
    <span class="persist-note text-gray-300"></span>.</div>`;
}

// ── Refresh helpers ─────────────────────────────────────────────────────────────

function refreshEcuTable() {
  if (window.htmx)
    htmx.ajax("GET", "/api/ecus", { target: "#ecu-table", swap: "outerHTML" });
}
function refreshServiceTable(address) {
  if (window.htmx)
    htmx.ajax("GET", `/api/ecus/${address}/services`, {
      target: "#service-table",
      swap: "outerHTML",
    });
}
function refreshGateway() {
  if (window.htmx)
    htmx.ajax("GET", "/api/gateway", {
      target: "#gateway-data",
      swap: "innerHTML",
    });
}

// ── Gateway edit ────────────────────────────────────────────────────────────────

async function editGateway() {
  try {
    const data = await apiGet("/api/gateway");
    const gw = data.gateway || {};
    const net = data.network || {};
    const proto = data.protocol || {};
    openModal(
      "Edit Gateway",
      `<form onsubmit="return submitGateway(event)" class="space-y-3 text-xs">
        <label class="flex flex-col gap-1">Name
          <input name="name" value="${esc(gw.name)}" class="${INP}"/></label>
        <label class="flex flex-col gap-1">Description
          <input name="description" value="${esc(gw.description)}" class="${INP}"/></label>
        <div class="grid grid-cols-2 gap-3">
          <label class="flex flex-col gap-1">Host
            <input name="host" value="${esc(net.host)}" class="${INP}"/></label>
          <label class="flex flex-col gap-1">Port
            <input name="port" type="number" value="${net.port ?? ""}" class="${INP}"/></label>
          <label class="flex flex-col gap-1">Max Connections
            <input name="max_connections" type="number" value="${net.max_connections ?? ""}" class="${INP}"/></label>
          <label class="flex flex-col gap-1">Timeout (s)
            <input name="timeout" type="number" value="${net.timeout ?? ""}" class="${INP}"/></label>
          <label class="flex flex-col gap-1">Protocol Version (dec)
            <input name="version" type="number" value="${proto.version ?? ""}" class="${INP}"/></label>
          <label class="flex flex-col gap-1">Inverse Version (dec)
            <input name="inverse_version" type="number" value="${proto.inverse_version ?? ""}" class="${INP}"/></label>
        </div>
        ${persistNoteHtml()}
        <div class="flex gap-2 pt-1">
          <button type="submit" class="${BTN_PRIMARY}">Save</button>
          <button type="button" onclick="closeModal()" class="${BTN_SECONDARY}">Cancel</button>
        </div>
      </form>`
    );
  } catch (e) {
    toast(e.message, false);
  }
}

async function submitGateway(ev) {
  ev.preventDefault();
  const f = ev.target;
  const body = {
    name: f.name.value,
    description: f.description.value,
    network: {
      host: f.host.value,
      port: Number(f.port.value),
      max_connections: Number(f.max_connections.value),
      timeout: Number(f.timeout.value),
    },
    protocol: {
      version: Number(f.version.value),
      inverse_version: Number(f.inverse_version.value),
    },
  };
  try {
    await apiSend("PUT", "/api/gateway", body);
    closeModal();
    refreshGateway();
    toast(`Gateway saved ${persistLabel()}.`);
  } catch (e) {
    toast(e.message, false);
  }
  return false;
}

// ── ECU create / edit / delete ──────────────────────────────────────────────────

function ecuFormHtml(ecu) {
  const e = ecu || {};
  const isNew = e.target_address == null;
  return `<form onsubmit="return submitEcu(event, ${isNew ? "null" : e.target_address})" class="space-y-3 text-xs">
    ${
      isNew
        ? `<label class="flex flex-col gap-1">Target Address (decimal)
            <input name="target_address" type="number" required class="${INP}"/></label>`
        : `<div class="text-gray-500">Address: <span class="text-gray-300">${e.target_address_hex}</span></div>`
    }
    <label class="flex flex-col gap-1">Name
      <input name="name" value="${esc(e.name)}" required class="${INP}"/></label>
    <label class="flex flex-col gap-1">Functional Address (decimal)
      <input name="functional_address" type="number" value="${e.functional_address ?? 0}" class="${INP}"/></label>
    <label class="flex flex-col gap-1">Tester Addresses (comma-separated decimal)
      <input name="tester_addresses" value="${(e.tester_addresses || []).join(",")}" class="${INP}"/></label>
    <label class="flex flex-col gap-1">Description
      <input name="description" value="${esc(e.description)}" class="${INP}"/></label>
    ${persistNoteHtml()}
    <div class="flex gap-2 pt-1">
      <button type="submit" class="${BTN_PRIMARY}">Save</button>
      <button type="button" onclick="closeModal()" class="${BTN_SECONDARY}">Cancel</button>
    </div>
  </form>`;
}

function newEcu() {
  openModal("Add ECU", ecuFormHtml(null));
}

async function editEcu(address) {
  try {
    const ecu = await apiGet(`/api/ecus/${address}`);
    openModal(`Edit ECU ${ecu.target_address_hex}`, ecuFormHtml(ecu));
  } catch (e) {
    toast(e.message, false);
  }
}

function parseAddresses(value) {
  return (value || "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map(Number);
}

async function submitEcu(ev, address) {
  ev.preventDefault();
  const f = ev.target;
  try {
    if (address == null) {
      await apiSend("POST", "/api/ecus", {
        target_address: Number(f.target_address.value),
        name: f.name.value,
        functional_address: Number(f.functional_address.value || 0),
        tester_addresses: parseAddresses(f.tester_addresses.value),
        description: f.description.value || null,
      });
    } else {
      await apiSend("PUT", `/api/ecus/${address}`, {
        name: f.name.value,
        functional_address: Number(f.functional_address.value),
        tester_addresses: parseAddresses(f.tester_addresses.value),
        description: f.description.value || null,
      });
    }
    closeModal();
    refreshEcuTable();
    toast(`ECU saved ${persistLabel()}.`);
  } catch (e) {
    toast(e.message, false);
  }
  return false;
}

async function deleteEcu(address, hex) {
  if (!confirm(`Delete ECU ${hex} ${persistLabel()}?`)) return;
  try {
    await apiSend("DELETE", `/api/ecus/${address}`);
    refreshEcuTable();
    toast(`ECU ${hex} deleted ${persistLabel()}.`);
  } catch (e) {
    toast(e.message, false);
  }
}

// ── Service create / edit / delete ───────────────────────────────────────────────

function responsesToText(responses) {
  return (responses || [])
    .map((r) =>
      typeof r === "object" && r !== null
        ? `${r.response}${r.delay_ms != null ? ", " + r.delay_ms : ""}`
        : r
    )
    .join("\n");
}

function parseResponses(text) {
  return (text || "")
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean)
    .map((line) => {
      const parts = line.split(",").map((s) => s.trim());
      if (parts.length > 1 && parts[1] !== "") {
        return { response: parts[0], delay_ms: Number(parts[1]) };
      }
      return parts[0];
    });
}

function serviceFormHtml(address, svc) {
  const s = svc || {};
  const isNew = svc == null;
  return `<form onsubmit="return submitService(event, ${address}, ${isNew ? "null" : `'${esc(s.name)}'`})" class="space-y-3 text-xs">
    ${
      isNew
        ? `<label class="flex flex-col gap-1">Service Name
            <input name="service_name" required class="${INP}"/></label>`
        : `<div class="text-gray-500">Service: <span class="text-gray-300">${esc(s.name)}</span></div>`
    }
    <label class="flex flex-col gap-1">Request (hex, e.g. 0x22F190)
      <input name="request" value="${esc(s.request)}" required class="${INP}"/></label>
    <label class="flex flex-col gap-1">Responses (one per line; optional "hex, delay_ms")
      <textarea name="responses" rows="4" class="${INP} font-mono">${esc(responsesToText(s.responses))}</textarea></label>
    <label class="flex flex-col gap-1">Description
      <input name="description" value="${esc(s.description)}" class="${INP}"/></label>
    <div class="flex gap-6">
      <label class="flex items-center gap-2"><input type="checkbox" name="supports_functional" ${s.supports_functional ? "checked" : ""}/> Supports functional</label>
      <label class="flex items-center gap-2"><input type="checkbox" name="no_response" ${s.no_response ? "checked" : ""}/> No response</label>
    </div>
    ${persistNoteHtml()}
    <div class="flex gap-2 pt-1">
      <button type="submit" class="${BTN_PRIMARY}">Save</button>
      <button type="button" onclick="closeModal()" class="${BTN_SECONDARY}">Cancel</button>
    </div>
  </form>`;
}

function newService(address) {
  openModal("Add Service", serviceFormHtml(address, null));
}

async function editService(address, name) {
  try {
    const svc = await apiGet(`/api/ecus/${address}/services/${encodeURIComponent(name)}`);
    openModal(`Edit Service ${esc(name)}`, serviceFormHtml(address, svc));
  } catch (e) {
    toast(e.message, false);
  }
}

async function submitService(ev, address, name) {
  ev.preventDefault();
  const f = ev.target;
  const body = {
    request: f.request.value,
    responses: parseResponses(f.responses.value),
    description: f.description.value || null,
    supports_functional: f.supports_functional.checked,
    no_response: f.no_response.checked,
  };
  try {
    if (name == null) {
      const svcName = f.service_name.value.trim();
      await apiSend(
        "POST",
        `/api/ecus/${address}/services?service_name=${encodeURIComponent(svcName)}`,
        body
      );
    } else {
      await apiSend(
        "PUT",
        `/api/ecus/${address}/services/${encodeURIComponent(name)}`,
        body
      );
    }
    closeModal();
    refreshServiceTable(address);
    toast(`Service saved ${persistLabel()}.`);
  } catch (e) {
    toast(e.message, false);
  }
  return false;
}

async function deleteService(address, name) {
  if (!confirm(`Delete service ${name} ${persistLabel()}?`)) return;
  try {
    await apiSend("DELETE", `/api/ecus/${address}/services/${encodeURIComponent(name)}`);
    refreshServiceTable(address);
    toast(`Service ${name} deleted ${persistLabel()}.`);
  } catch (e) {
    toast(e.message, false);
  }
}
