// Pure helpers shared by the browser viewer and Node's built-in test runner.
export const display = (value) => value == null ? "Unknown" :
  typeof value === "object" ? JSON.stringify(value) : String(value);
export const numeric = (value) => typeof value === "number" && Number.isFinite(value);

// Never coerce null/blank coordinates to zero or substitute country centroids.
export function hasLocation(row) {
  return numeric(row.latitude) && numeric(row.longitude) &&
    Math.abs(row.latitude) <= 90 && Math.abs(row.longitude) <= 180;
}

export function projectSummary(rows) {
  const ac = statistics(rows, "capacity_ac_mw"), dc = statistics(rows, "capacity_dc_mw");
  return {ac, dc, ...projectGeography(rows)};
}

export function bessProjectSummary(rows) {
  return {power: statistics(rows, "power_capacity_mw"),
    energy: statistics(rows, "energy_capacity_mwh"), ...projectGeography(rows)};
}

function projectGeography(rows) {
  return {located: rows.filter(hasLocation).length,
    countries: new Set(rows.map((row) => row.country_code).filter((code) =>
      typeof code === "string" && code.trim())).size};
}

// Group projected screen points, so every located project contributes without
// creating tens of thousands of DOM markers. Recomputed at each zoom level.
export function clusterLocations(points, cellSize = 40) {
  const cells = new Map();
  for (const {x, y, row} of points) {
    const key = `${Math.floor(x / cellSize)},${Math.floor(y / cellSize)}`;
    if (!cells.has(key)) cells.set(key, {x: 0, y: 0, rows: []});
    const cell = cells.get(key); cell.x += x; cell.y += y; cell.rows.push(row);
  }
  return [...cells.values()].map((cell) => ({...cell,
    x: cell.x / cell.rows.length, y: cell.y / cell.rows.length}));
}

export function filterRows(rows, {search = "", field = "", equals = "", metric = "", min = "", max = "", missing = "all"} = {}) {
  const query = search.trim().toLocaleLowerCase();
  return rows.filter((row) => {
    if (query && !Object.values(row).some((v) => v != null && display(v).toLocaleLowerCase().includes(query))) return false;
    if (field && equals !== "" && JSON.stringify(row[field] ?? null) !== equals) return false;
    const value = row[metric];
    if (metric && missing === "known" && value == null) return false;
    if (metric && missing === "missing" && value != null) return false;
    if (metric && (min !== "" || max !== "")) {
      if (!numeric(value)) return false;
      if (min !== "" && value < Number(min)) return false;
      if (max !== "" && value > Number(max)) return false;
    }
    return true;
  });
}

export function sortRows(rows, key, descending = false) {
  return [...rows].sort((a, b) => {
    const left = a[key], right = b[key];
    // Unknown values stay last in both directions.
    if (left == null) return right == null ? 0 : 1;
    if (right == null) return -1;
    const order = numeric(left) && numeric(right) ? left - right :
      display(left).localeCompare(display(right), undefined, {numeric: true});
    return descending ? -order : order;
  });
}

export function statistics(rows, field) {
  const values = rows.map((row) => row[field]).filter(numeric).sort((a, b) => a - b);
  const n = values.length, sum = values.reduce((total, value) => total + value, 0);
  return {known: n, missing: rows.length - n, mean: n ? sum / n : null,
    median: n ? (values[Math.floor((n - 1) / 2)] + values[Math.floor(n / 2)]) / 2 : null,
    min: n ? values[0] : null, max: n ? values[n - 1] : null,
    reportedSum: n ? sum : null};
}

export function groupRows(rows, field, metric, aggregation = "count") {
  const groups = new Map();
  for (const row of rows) {
    const key = JSON.stringify(row[field] ?? null);
    if (!groups.has(key)) groups.set(key, {label: display(row[field]), rows: []});
    groups.get(key).rows.push(row);
  }
  return [...groups.values()].map(({label, rows: group}) => {
    const stats = statistics(group, metric);
    return {label, records: group.length, known: stats.known, missing: stats.missing,
      value: aggregation === "count" ? group.length : aggregation === "mean" ? stats.mean : stats.reportedSum};
  }).sort((a, b) => (b.value ?? -Infinity) - (a.value ?? -Infinity) || a.label.localeCompare(b.label));
}

export function toCsv(rows, columns) {
  const cell = (value) => {
    let text = value == null ? "" : display(value);
    // Neutralize spreadsheet formula injection; retain actual negative numbers.
    if (typeof value !== "number" && /^[\s]*[=+\-@\t\r\n]/.test(text)) text = "'" + text;
    return '"' + text.replaceAll('"', '""') + '"';
  };
  return [columns.map(cell).join(","), ...rows.map((row) => columns.map((c) => cell(row[c])).join(","))].join("\r\n");
}


/** Count physical facility records separately from documented phase and campus scopes. */
export function dataCenterScopes(rows) {
  return {
    facilities: new Set(rows.filter(r => r.record_scope === "facility" && r.facility_id).map(r => r.facility_id)).size,
    phases: rows.filter(r => r.record_scope === "phase").length,
    campuses: rows.filter(r => r.record_scope === "campus").length,
  };
}

/** Data-center capacity: exclude campus/unresolved overlap rows persistently.
 * Return separate rating bases, preserving zero and missingness. No conversion.
 */
export function dataCenterCapacity(rows, field) {
  if (!["it_capacity_mw", "grid_capacity_mw", "facility_capacity_mw"].includes(field)) throw new Error("Choose an explicit capacity boundary");
  const eligible = rows.filter(r => ["independent", "child"].includes(r.aggregation_role) && !r.overlap_group);
  const basisField = field.replace(/_mw$/, "_basis"), byBasis = {};
  for (const row of eligible) {
    if (typeof row[field] !== "number" || !Number.isFinite(row[field])) continue;
    const basis = row[basisField] || "unspecified";
    byBasis[basis] ||= {reported_mw: 0, records: 0};
    byBasis[basis].reported_mw += row[field]; byBasis[basis].records += 1;
  }
  return {excluded: rows.length - eligible.length, unknown: eligible.filter(r => r[field] == null).length, byBasis};
}

/** Wind capacities never combine lifecycle states, parent totals or unresolved scopes. */
export function windEvidence(rows) {
  const projects = rows.filter(r => r.entity_type === "projects");
  return {
    lifecycleKnown: projects.filter(r => r.status && r.status !== "unknown").length,
    lifecycleUnknown: projects.filter(r => !r.status || r.status === "unknown").length,
    scopeExcluded: projects.filter(r => !["independent", "child"].includes(r.aggregation_role) || r.overlap_group).length,
  };
}

export function windCapacity(rows, field) {
  if (!["installed_capacity_mw", "commissioned_capacity_mw", "planned_capacity_mw", "awarded_capacity_mw", "export_capacity_mw", "historical_capacity_mw"].includes(field)) throw new Error("Choose an explicit wind capacity");
  const selected = rows.filter(r => ["independent", "child"].includes(r.aggregation_role) && !r.overlap_group);
  const byStatus = {};
  for (const row of selected) {
    if (!numeric(row[field])) continue;
    const key = row.status + (field === "historical_capacity_mw" ? `@${row.capacity_reference_year}` : "");
    byStatus[key] ||= {reported_mw: 0, records: 0};
    byStatus[key].reported_mw += row[field]; byStatus[key].records++;
  }
  return {excluded: rows.length - selected.length, unknown: selected.filter(r => r[field] == null).length, byStatus};
}
