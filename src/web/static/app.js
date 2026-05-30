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
    const host = data.host && data.port ? ` ${data.host}:${data.port}` : "";
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
    const cards = [
      { label: "Server", value: data.running ? "Running" : "Stopped", color: data.running ? "text-green-400" : "text-red-400" },
      { label: "ECUs", value: data.ecu_count ?? "—" },
      { label: "Services", value: data.service_count ?? "—" },
    ];
    evt.detail.serverResponse = `<div id="stats-grid" class="col-span-3 grid grid-cols-3 gap-4">` +
      cards.map(c => `
        <div class="bg-gray-800 rounded p-4 border border-gray-700">
          <div class="text-gray-400 text-xs mb-1">${c.label}</div>
          <div class="text-lg ${c.color ?? "text-white"}">${c.value}</div>
        </div>`).join("") + `</div>`;
  }

  if (id === "gateway-data") {
    evt.detail.serverResponse = `<div id="gateway-data" hx-get="/api/gateway" hx-trigger="load" hx-swap="innerHTML" class="bg-gray-800 rounded border border-gray-700 p-4 text-xs leading-6"><pre class="overflow-auto">${JSON.stringify(data, null, 2)}</pre></div>`;
  }

  if (id === "ecu-list" || id === "ecu-table") {
    const ecus = Array.isArray(data) ? data : [];
    if (ecus.length === 0) {
      evt.detail.serverResponse = `<div id="${id}" class="text-gray-500 text-xs">No ECUs configured.</div>`;
      return;
    }
    const rows = ecus.map(e => `
      <tr class="border-b border-gray-700 hover:bg-gray-700/40">
        <td class="px-3 py-2">${e.target_address_hex}</td>
        <td class="px-3 py-2">${e.name}</td>
        <td class="px-3 py-2">${e.service_count}</td>
        <td class="px-3 py-2">
          <a href="/ecus/${e.target_address}/services"
             class="text-amber-400 hover:underline">Services →</a>
        </td>
        <td class="px-3 py-2">
          <button class="text-red-500 hover:text-red-400 text-xs"
                  hx-delete="/api/ecus/${e.target_address}"
                  hx-confirm="Delete ECU ${e.target_address_hex}?"
                  hx-target="#ecu-table"
                  hx-swap="outerHTML">Delete</button>
        </td>
      </tr>`).join("");
    evt.detail.serverResponse = `
      <div id="${id}" class="overflow-x-auto">
        <table class="w-full text-xs">
          <thead class="text-gray-400 border-b border-gray-700">
            <tr>
              <th class="px-3 py-2 text-left">Address</th>
              <th class="px-3 py-2 text-left">Name</th>
              <th class="px-3 py-2 text-left">Services</th>
              <th class="px-3 py-2"></th>
              <th class="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  if (id === "service-table") {
    const services = Array.isArray(data) ? data : [];
    if (services.length === 0) {
      evt.detail.serverResponse = `<div id="service-table" class="text-gray-500 text-xs">No services configured.</div>`;
      return;
    }
    const url = location.pathname;
    const rows = services.map(s => `
      <tr class="border-b border-gray-700 hover:bg-gray-700/40">
        <td class="px-3 py-2 font-bold">${s.name}</td>
        <td class="px-3 py-2 text-gray-400">${s.request ?? "—"}</td>
        <td class="px-3 py-2">${(s.responses || []).length} response(s)</td>
        <td class="px-3 py-2">${s.supports_functional ? "✓" : ""}</td>
        <td class="px-3 py-2">
          <button class="text-red-500 hover:text-red-400 text-xs"
                  hx-delete="${url}/${s.name}"
                  hx-confirm="Delete service ${s.name}?"
                  hx-target="#service-table"
                  hx-swap="outerHTML">Delete</button>
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
