import {display, filterRows, sortRows, statistics, groupRows, toCsv, projectSummary, bessProjectSummary, hasLocation, dataCenterCapacity, dataCenterScopes, windCapacity, windEvidence, windTurbineSummary} from "./database-core.mjs";

const root = document.querySelector("[data-database]") || document.getElementById("pv-database");
const isWind = root.dataset.database === "wind";
const isDataCenter = root.dataset.database === "data_centers";
const isBess = root.dataset.database === "bess";
const isBessOem = root.dataset.database === "bess_oem";
const el = (id) => document.getElementById(`db-${id}`);
const make = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
};
const number = (n) => n == null ? "Unknown" : n.toLocaleString(undefined, {maximumFractionDigits: 3});
const base = new URL(root.dataset.base, document.baseURI);
let index, rows = [], filtered = [], visible = [], page = 0, sortKey = "name", descending = false;
let tableName = "", token = 0, currentRecord;
let projectMap, mapModule, mapRequest = 0;
const categories = ["owner_names", "operator_names", "model", "turbine_model", "foundation_type", "iec_class", "platform", "facility_type", "equipment_category", "aggregation_role", "it_capacity_basis", "grid_capacity_basis", "facility_capacity_basis", "cooling_technology", "manufacturer", "country_code", "technology", "status", "quality_status", "market_scope", "bifacial", "chemistry", "configuration", "power_basis", "energy_basis", "architecture", "market_segment", "record_scope", "product_status", "energy_boundary", "efficiency_boundary"];

function options(element, entries, selected) {
  element.replaceChildren(...entries.map(([value, label]) => {
    const option = make("option", label); option.value = value; return option;
  }));
  if (selected !== undefined && entries.some(([key]) => key === selected)) element.value = selected;
}
function fieldLabel(name) {
  const unit = index.fields[name]?.unit;
  return name + (unit ? ` [${unit}]` : "");
}
async function fetchJson(name, sha) {
  const response = await fetch(new URL(name, base), {cache: "no-cache"});
  if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
  const bytes = await response.arrayBuffer();
  if (sha) {
    if (!globalThis.crypto?.subtle) throw new Error("Checksum verification requires HTTPS or localhost.");
    const digest = [...new Uint8Array(await crypto.subtle.digest("SHA-256", bytes))]
      .map((b) => b.toString(16).padStart(2, "0")).join("");
    if (digest !== sha) throw new Error("Snapshot changed while loading. Retry to refresh all files.");
  }
  return JSON.parse(new TextDecoder().decode(bytes));
}
function failure(error) {
  el("status").textContent = `Could not load the database: ${error.message} Use Retry or the Parquet downloads below. For local files, serve the built docs over HTTP.`;
  el("retry").hidden = false; el("workspace").hidden = true;
}
async function initialize() {
  el("retry").hidden = true; el("status").textContent = "Loading database catalogue…";
  try {
    index = await fetchJson("viewer-index.json");
    const desired = new URL(location.href).searchParams.get("table");
    options(el("table"), Object.entries(index.tables).map(([key, value]) =>
      [key, `${key.replaceAll("_", " ")} · ${number(value.rows)}`]), desired || tableName);
    await loadTable();
  } catch (error) { failure(error); }
}
async function loadTable() {
  const request = ++token, entity = el("table").value, info = index.tables[entity];
  tableName = entity; el("workspace").hidden = true; el("retry").hidden = true;
  el("status").textContent = `Loading ${entity.replaceAll("_", " ")} (${(info.viewer_bytes / 1e6).toFixed(1)} MB)…`;
  try {
    const data = await fetchJson(info.viewer, info.viewer_sha256);
    if (request !== token) return;
    if (data.parquet_sha256 !== info.parquet_sha256 || data.rows.length !== info.rows) throw new Error("Snapshot metadata mismatch; retry the latest build.");
    rows = data.rows.map((values) => Object.fromEntries(data.columns.map((key, i) => [key, values[i]])));
    const populated = new Set(data.columns);
    const fields = categories.filter((key) => populated.has(key));
    const group = entity === "projects" ? "country_code" : "manufacturer";
    options(el("filter-field"), [["", "No category filter"], ...fields.map((key) => [key, key])]);
    options(el("group"), fields.map((key) => [key, key]), group);
    const metrics = Object.entries(index.fields).filter(([key, meta]) =>
      ["float", "int"].includes(meta.type) && populated.has(key)).map(([key]) => [key, fieldLabel(key)]);
    options(el("metric"), [["", "No numeric field"], ...metrics],
      entity === "projects" ? (isWind ? "installed_capacity_mw" : isDataCenter ? "it_capacity_mw" : isBess ? "energy_capacity_mwh" : "capacity_ac_mw") : isWind ? "rated_power_kw" : isDataCenter ? "accelerator_power_w" : isBessOem ? "energy_capacity_mwh" : entity === "modules" ? "pmax_stc_w" : metrics[0]?.[0]);
    el("parquet").href = new URL(info.parquet, base).href;
    el("version").textContent = `Schema ${index.schema_version} · ${number(info.rows)} records · ${Object.keys(index.fields).length} columns`;
    el("provenance").textContent = `Parquet SHA-256: ${info.parquet_sha256}. Browser projection checksum verified; all records included.`;
    if (el("title")) el("title").textContent = isWind ? `Wind ${entity[0].toUpperCase() + entity.slice(1)}` : isDataCenter ? (entity === "projects" ? "Data Center Projects" : "Data Center Equipment") : isBess ? "BESS project intelligence" : isBessOem ? "BESS equipment intelligence" : entity === "projects" ? "PV project intelligence" : "PV equipment intelligence";
    resetFilters(); defaultColumns(); renderColumns();
    el("workspace").hidden = false;
    render();
    el("status").textContent = `Loaded ${number(rows.length)} ${entity.replaceAll("_", " ")} records.`;
    const url = new URL(location.href); url.searchParams.set("table", entity); history.replaceState(null, "", url);
  } catch (error) { if (request === token) failure(error); }
}
function defaultColumns() {
  const specific = tableName === "projects" ? (isWind ? ["country_code", "technology", "status", "status_as_of", "installed_capacity_mw", "planned_capacity_mw", "historical_capacity_mw", "turbine_count", "aggregation_role"] : isDataCenter ? ["country_code", "record_scope", "status", "it_capacity_mw", "it_capacity_basis", "grid_capacity_mw", "facility_capacity_mw", "cooling_technology"] : isBess ? ["country_code", "status", "status_as_of", "power_capacity_mw", "energy_capacity_mwh", "chemistry"] : ["country_code", "status", "capacity_ac_mw", "capacity_dc_mw"]) :
    isWind && tableName === "turbines" ? ["project_record_id", "country_code", "status", "manufacturer", "turbine_model", "rotor_diameter_m", "hub_height_m"] : isWind ? ["manufacturer", "model", "rated_power_kw", "rotor_diameter_m", "equipment_category", "curve_kind", "curve_origin"] : isDataCenter ? ["manufacturer", "model", "variant", "equipment_category", "input_power_kw", "accelerator_power_w", "memory_gb", "power_conditions"] : isBessOem ? ["manufacturer", "model", "variant", "record_scope", "energy_capacity_mwh", "energy_basis", "power_capacity_mw", "power_basis", "apparent_power_mva", "chemistry", "product_status"] : ["manufacturer", "model", el("metric").value];
  visible = [...new Set(["name", ...specific, "quality_status", "updated_at", "source_urls"])].filter((key) => key in index.fields);
}
function renderColumns() {
  el("columns").replaceChildren(...Object.keys(index.fields).map((key) => {
    const label = make("label"), input = make("input"); input.type = "checkbox"; input.value = key;
    input.checked = visible.includes(key); label.title = index.fields[key].description;
    input.addEventListener("change", () => {
      visible = input.checked ? [...visible, key] : visible.filter((item) => item !== key);
      renderTable();
    });
    label.append(input, make("span", fieldLabel(key))); return label;
  }));
}
function categoryOptions() {
  const field = el("filter-field").value;
  const values = field ? [...new Set(rows.map((row) => JSON.stringify(row[field] ?? null)))] : [];
  values.sort((a, b) => display(JSON.parse(a)).localeCompare(display(JSON.parse(b))));
  options(el("filter-value"), [["", "All values"], ...values.map((value) => [value, display(JSON.parse(value))])]);
  el("filter-value").disabled = !field;
}
function resetFilters() {
  for (const key of ["search", "min", "max", "filter-field"]) el(key).value = "";
  el("missing").value = "all"; el("aggregation").value = "count";
  page = 0; sortKey = "name"; descending = false; categoryOptions();
}
function render() {
  const metric = el("metric").value;
  filtered = filterRows(rows, {search: el("search").value, field: el("filter-field").value,
    equals: el("filter-value").value, metric, min: el("min").value, max: el("max").value, missing: el("missing").value});
  const stats = statistics(filtered, metric);
  const projects = tableName === "projects" && !isBessOem && !isDataCenter && !isWind;
  const summary = [[number(filtered.length), projects ? "Matching projects" : "Matching records", `of ${number(rows.length)} in catalogue`]];
  if (isWind && tableName === "projects") {
    const evidence = windEvidence(filtered);
    const eligible = filtered.filter(r => ["independent", "child"].includes(r.aggregation_role) && !r.overlap_group);
    summary.push([number(new Set(filtered.map(r => r.country_code).filter(Boolean)).size), "Countries", "Catalogue coverage"],
      [number(statistics(eligible, "turbine_count").reportedSum), "Reported turbines", "Only reviewed non-overlapping project scopes"],
      [number(filtered.filter(hasLocation).length), "Mapped records", `${number(filtered.filter(r => !hasLocation(r)).length)} without coordinates; administrative locations remain in the table`],
      [number(evidence.lifecycleKnown), "Dated lifecycle evidence", `${number(evidence.lifecycleUnknown)} unknown; inspect observation dates`],
      [number(evidence.scopeExcluded), "Excluded project scopes", "Known lifecycle alone does not resolve phase or repowering overlap"]);
    for (const [field, label] of [["installed_capacity_mw", "Installed MW"], ["commissioned_capacity_mw", "Commissioned MW"], ["planned_capacity_mw", "Planned MW"], ["awarded_capacity_mw", "Awarded MW"], ["export_capacity_mw", "Export MW"]]) {
      const total = windCapacity(filtered, field), entries = Object.entries(total.byStatus);
      summary.push([entries.length ? entries.map(([status,v]) => `${number(v.reported_mw)} ${status.replaceAll("_", " ")}`).join("; ") : "Unknown", label,
        `${total.unknown} unknown · ${total.excluded} aggregate/unresolved exclusions`]);
    }
    summary.push([number(filtered.filter(r => r.historical_capacity_mw != null).length), "Historical capacity records", "Excluded until scope/status reconciliation; never a current MW total"]);
  } else if (isWind && tableName === "turbines") {
    const inventory = windTurbineSummary(filtered);
    summary.push([number(inventory.projects), "Linked project identities", "Explicit registry parent links"],
      [number(inventory.manufacturers), "Reported manufacturers", `${inventory.manufacturerUnknown} unknown; inventory labels, not OEM validation`],
      [number(inventory.located), "Mapped turbine records", "Includes planned, erected and historical rows"],
      [number(inventory.lifecycleUnknown), "Lifecycle unknown", "Erected alone does not establish operation"]);
  } else if (isWind && tableName === "equipment") {
    summary.push([number(new Set(filtered.map(r => r.manufacturer).filter(Boolean)).size), "Manufacturers"],
      [number(stats.known), "Metric reported"], [number(stats.missing), "Metric unknown"], [number(stats.mean), "Metric mean", fieldLabel(metric)]);
  } else if (isDataCenter && tableName === "projects") {
    const scopes = dataCenterScopes(filtered);
    summary.push([number(scopes.facilities), "Facility records", `${scopes.phases} phase records · ${scopes.campuses} campus aggregates`],
      [number(new Set(filtered.map(r => r.country_code).filter(Boolean)).size), "Countries", "Reported country codes"],
      [number(filtered.filter(r => r.status === "operational").length), "Operational observations", "Includes labelled campuses; status is dated evidence"]);
    for (const [field, label] of [["it_capacity_mw", "IT capacity · MW"], ["grid_capacity_mw", "Grid capacity · MW"], ["facility_capacity_mw", "Facility demand · MW"]]) {
      const total = dataCenterCapacity(filtered, field), entries = Object.entries(total.byBasis);
      summary.push([entries.length ? entries.map(([basis,v]) => `${number(v.reported_mw)} ${basis.replaceAll("_", " ")}`).join("; ") : "Unknown", label,
        `${total.unknown} unknown · ${total.excluded} campus/overlap exclusions`]);
    }
  } else if (projects && isBess) {
    const totals = bessProjectSummary(filtered);
    summary.push([number(totals.power.reportedSum), "Total power · MW", `${number(totals.power.known)} reported · ${number(totals.power.missing)} unknown`, "db-stat-ac"],
      [number(totals.energy.reportedSum), "Total energy · MWh", `${number(totals.energy.known)} reported · ${number(totals.energy.missing)} unknown`],
      [number(totals.countries), "Countries", "Reported country codes"],
      [number(totals.located), "Mapped projects", `${number(filtered.length - totals.located)} without valid coordinates`],
      [filtered.length ? `${Math.round(100 * totals.energy.known / filtered.length)}%` : "—", "Energy data coverage", "Share with reported MWh"]);
  } else if (projects) {
    const totals = projectSummary(filtered);
    summary.push([number(totals.ac.reportedSum), "Total AC capacity · MW", `${number(totals.ac.known)} reported · ${number(totals.ac.missing)} unknown`, "db-stat-ac"],
      [number(totals.dc.reportedSum), "Total DC capacity · MW", `${number(totals.dc.known)} reported · ${number(totals.dc.missing)} unknown`],
      [number(totals.countries), "Countries", "Reported country codes"],
      [number(totals.located), "Mapped projects", `${number(filtered.length - totals.located)} without valid coordinates`],
      [filtered.length ? `${Math.round(100 * totals.ac.known / filtered.length)}%` : "—", "AC data coverage", "Share with reported AC MW"]);
  } else if (metric) summary.push([number(stats.known), "Values reported"], [number(stats.missing), "Values unknown"],
    [number(stats.mean), "Mean", fieldLabel(metric)], [number(stats.median), "Median", fieldLabel(metric)],
    [`${number(stats.min)} – ${number(stats.max)}`, "Reported range"]);
  el("stats").replaceChildren(...summary.map(([value, label, detail, style]) => {
    const card = make("div", undefined, `db-stat ${style || ""}`);
    card.append(make("span", label, "db-stat-label"), make("strong", value));
    if (detail) card.append(make("small", detail)); return card;
  }));
  if (el("metric-summary")) el("metric-summary").textContent = metric ?
    `${fieldLabel(metric)} · Mean ${number(stats.mean)} · Median ${number(stats.median)} · Range ${number(stats.min)}–${number(stats.max)} · ${number(stats.known)} reported / ${number(stats.missing)} unknown` : "Select a numeric field to inspect its statistics.";
  if (isDataCenter && tableName === "projects" && el("metric-summary")) el("metric-summary").textContent = `${fieldLabel(metric)}: ${stats.known} reported, ${stats.missing} unknown. Capacity totals above keep scope, lifecycle and rating categories separate. Group charts show record counts.`;
  for (const key of ["min", "max", "missing"]) el(key).disabled = !metric;
  el("aggregation").querySelectorAll("option").forEach((option) => { option.disabled = option.value !== "count" && (!metric || ((isDataCenter || isWind) && tableName === "projects")); });
  if (!metric || ((isDataCenter || isWind) && tableName === "projects")) el("aggregation").value = "count";
  renderChart(); renderTable(); renderMap();
}
async function renderMap() {
  if (!el("map-panel")) return;
  const request = ++mapRequest, enabled = tableName === "projects" || (isWind && tableName === "turbines");
  el("map-panel").hidden = !enabled;
  el("visuals").classList.toggle("db-with-map", enabled);
  if (!enabled) return;
  const noun = tableName === "turbines" ? "turbine records" : "projects";
  el("map-title").textContent = tableName === "turbines" ? "Registry turbine locations" : "Project locations";
  const count = filtered.filter(hasLocation).length;
  el("map-caption").textContent = count ? `${number(count)} mapped · ${number(filtered.length - count)} without valid coordinates. All matching ${noun} contribute; zoom or open a group to explore.` :
    filtered.length ? `No matching ${noun} have valid coordinates. They remain available in the table.` : `No ${noun} match these filters.`;
  el("map-fit").disabled = !count;
  try {
    mapModule ||= import("./database-map.mjs");
    const {createProjectMap} = await mapModule;
    if (request !== mapRequest || !(tableName === "projects" || (isWind && tableName === "turbines"))) return;
    projectMap ||= createProjectMap(el("map"), showRecord, root.dataset.database || "pv");
    projectMap.update(filtered, {worldView: isBess && filtered.length === rows.length});
  } catch {
    mapModule = null;
    el("map-caption").textContent = "Map could not load. Project KPIs and the results table remain available. Reload the page to retry.";
  }
}
function renderChart() {
  const field = el("group").value, metric = el("metric").value, aggregation = el("aggregation").value;
  const groups = field ? groupRows(filtered, field, metric, aggregation) : [];
  const shown = groups.slice(0, 15), max = Math.max(1, ...shown.map((g) => Math.abs(g.value ?? 0)));
  el("chart-caption").textContent = `${Math.min(groups.length, 15)} of ${groups.length} groups · ${aggregation === "count" ? "record counts" : `${aggregation === "sum" ? "sum of reported values" : "mean of reported values"} · ${fieldLabel(metric)}`} · All matching records contribute. Bar lengths show magnitude; labels retain sign. Unknown groups are included.`;
  el("chart").replaceChildren(...shown.map((group) => {
    const row = make("div", undefined, "db-bar-row"), track = make("div", undefined, "db-bar-track"), bar = make("div", undefined, "db-bar");
    bar.style.width = `${100 * Math.abs(group.value ?? 0) / max}%`; track.append(bar);
    row.title = `${group.records} records; numeric values: ${group.known} reported, ${group.missing} unknown`;
    row.append(make("span", group.label, "db-bar-label"), track, make("span", number(group.value))); return row;
  }));
  if (!shown.length) el("chart").append(make("p", "No matching records or no grouping field available."));
}
function renderTable() {
  const ordered = sortRows(filtered, sortKey, descending), size = Number(el("page-size").value);
  const pages = Math.max(1, Math.ceil(ordered.length / size)); page = Math.max(0, Math.min(page, pages - 1));
  el("page").textContent = `${number(ordered.length)} matches · Page ${page + 1} of ${pages}`;
  el("prev").disabled = page === 0; el("next").disabled = page === pages - 1;
  const header = make("tr"); header.append(make("th", "Record"));
  for (const key of visible) {
    const th = make("th"), button = make("button", fieldLabel(key) + (sortKey === key ? descending ? " ↓" : " ↑" : ""));
    button.type = "button"; th.scope = "col"; th.title = index.fields[key].description;
    if (sortKey === key) th.setAttribute("aria-sort", descending ? "descending" : "ascending");
    button.addEventListener("click", () => { descending = sortKey === key ? !descending : false; sortKey = key; page = 0; renderTable(); });
    th.append(button); header.append(th);
  }
  el("results").tHead.replaceChildren(header);
  el("results").tBodies[0].replaceChildren(...ordered.slice(page * size, (page + 1) * size).map((row) => {
    const tr = make("tr"), action = make("td"), button = make("button", "Details"); button.type = "button";
    button.addEventListener("click", () => showRecord(row)); action.append(button); tr.append(action);
    for (const key of visible) {
      const value = key === "source_urls" && Array.isArray(row[key])
        ? `${row[key].length} source(s) · open Details` : display(row[key]);
      const td = make("td", value.length > 180 ? value.slice(0, 177) + "…" : value); td.title = value; tr.append(td);
    }
    return tr;
  }));
  if (!ordered.length) { const tr = make("tr"), td = make("td", "No records match these filters."); td.colSpan = visible.length + 1; tr.append(td); el("results").tBodies[0].append(tr); }
  el("export").disabled = !visible.length || !filtered.length;
}
function showRecord(row) {
  currentRecord = Object.fromEntries(Object.keys(index.fields).map((key) => [key, row[key] ?? null]));
  el("detail-title").textContent = row.name || row.record_id;
  const table = make("table"), tbody = make("tbody"); table.append(tbody);
  for (const [key, meta] of Object.entries(index.fields)) {
    const tr = make("tr"), th = make("th", fieldLabel(key)), td = make("td"); th.scope = "row"; th.title = meta.description;
    const value = row[key];
    if (key === "source_urls" && Array.isArray(value)) {
      for (const url of value) {
        const p = make("p");
        try { const parsed = new URL(url); if (!["https:", "http:"].includes(parsed.protocol)) throw new Error("Unsafe URL");
          const a = make("a", url); a.href = parsed.href; a.target = "_blank"; a.rel = "noopener noreferrer"; p.append(a);
        } catch { p.textContent = display(url); } td.append(p);
      }
    } else if (meta.type === "json" && value != null) {
      let text = value; try { text = JSON.stringify(JSON.parse(value), null, 2); } catch { /* Preserve raw value. */ }
      td.append(make("pre", text));
    } else td.textContent = display(value);
    tr.append(th, td); tbody.append(tr);
  }
  el("detail-content").replaceChildren(table); el("detail").showModal();
}
function download(content, name, mime) {
  const url = URL.createObjectURL(new Blob([content], {type: mime})), anchor = make("a");
  anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
el("table").addEventListener("change", loadTable);
el("retry").addEventListener("click", initialize);
el("filter-field").addEventListener("change", () => { categoryOptions(); page = 0; render(); });
for (const key of ["filter-value", "metric", "missing"]) el(key).addEventListener("change", () => {
  if (key === "metric") { el("min").value = ""; el("max").value = ""; }
  page = 0; render();
});
let timer;
for (const key of ["search", "min", "max"]) el(key).addEventListener("input", () => {
  clearTimeout(timer); timer = setTimeout(() => { page = 0; render(); }, 180);
});
for (const key of ["group", "aggregation"]) el(key).addEventListener("change", renderChart);
el("reset").addEventListener("click", () => { resetFilters(); render(); });
el("default-columns").addEventListener("click", () => { defaultColumns(); renderColumns(); renderTable(); });
el("all-columns").addEventListener("click", () => { visible = Object.keys(index.fields); renderColumns(); renderTable(); });
el("page-size").addEventListener("change", () => { page = 0; renderTable(); });
el("prev").addEventListener("click", () => { page--; renderTable(); });
el("next").addEventListener("click", () => { page++; renderTable(); });
el("export").addEventListener("click", () => download(toCsv(sortRows(filtered, sortKey, descending), visible), `${tableName}-filtered.csv`, "text/csv;charset=utf-8"));
el("export-record").addEventListener("click", () => download(JSON.stringify(currentRecord, null, 2), `${tableName}-${currentRecord.record_id}.json`, "application/json"));
el("close").addEventListener("click", () => el("detail").close());
el("map-fit")?.addEventListener("click", () => projectMap?.fit());
el("map-world")?.addEventListener("click", () => projectMap?.world());
initialize();
