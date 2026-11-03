import assert from "node:assert/strict";
import test from "node:test";
import {filterRows, sortRows, statistics, groupRows, toCsv, hasLocation, projectSummary, bessProjectSummary, clusterLocations, dataCenterScopes} from "../../docs/_static/database-core.mjs";

const rows = [
  {name: "A", country: "CHL", power: 0, bifacial: false, sources: ["OEM"]},
  {name: "B", country: "CHL", power: 20, bifacial: true},
  {name: "C", country: "ESP", power: null},
  {name: "D", country: null, power: 10},
];

test("data center phases never inflate facility counts, including filtered phases", () => {
  const scopes = [
    {record_scope: "campus", facility_id: "campus"},
    {record_scope: "facility", facility_id: "building"},
    {record_scope: "phase", facility_id: "building", phase_id: "one"},
    {record_scope: "phase", facility_id: "unresolved-building", phase_id: "two"},
  ];
  assert.deepEqual(dataCenterScopes(scopes), {facilities: 1, phases: 2, campuses: 1});
  assert.deepEqual(dataCenterScopes(scopes.filter(r => r.record_scope === "phase")), {facilities: 0, phases: 2, campuses: 0});
});
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

// Synthetic BESS records: power and energy are independent source ratings.
const batteries = [
  {name: "A", country_code: "CHL", status: "operational", power_capacity_mw: 100, energy_capacity_mwh: 400, latitude: -34, longitude: -71},
  {name: "B", country_code: "CHL", status: "planned", power_capacity_mw: 0, energy_capacity_mwh: null, latitude: 0, longitude: 0},
  {name: "C", country_code: "ESP", status: "operational", power_capacity_mw: null, energy_capacity_mwh: 300, duration_hours: 3, latitude: null, longitude: null},
  {name: "D", country_code: null, status: "planned", power_capacity_mw: 25, energy_capacity_mwh: 0, latitude: 91, longitude: 20},
];
test("BESS totals keep MW and MWh independent, including unmapped records and reported zeros", () => {
  const summary = bessProjectSummary(batteries);
  assert.equal(summary.power.reportedSum, 125);
  assert.equal(summary.energy.reportedSum, 700);
  assert.equal(summary.power.known, 3);
  assert.equal(summary.energy.missing, 1);
  assert.equal(summary.located, 2);
  assert.equal(summary.countries, 2);
  assert.equal(bessProjectSummary([batteries[1]]).power.reportedSum, 0);
  assert.equal(bessProjectSummary([batteries[1]]).energy.reportedSum, null);
  assert.equal(bessProjectSummary([batteries[2]]).power.reportedSum, null); // No MWh/duration inference.
  assert.equal(bessProjectSummary([batteries[3]]).energy.reportedSum, 0);
  assert.equal(bessProjectSummary([]).power.reportedSum, null);
  assert.equal(bessProjectSummary([]).energy.reportedSum, null);
});
test("BESS KPIs follow combined filters across all rows, independent of page size and selected metric", () => {
  const filtered = filterRows(batteries, {field: "status", equals: '"operational"', metric: "energy_capacity_mwh", min: "300"});
  assert.equal(bessProjectSummary(filtered).power.reportedSum, 100);
  assert.equal(bessProjectSummary(filtered).energy.reportedSum, 700);
  assert.equal(bessProjectSummary(filtered).located, 1);
  assert.equal(bessProjectSummary(filterRows(batteries, {search: "ESP"})).power.reportedSum, null);
  const many = Array.from({length: 101}, () => batteries[0]);
  assert.equal(bessProjectSummary(many).power.reportedSum, 10100);
  assert.equal(bessProjectSummary(many).energy.reportedSum, 40400);
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

test("data center capacity keeps scopes and bases separate, even after filtering", async () => {
  const {dataCenterCapacity} = await import("../../docs/_static/database-core.mjs");
  const rows = [
    {aggregation_role:"independent", it_capacity_mw:0, it_capacity_basis:"operational"},
    {aggregation_role:"child", it_capacity_mw:10, it_capacity_basis:"ultimate_planned"},
    {aggregation_role:"aggregate", it_capacity_mw:100},
    {aggregation_role:"independent", grid_capacity_mw:999},
    {aggregation_role:"child", overlap_group:"uncertain", it_capacity_mw:50},
  ];
  assert.deepEqual(dataCenterCapacity(rows,"it_capacity_mw"), {excluded:2,unknown:1,byBasis:{operational:{reported_mw:0,records:1},ultimate_planned:{reported_mw:10,records:1}}});
  assert.equal(dataCenterCapacity(rows.slice(-1),"it_capacity_mw").excluded,1);
  assert.deepEqual(dataCenterCapacity(rows.slice(3,4),"it_capacity_mw").byBasis,{});
  assert.throws(() => dataCenterCapacity(rows,"backup_generation_mw"));
});


test("wind excludes unresolved scopes and keeps capacity lifecycle categories separate", async () => {
  const {windCapacity} = await import("../../docs/_static/database-core.mjs");
  const rows = [
    {aggregation_role:"child", status:"operational", installed_capacity_mw:0},
    {aggregation_role:"child", status:"operational", installed_capacity_mw:20},
    {aggregation_role:"aggregate", status:"operational", installed_capacity_mw:20},
    {aggregation_role:"unresolved", status:"unknown", installed_capacity_mw:999},
    {aggregation_role:"independent", status:"announced", planned_capacity_mw:100},
    {aggregation_role:"child", status:"decommissioned", installed_capacity_mw:5},
    {aggregation_role:"child", status:"operational", installed_capacity_mw:20, overlap_group:"repower"},
  ];
  assert.deepEqual(windCapacity(rows,"installed_capacity_mw"), {excluded:3,unknown:1,byStatus:{operational:{reported_mw:20,records:2},decommissioned:{reported_mw:5,records:1}}});
  assert.equal(windCapacity(rows.slice(-1),"installed_capacity_mw").excluded,1);
  assert.deepEqual(windCapacity(rows.slice(4,5),"installed_capacity_mw").byStatus,{});
  assert.equal(windCapacity(rows,"planned_capacity_mw").byStatus.announced.reported_mw,100);
  assert.throws(() => windCapacity(rows,"capacity_mw"));
});

test("wind lifecycle evidence does not imply eligible capacity scope", async () => {
  const {windEvidence} = await import("../../docs/_static/database-core.mjs");
  const rows = [
    {entity_type:"projects",status:"operational",aggregation_role:"unresolved"},
    {entity_type:"projects",status:"decommissioned",aggregation_role:"independent"},
    {entity_type:"projects",status:"unknown",aggregation_role:"unresolved"},
    {entity_type:"projects",status:"operational",aggregation_role:"child",overlap_group:"phase-pending"},
    {entity_type:"equipment",status:"unknown"},
  ];
  assert.deepEqual(windEvidence(rows), {lifecycleKnown:3,lifecycleUnknown:1,scopeExcluded:3});
  assert.deepEqual(windEvidence([]), {lifecycleKnown:0,lifecycleUnknown:0,scopeExcluded:0});
});
