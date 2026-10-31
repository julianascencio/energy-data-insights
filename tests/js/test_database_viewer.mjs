import assert from "node:assert/strict";
import test from "node:test";
import {filterRows, sortRows, statistics, groupRows, toCsv} from "../../docs/_static/database-core.mjs";

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
