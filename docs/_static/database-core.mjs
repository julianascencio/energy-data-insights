// Pure helpers shared by the browser viewer and Node's built-in test runner.
export const display = (value) => value == null ? "Unknown" :
  typeof value === "object" ? JSON.stringify(value) : String(value);
export const numeric = (value) => typeof value === "number" && Number.isFinite(value);

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
