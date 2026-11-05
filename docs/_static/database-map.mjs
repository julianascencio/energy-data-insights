import * as L from "./vendor/leaflet/leaflet.mjs";
import {hasLocation, clusterLocations, statistics} from "./database-core.mjs";

const number = (value) => value == null ? "Unknown" : value.toLocaleString(undefined, {maximumFractionDigits: 3});
const make = (tag, text, className) => {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
};

export function createProjectMap(container, onRecord, database = "pv") {
  const capacities = database === "bess" ?
    [["power_capacity_mw", "MW power"], ["energy_capacity_mwh", "MWh energy"]] :
    [["capacity_ac_mw", "MW AC"], ["capacity_dc_mw", "MW DC"]];
  const map = L.map(container, {preferCanvas: true, scrollWheelZoom: false,
    minZoom: 0, maxZoom: 16, zoomSnap: 0.5, maxBounds: [[-90, -220], [90, 220]]});
  const markers = L.layerGroup().addTo(map);
  let locations = [];
  map.attributionControl.setPrefix('<a href="https://leafletjs.com">Leaflet</a>');
  map.attributionControl.addAttribution('<a href="https://www.naturalearthdata.com">Natural Earth</a> · 1:110m overview');

  // A basemap failure must not prevent project markers, KPIs or table access.
  fetch(new URL("database-world.geojson", import.meta.url)).then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }).then((data) => L.geoJSON(data, {interactive: false,
    style: {color: "#9aafb2", weight: 0.65, fillColor: "#dce7e6", fillOpacity: 0.85},
  }).addTo(map).bringToBack()).catch(() => {
    const note = make("p", "Background map unavailable. Project locations are still shown.", "db-map-warning");
    container.after(note);
  });

  function popup(group) {
    const content = make("div", undefined, "db-map-popup");
    if (group.rows.length === 1) {
      const row = group.rows[0];
      content.append(make("strong", row.name || row.record_id),
        make("p", `${row.country_code || "Unknown country"} · ${row.status || "Unknown status"}`),
        make("p", database === "hydro" ? `${row.technology} · Historical ${number(row.historical_capacity_mw)} MW · ${row.aggregation_role}; current capacity unverified` : database === "wind" && row.entity_type === "turbines" ? `Registry inventory · ${row.manufacturer || "Unknown manufacturer"} · ${row.turbine_model || "Unknown model"} · Parent ${row.project_record_id}` : database === "wind" ? `${row.technology} · Installed ${number(row.installed_capacity_mw)} MW · Planned ${number(row.planned_capacity_mw)} MW · ${row.aggregation_role}` : row.facility_id ? `${row.record_scope} · IT ${number(row.it_capacity_mw)} MW (${row.it_capacity_basis || "unknown basis"}) · Grid ${number(row.grid_capacity_mw)} MW · Facility ${number(row.facility_capacity_mw)} MW` : capacities.map(([field, unit]) => `${number(row[field])} ${unit}`).join(" · ")),
        make("p", `Location accuracy: ${row.location_accuracy || "Unknown"}`));
      if (database === "bess") content.append(
        make("p", `Power basis: ${row.power_basis || "Unknown"} · Energy basis: ${row.energy_basis || "Unknown"}`),
        make("p", `Capacity scope: ${row.capacity_scope || "Unknown"} · Status as of: ${row.status_as_of || "Unknown"}`));
      const button = make("button", row.entity_type === "turbines" ? "View turbine evidence" : "View project details"); button.type = "button";
      button.addEventListener("click", () => onRecord(row)); content.append(button);
      return content;
    }
    content.append(make("strong", `${number(group.rows.length)} ${group.rows[0].entity_type === "turbines" ? "turbine records" : "projects"} in this group`),
      make("p", (database === "wind" || database === "hydro") ? "Capacity categories and reviewed scopes are shown in the dashboard." : group.rows.some(row => row.facility_id) ? "Facility/campus records. Scope-aware capacities are shown in the dashboard." : capacities.map(([field, unit]) => `${number(statistics(group.rows, field).reportedSum)} ${unit} reported`).join(" · ")));
    if (database === "bess") content.append(make("p", "Reported sums; project phases, statuses and rating bases may differ."));
    const zoom = make("button", "Zoom to group"); zoom.type = "button";
    zoom.disabled = map.getZoom() === map.getMaxZoom();
    zoom.addEventListener("click", () => {
      map.closePopup();
      map.setView(L.latLng(group.rows[0].latitude, group.rows[0].longitude), Math.min(16, map.getZoom() + 2));
    });
    const list = make("ul"), navigation = make("div", undefined, "db-map-pages");
    const previous = make("button", "Previous"), next = make("button", "Next"), caption = make("span");
    previous.type = next.type = "button";
    let offset = 0;
    function showPage() {
      list.replaceChildren(...group.rows.slice(offset, offset + 8).map((row) => {
        const item = make("li"), button = make("button", row.name || row.record_id);
        button.type = "button"; button.addEventListener("click", () => onRecord(row));
        item.append(button); return item;
      }));
      previous.disabled = offset === 0; next.disabled = offset + 8 >= group.rows.length;
      caption.textContent = `${offset + 1}–${Math.min(offset + 8, group.rows.length)} of ${number(group.rows.length)}`;
    }
    previous.addEventListener("click", () => { offset -= 8; showPage(); });
    next.addEventListener("click", () => { offset += 8; showPage(); });
    navigation.append(previous, caption, next); content.append(zoom, list, navigation); showPage();
    return content;
  }

  function draw() {
    markers.clearLayers();
    const bounds = map.getPixelBounds(), zoom = map.getZoom();
    const points = [];
    for (const row of locations) {
      const point = map.project([row.latitude, row.longitude], zoom);
      if (point.x < bounds.min.x - 40 || point.x > bounds.max.x + 40 ||
          point.y < bounds.min.y - 40 || point.y > bounds.max.y + 40) continue;
      points.push({x: point.x, y: point.y, row});
    }
    for (const group of clusterLocations(points)) {
      const count = group.rows.length, cluster = count > 1;
      const dot = make("span", cluster ? number(count) : "", cluster ? "db-map-cluster" : "db-map-point");
      const size = cluster ? 38 : 14;
      const icon = L.divIcon({html: dot, className: "db-map-marker", iconSize: [size, size], iconAnchor: [size / 2, size / 2]});
      const title = cluster ? `${number(count)} projects — open group` : group.rows[0].name || "Project details";
      const location = map.unproject([group.x, group.y], zoom);
      const open = () => {
        // Keep the popup independent of markers: automatic popup panning
        // redraws visible clusters and must not remove the open record list.
        L.popup({maxWidth: 320, minWidth: 230, maxHeight: 240}).setLatLng(location)
          .setContent(popup(group)).openOn(map);
      };
      L.marker(location, {icon, title, alt: title, keyboard: true, autoPanOnFocus: false})
        .on("click", open).on("keypress", (event) => {
          if (["Enter", " "].includes(event.originalEvent.key)) {
            L.DomEvent.preventDefault(event.originalEvent); open();
          }
        }).addTo(markers);
    }
  }
  map.on("moveend zoomend resize", draw);
  function fit() {
    map.closePopup();
    if (locations.length) map.fitBounds(L.latLngBounds(locations.map((row) => [row.latitude, row.longitude])), {padding: [30, 30], maxZoom: 6, animate: false});
    else map.setView([20, 0], 1, {animate: false});
  }
  function world() {
    map.closePopup();
    map.fitBounds([[-60, -180], [85, 180]], {padding: [12, 12], animate: false});
  }
  new ResizeObserver(() => map.invalidateSize({pan: false})).observe(container);
  return {
    update(rows, {worldView = false} = {}) {
      locations = rows.filter(hasLocation);
      map.invalidateSize({pan: false});
      if (worldView) world(); else fit();
      draw();
    },
    fit,
    world,
  };
}
