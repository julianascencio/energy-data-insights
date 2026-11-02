import assert from "node:assert/strict";
import test from "node:test";
import {filterRows, sortRows, statistics, groupRows, toCsv, hasLocation, projectSummary, clusterLocations} from "../../docs/_static/database-core.mjs";

const rows = [
  {name: "A", country: "CHL", power: 0, bifacial: false, sources: ["OEM"]},
  {name: "B", country: "CHL", power: 20, bifacial: true},
  {name: "C", country: "ESP", power: null},
  {name: "D", country: null, power: 10},
];
test("filters combine search, exact values, ranges and explicit missingness", () => {
  assert.deepEqual(filterRows(rows, {search: "oem", metric: "power", min: "0", max: "0"}), [rows[0]]);
  assert.deepEqual(filterRows(rows, {field: "bifacial", equals: "false"}), [rows[0]]);
  assert.deepEqual(filterRows(rows, {field: "country", equals: "null"}), [rows[3]]);
  assert.deepEqual(filterRows(rows, {metric: "power", missing: "missing"}), [rows[2]]);
  assert.equal(filterRows(rows, {metric: "power", missing: "missing", min: "0"}).length, 0);
  assert.equal(filterRows(rows, {metric: "power", min: "20", max: "10"}).length, 0);
});
test("numeric sorting keeps unknown values last in either direction", () => {
  assert.deepEqual(sortRows(rows, "power").map((r) => r.name), ["A", "D", "B", "C"]);
  assert.deepEqual(sortRows(rows, "power", true).map((r) => r.name), ["B", "D", "A", "C"]);
  assert.deepEqual(rows.map((r) => r.name), ["A", "B", "C", "D"]);
});
test("statistics and groups exclude nulls without dropping reported zero", () => {
  assert.deepEqual(statistics(rows, "power"), {known: 3, missing: 1, mean: 10, median: 10, min: 0, max: 20, reportedSum: 30});
  assert.equal(statistics([], "power").reportedSum, null);
  assert.equal(statistics(rows.slice(0, 2), "power").median, 10);
  const groups = groupRows(rows, "country", "power", "sum");
  assert.equal(groups.find((g) => g.label === "ESP").value, null);
  assert.equal(groups.find((g) => g.label === "Unknown").value, 10);
  assert.equal(groups.find((g) => g.label === "CHL").value, 20);
});
test("CSV preserves quoted multiline/list data and neutralizes formulas", () => {
  const csv = toCsv([{a: '=HYPERLINK("evil")', b: -2, c: 'a,"b"\n', d: ["URL"], e: null}], ["a", "b", "c", "d", "e"]);
  assert.ok(csv.includes('"\'=HYPERLINK(""evil"")"'));
  assert.ok(csv.includes('"-2"'));
  assert.ok(csv.includes('"a,""b""\n"'));
  assert.ok(csv.includes('"[""URL""]"'));
  assert.ok(csv.endsWith(',""'));
});

// Synthetic catalogue: independent AC/DC values, unknown AC and reported zero.
const projects = [
  {name: "A", country_code: "CHL", capacity_ac_mw: 100, capacity_dc_mw: 130, latitude: -34.4, longitude: -70.9},
  {name: "B", country_code: "CHL", capacity_ac_mw: 0, capacity_dc_mw: 8, latitude: 0, longitude: 0},
  {name: "C", country_code: "ESP", capacity_ac_mw: null, capacity_dc_mw: 300, capacity_mw: 999, latitude: null, longitude: null},
  {name: "D", country_code: null, capacity_ac_mw: 25, capacity_dc_mw: null, latitude: 91, longitude: 20},
];
test("project totals sum only reported AC, preserve zero and include unmapped records", () => {
  const summary = projectSummary(projects);
  assert.equal(summary.ac.reportedSum, 125);
  assert.equal(summary.ac.known, 3);
  assert.equal(summary.ac.missing, 1);
  assert.equal(summary.dc.reportedSum, 438);
  assert.equal(summary.located, 2);
  assert.equal(summary.countries, 2);
  assert.equal(projectSummary([projects[1]]).ac.reportedSum, 0);
  assert.equal(projectSummary([projects[2]]).ac.reportedSum, null);
  assert.equal(projectSummary([]).ac.reportedSum, null);
  assert.equal(projectSummary([]).countries, 0);
});
test("dashboard totals follow combined filters, including filters on a different metric", () => {
  const filtered = filterRows(projects, {field: "country_code", equals: '"CHL"', metric: "capacity_dc_mw", min: "100"});
  assert.equal(projectSummary(filtered).ac.reportedSum, 100);
  assert.equal(projectSummary(filterRows(projects, {search: "ESP"})).ac.reportedSum, null);
  const many = Array.from({length: 101}, () => projects[0]);
  assert.equal(projectSummary(many).ac.reportedSum, 10100); // Not the 25-row page.
});
test("map rejects invalid/incomplete coordinates without rejecting valid zeros or boundaries", () => {
  for (const [latitude, longitude] of [[null, null], ["", ""], ["1", 2], [false, 0], [undefined, 1], [NaN, 1], [1, Infinity], [91, 2], [1, -181]]) {
    assert.equal(hasLocation({latitude, longitude}), false);
  }
  for (const [latitude, longitude] of [[0, 0], [-90, -180], [90, 180], [-34, -70]]) {
    assert.equal(hasLocation({latitude, longitude}), true);
  }
});
test("map clusters preserve all 60000 project references, including identical locations", () => {
  const points = Array.from({length: 60000}, (_, i) => ({x: i % 600, y: i % 300, row: {record_id: i}}));
  const clusters = clusterLocations(points);
  assert.ok(clusters.length < 200);
  assert.equal(clusters.reduce((count, group) => count + group.rows.length, 0), 60000);
  assert.equal(new Set(clusters.flatMap((group) => group.rows.map((row) => row.record_id))).size, 60000);
  assert.deepEqual(clusterLocations([{x: 1, y: 2, row: projects[0]}, {x: 3, y: 4, row: projects[1]}]),
    [{x: 2, y: 3, rows: [projects[0], projects[1]]}]);
  assert.deepEqual(clusterLocations([]), []);
});
