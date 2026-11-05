import assert from "node:assert/strict";
import test from "node:test";
import {hydroCapacity} from "../../docs/_static/database-core.mjs";
test("hydro scopes, technology, pumping, null and zero remain separate", () => {
  const base = {status: "operational", technology: "pumped_storage", aggregation_role: "independent"};
  const rows = [{...base, installed_capacity_mw: 100, pumping_capacity_mw: 120}, {...base, aggregation_role: "aggregate", installed_capacity_mw: 100}, {...base, aggregation_role: "unresolved", installed_capacity_mw: 999}, {...base, technology: "run_of_river", installed_capacity_mw: 0}, {...base}];
  const summary = hydroCapacity(rows, "installed_capacity_mw");
  assert.equal(summary.excluded, 2); assert.equal(summary.unknown, 1);
  assert.equal(summary.byStatus["operational/pumped_storage"].reported_mw, 100);
  assert.equal(summary.byStatus["operational/run_of_river"].reported_mw, 0);
  assert.equal(hydroCapacity(rows, "pumping_capacity_mw").byStatus["operational/pumped_storage"].reported_mw, 120);
  assert.deepEqual(hydroCapacity(rows.filter(r => r.aggregation_role === "aggregate"), "installed_capacity_mw").byStatus, {});
  assert.throws(() => hydroCapacity(rows, "storage_capacity_mwh"));
});
