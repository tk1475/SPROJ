// ── Basemaps ──────────────────────────────────────────────────────────────────
const BASEMAPS = {
  osm: L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: "&copy; OpenStreetMap contributors",
  }),
  "carto-light": L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors &copy; CARTO" }
  ),
  "carto-dark": L.tileLayer(
    "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors &copy; CARTO" }
  ),
};

const map = L.map("map", { preferCanvas: true }).setView([31.5204, 74.3587], 11);
BASEMAPS.osm.addTo(map);

const boundaryLayerGroup = L.layerGroup().addTo(map);
const choroplethGroup    = L.layerGroup().addTo(map);
const rawLayerGroup      = L.layerGroup().addTo(map);
const indexLayerGroup    = L.layerGroup().addTo(map);

// ── DOM refs ──────────────────────────────────────────────────────────────────
const statusEl         = document.getElementById("status");
const layerControlsEl  = document.getElementById("layer-controls");
const heatControlsEl   = document.getElementById("heatmap-controls");
const metricControlsEl = document.getElementById("metric-controls");
const legendEl         = document.getElementById("legend");
const toggleIndexBtn   = document.getElementById("toggle-index");
const resetWeightsBtn  = document.getElementById("reset-weights");
const stylePanelEl     = document.getElementById("style-panel-section");
const styleLayerNameEl = document.getElementById("style-layer-name");

// style panel controls
const spOpacity       = document.getElementById("sp-opacity");
const spOpacityVal    = document.getElementById("sp-opacity-val");
const spScale         = document.getElementById("sp-scale");
const spScaleVal      = document.getElementById("sp-scale-val");
const spScheme        = document.getElementById("sp-scheme");
const spOutlineToggle = document.getElementById("sp-outline-toggle");
const spOutlineOpts   = document.getElementById("sp-outline-opts");
const spOutlineColor  = document.getElementById("sp-outline-color");
const spOutlineWidth  = document.getElementById("sp-outline-width");
const spOutlineWidthVal = document.getElementById("sp-outline-width-val");
const spApplyBtn      = document.getElementById("sp-apply");
const spResetBtn      = document.getElementById("sp-reset-style");

// ── Color schemes ─────────────────────────────────────────────────────────────
const COLOR_SCHEMES = {
  hudi:        [[11,79,108],[60,174,163],[246,213,92],[237,85,59],[125,21,56]],
  ndvi:        [[165,0,38],[215,48,39],[254,178,76],[255,255,191],[145,207,96],[26,152,80]],
  temperature: [[49,54,149],[116,173,209],[224,243,248],[254,224,144],[244,109,67],[165,0,38]],
  aqi:         [[26,152,80],[145,207,96],[254,224,139],[252,141,89],[215,48,39],[165,0,38]],
  nightlights: [[8,7,19],[72,12,101],[163,37,106],[239,106,81],[252,200,103],[252,252,163]],
  // Plasma-style colormap for methane — deep purple → magenta → orange → bright yellow
  methane:     [[13,8,135],[84,2,163],[139,10,165],[185,50,137],[219,92,104],[244,136,73],[254,188,43],[240,249,33]],
  seq_orange:  [[255,247,236],[254,232,200],[253,187,132],[252,141,89],[227,74,51],[179,0,0]],
  seq_blue:    [[239,243,255],[198,219,239],[158,202,225],[107,174,214],[49,130,189],[8,81,156]],
  seq_purple:  [[242,240,247],[218,218,235],[188,189,220],[158,154,200],[106,81,163],[63,0,125]],
};

// ── Metric definitions ─────────────────────────────────────────────────────────
// note: shown in metric layer card; res: shown as resolution badge
const HEATMAP_METRICS = [
  { key:"ndvi",              label:"NDVI",               col:"ndvi",              note:"Vegetation index",              res:"100 m → 250 m",  scheme:"ndvi"        },
  { key:"lst",               label:"Land Surface Temp",  col:"lst",               note:"°C · Landsat 8/9",              res:"100 m → 250 m",  scheme:"temperature" },
  { key:"aqi",               label:"Air Quality (AQI)",  col:"aqi",               note:"PM₂.₅ · OpenAQ / WAQI",         res:"64 pts → 250 m", scheme:"aqi"         },
  { key:"night_lights",      label:"Night Lights",       col:"night_lights",      note:"nW/cm²/sr · VIIRS/SNPP",        res:"500 m → 250 m",  scheme:"nightlights" },
  { key:"poi_density",       label:"POI Density",        col:"poi_density",       note:"POIs per ha · Overture/OSM",    res:"pts → 250 m",    scheme:"seq_blue"    },
  { key:"road_density",      label:"Road Density",       col:"road_density",      note:"Road length/ha · OSM",          res:"lines → 250 m",  scheme:"seq_orange"  },
  { key:"poi_access",        label:"POI Accessibility",  col:"poi_access",        note:"Walk time to nearest POI (min)",res:"250 m grid",     scheme:"aqi"         },
  { key:"building_presence", label:"Building Presence",  col:"building_presence", note:"Built-area share · Open Bldgs", res:"250 m grid",     scheme:"seq_orange"  },
  { key:"ch4",               label:"Methane (CH₄)",      col:"ch4",               note:"ppb bias-corrected · TROPOMI",  res:"5.5 km → 250 m", scheme:"methane"     },
];

// ── Value formatting ──────────────────────────────────────────────────────────
const UNITS    = { aqi:"AQI", lst:"°C", ndvi:"", night_lights:"nW/cm²/sr", poi_density:"POIs/ha",
                   road_density:"m/ha", building_presence:"", highrise_share:"",
                   poi_access:"min", n1_min:"min", n3_min:"min", snap_dist_m:"m", ch4:"ppb" };
const DECIMALS = { lst:1, ndvi:3, aqi:0, poi_access:1, ch4:1 };

function formatVal(key, val) {
  if (val == null) return "—";
  const n = Number(val);
  if (Number.isNaN(n)) return String(val);
  const d    = DECIMALS[key] ?? 2;
  const unit = UNITS[key] != null ? (UNITS[key] ? " " + UNITS[key] : "") : "";
  return n.toFixed(d) + unit;
}

// ── Layer style state (shared / editable via style panel) ─────────────────────
const DEFAULT_STYLE = { opacity:0.85, cellScale:1.01, numClasses:5,
                        colorScheme:"hudi", outlineEnabled:false,
                        outlineColor:"#ffffff", outlineWidth:0.3 };
const layerStyle = { ...DEFAULT_STYLE };

// ── App state ─────────────────────────────────────────────────────────────────
const state = {
  manifest:        null,
  indexGeoJson:    null,
  indexFeatures:   [],
  rawLayers:       new Map(),
  activeRawLayers: new Set(),
  activeHeatKey:   null,       // currently shown metric choropleth
  choroplethCache: new Map(),  // metricKey → {layer, breaks, classColors}
  indexVisible:    false,
  indexChoropleth: null,
  metricControls:  new Map(),
  currentBasemap:  "osm",
  styleTarget:     null,       // "heat" | "index" | null
};

// ── Utilities ─────────────────────────────────────────────────────────────────
async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`HTTP ${res.status} — ${path}`);
  return res.json();
}
function setStatus(msg) { statusEl.textContent = msg; }

// ── Colour interpolation ──────────────────────────────────────────────────────
function lerpColor(stops, t) {
  const scaled = Math.max(0, Math.min(1, t)) * (stops.length - 1);
  const i      = Math.floor(scaled);
  const frac   = scaled - i;
  const [r1,g1,b1] = stops[i];
  const [r2,g2,b2] = stops[Math.min(i+1, stops.length-1)];
  return `rgb(${Math.round(r1+(r2-r1)*frac)},${Math.round(g1+(g2-g1)*frac)},${Math.round(b1+(b2-b1)*frac)})`;
}

function schemeColor(classIdx, numClasses, schemeKey) {
  const stops = COLOR_SCHEMES[schemeKey] || COLOR_SCHEMES.hudi;
  const t     = numClasses <= 1 ? 0.5 : classIdx / (numClasses - 1);
  return lerpColor(stops, t);
}

// ── Class breaks (quantile) ───────────────────────────────────────────────────
function computeBreaks(values, nClasses) {
  const sorted = values.filter(v => v != null && !Number.isNaN(+v)).map(Number).sort((a,b)=>a-b);
  if (!sorted.length) return null;
  const breaks = [];
  for (let i = 0; i <= nClasses; i++) {
    breaks.push(sorted[Math.min(Math.round((i/nClasses)*(sorted.length-1)), sorted.length-1)]);
  }
  return breaks;
}

function classifyValue(v, breaks) {
  if (v == null || Number.isNaN(+v) || !breaks) return null;
  const n = +v;
  let cls = breaks.length - 2; // = numClasses - 1
  for (let i = 1; i < breaks.length; i++) {
    if (n <= breaks[i]) { cls = i - 1; break; }
  }
  return cls;
}

// ── Grid cell geometry ────────────────────────────────────────────────────────
const HALF_LAT_DEG = (250 / 2) / 111320; // at equator; corrected per feature lat

function cellBounds(latlng, scale) {
  const halfLat = HALF_LAT_DEG * scale;
  const halfLon = (250 / 2) / (111320 * Math.cos(latlng.lat * Math.PI / 180)) * scale;
  return [[latlng.lat - halfLat, latlng.lng - halfLon],
          [latlng.lat + halfLat, latlng.lng + halfLon]];
}

// ── Core choropleth builder ───────────────────────────────────────────────────
// features: GeoJSON feature array (Point geometry)
// col: property name (or null for pre-computed '_score')
// schemeKey: color scheme name
// label: used in popups
// Returns { layer, breaks, classColors }
function buildChoropleth(features, col, schemeKey, label) {
  const style       = layerStyle;
  const { numClasses, cellScale, opacity, outlineEnabled, outlineColor, outlineWidth } = style;

  const vals   = features.map(f => f.properties[col]).filter(v => v != null && !Number.isNaN(+v)).map(Number);
  if (!vals.length) return null;

  const breaks      = computeBreaks(vals, numClasses);
  const classColors = Array.from({ length: numClasses }, (_, i) => schemeColor(i, numClasses, schemeKey));

  const layer = L.geoJSON({ type:"FeatureCollection", features }, {
    pointToLayer(feature, latlng) {
      const v   = feature.properties[col];
      const cls = classifyValue(v, breaks);

      const fillColor   = cls != null ? classColors[cls] : "transparent";
      const fillOpacity = cls != null ? opacity : 0;

      return L.rectangle(cellBounds(latlng, cellScale), {
        fillColor,
        fillOpacity,
        color:   outlineEnabled ? outlineColor : "transparent",
        weight:  outlineEnabled ? outlineWidth : 0,
        interactive: cls != null,
      });
    },
    onEachFeature(feature, layer) {
      const v = feature.properties[col];
      if (v == null) return;
      const cls = classifyValue(v, breaks);
      const classLabel = cls != null && breaks
        ? `${formatVal(col, breaks[cls])} – ${formatVal(col, breaks[cls+1])}`
        : "—";
      layer.bindPopup(
        `<div class="popup-header">${label}</div>
         <table class="popup-table">
           <tr><th>Value</th><td>${formatVal(col, v)}</td></tr>
           <tr><th>Class</th><td>${classLabel}</td></tr>
         </table>`
      );
    },
  });

  return { layer, breaks, classColors };
}

// ── Boundary ──────────────────────────────────────────────────────────────────
async function loadBoundary(path) {
  try {
    const data = await fetchJson(path);
    L.geoJSON(data, { style:{ color:"#1a3a4a", weight:1.8, fillOpacity:0, dashArray:"4 2" } })
     .addTo(boundaryLayerGroup);
  } catch { /* non-critical */ }
}

// ── Metric choropleth toggle ──────────────────────────────────────────────────
function clearActiveChoropleth() {
  if (state.activeHeatKey) {
    const cached = state.choroplethCache.get(state.activeHeatKey);
    if (cached) choroplethGroup.removeLayer(cached.layer);
  }
}

function showMetricChoropleth(key) {
  const metricDef = HEATMAP_METRICS.find(m => m.key === key);
  if (!metricDef) return;

  // Toggle off
  if (state.activeHeatKey === key) {
    clearActiveChoropleth();
    state.activeHeatKey   = null;
    state.styleTarget     = null;
    stylePanelEl.style.display = "none";
    updateHeatmapButtons();
    renderLegend();
    return;
  }

  clearActiveChoropleth();

  // Reset scheme to metric default, then build
  layerStyle.colorScheme = metricDef.scheme;
  syncStylePanelToState(metricDef.label, metricDef.scheme);

  let cached = state.choroplethCache.get(key);
  if (!cached) {
    setStatus(`Building ${metricDef.label} layer…`);
    const hasData = state.indexFeatures.some(f => f.properties[metricDef.col] != null);
    if (!hasData) { setStatus(`No data for ${metricDef.label}.`); return; }
    cached = buildChoropleth(state.indexFeatures, metricDef.col, metricDef.scheme, metricDef.label);
    if (!cached) { setStatus(`No data for ${metricDef.label}.`); return; }
    state.choroplethCache.set(key, cached);
  }

  choroplethGroup.addLayer(cached.layer);
  state.activeHeatKey = key;
  state.styleTarget   = "heat";
  stylePanelEl.style.display = "";
  styleLayerNameEl.textContent = metricDef.label;

  updateHeatmapButtons();
  renderLegend(cached, metricDef.col, metricDef.label);
  setStatus(`${metricDef.label} · ${state.indexFeatures.length.toLocaleString()} cells`);
}

function updateHeatmapButtons() {
  document.querySelectorAll(".heatmap-btn").forEach(btn => {
    const isActive = btn.dataset.key === state.activeHeatKey;
    btn.classList.toggle("active", isActive);
    btn.textContent = isActive ? "Hide" : "Show";
  });
}

function renderHeatmapControls() {
  heatControlsEl.innerHTML = "";
  for (const m of HEATMAP_METRICS) {
    const hasData = state.indexFeatures.some(f => f.properties[m.col] != null);

    const card = document.createElement("div");
    card.className = `control-card${hasData ? "" : " disabled"}`;

    const row = document.createElement("div");
    row.className = "control-row";

    const labelWrap = document.createElement("div");
    labelWrap.style.cssText = "display:flex;align-items:center;gap:6px;flex:1;min-width:0";

    const dot = document.createElement("span");
    dot.className = "metric-dot";
    dot.style.background = METRIC_DOT_COLORS[m.key] || "#888";

    const label = document.createElement("span");
    label.className = "control-title";
    label.textContent = m.label;

    labelWrap.append(dot, label);

    const btn = document.createElement("button");
    btn.className = "heatmap-btn";
    btn.dataset.key = m.key;
    btn.textContent = "Show";
    btn.disabled = !hasData;
    btn.addEventListener("click", () => showMetricChoropleth(m.key));

    row.append(labelWrap, btn);
    card.appendChild(row);

    const noteWrap = document.createElement("div");
    noteWrap.style.cssText = "display:flex;justify-content:space-between;align-items:baseline;gap:6px;margin-top:4px";

    const note = document.createElement("span");
    note.className = "control-note";
    note.style.margin = "0";
    note.textContent = hasData ? m.note : "Not available in current index grid.";

    if (hasData && m.res) {
      const resBadge = document.createElement("span");
      resBadge.className = "control-note";
      resBadge.style.cssText = "margin:0;flex-shrink:0;font-size:0.68rem;opacity:0.75;font-variant-numeric:tabular-nums";
      resBadge.textContent = m.res;
      noteWrap.append(note, resBadge);
    } else {
      noteWrap.appendChild(note);
    }
    card.appendChild(noteWrap);

    heatControlsEl.appendChild(card);
  }
}

// ── Raw overlay layers ────────────────────────────────────────────────────────
function computeRange(features, col) {
  let lo = Infinity, hi = -Infinity;
  for (const f of features) {
    const v = f.properties?.[col];
    if (v != null && !Number.isNaN(+v)) { lo = Math.min(lo, +v); hi = Math.max(hi, +v); }
  }
  return lo <= hi ? { lo, hi } : null;
}

// Source type → color for the source inventory layer
const SOURCE_TYPE_COLORS = {
  landfill:    "#f59e0b",
  wastewater:  "#3b82f6",
  industrial:  "#ef4444",
  livestock:   "#10b981",
  agricultural:"#84cc16",
  brick_kiln:  "#f97316",
  emit_plume:  "#a855f7",
};

function buildOverlayStyle(lm, range) {
  const col   = lm.value_column;
  const stops = COLOR_SCHEMES.hudi;

  const isMainRoad       = lm.key === "roads_main";
  const isLocalRoad      = lm.key === "roads_local";
  const isRoad           = isMainRoad || isLocalRoad;
  const isHotspotGrid    = lm.key === "ch4_hotspot_grid";
  const isSourceInv      = lm.key === "ch4_sources";
  const isTrajectories   = lm.key === "ch4_trajectories";

  return {
    pointToLayer(feature, latlng) {
      // CH4 hotspot grid — plasma-coloured rectangle cells
      if (isHotspotGrid) {
        const level = feature.properties.hotspot_level ?? 0;
        const colors = ["#3b0a6e","#8b2fc9","#d4456e","#f97316","#fde047"];
        const fillColor = colors[Math.min(level, colors.length - 1)];
        const opacity   = level === 0 ? 0.25 : 0.72;
        return L.rectangle(cellBounds(latlng, layerStyle.cellScale), {
          fillColor, fillOpacity: opacity,
          color: "transparent", weight: 0, interactive: level > 0,
        });
      }
      // Source inventory — triangle markers, color by type
      if (isSourceInv) {
        const srcType = feature.properties.source_type ?? "other";
        const color   = SOURCE_TYPE_COLORS[srcType] ?? "#aaaaaa";
        return L.circleMarker(latlng, {
          radius: 7, fillColor: color, color: "#fff",
          weight: 1.5, fillOpacity: 0.9,
        });
      }
      // Default point
      let color = "#3d8ca1";
      if (col && range) {
        const v = feature.properties[col];
        if (v != null) color = lerpColor(stops, (+v - range.lo) / Math.max(range.hi - range.lo, 1e-9));
      }
      return L.circleMarker(latlng, {
        radius: lm.key === "pois" ? 3 : 4,
        color: "transparent", weight: 0, fillColor: color, fillOpacity: 0.8,
      });
    },
    style(feature) {
      if (isTrajectories) {
        const t = feature?.properties?.transport_hr ?? 3;
        const opacity = t <= 1 ? 0.65 : t <= 2 ? 0.45 : t <= 3 ? 0.32 : 0.18;
        return { color: "#e879f9", weight: 0.9, opacity, fillOpacity: 0 };
      }
      if (isMainRoad) {
        const hw = feature?.properties?.highway ?? "";
        const isMajor = /motorway|trunk|primary/.test(hw);
        return { color: "#e8a04a", weight: isMajor ? 2.5 : 1.6, opacity: 0.9, fillOpacity: 0 };
      }
      if (isLocalRoad) {
        return { color: "#c4b8a0", weight: 0.7, opacity: 0.65, fillOpacity: 0 };
      }
      return { color: "#3d8ca1", weight: 1, opacity: 0.85 };
    },
    onEachFeature(feature, layer) {
      const p = feature.properties || {};

      if (isHotspotGrid) {
        if ((p.hotspot_level ?? 0) === 0) return;
        layer.bindPopup(
          `<div class="popup-header">CH₄ Hotspot</div>
           <table class="popup-table">
             <tr><th>Level</th><td>${p.hotspot_label ?? "—"}</td></tr>
             <tr><th>Anomaly</th><td>${p.ch4_anomaly_ppb != null ? (+p.ch4_anomaly_ppb).toFixed(1) + " ppb" : "—"}</td></tr>
             <tr><th>5-mo mean</th><td>${p.ch4_mean_ppb != null ? (+p.ch4_mean_ppb).toFixed(1) + " ppb" : "—"}</td></tr>
             <tr><th>Persistence</th><td>${p.persistence_months ?? "—"} / 5 months</td></tr>
           </table>`
        );
        return;
      }
      if (isSourceInv) {
        const est = p.emission_est_t_yr != null ? (+p.emission_est_t_yr).toFixed(1) + " t CH₄/yr" : "outside hotspot";
        layer.bindPopup(
          `<div class="popup-header">${p.name || "CH₄ Source"}</div>
           <table class="popup-table">
             <tr><th>Type</th><td>${(p.source_type ?? "").replace(/_/g, " ")}</td></tr>
             <tr><th>Data</th><td>${p.source ?? "—"}</td></tr>
             <tr><th>Emission est.</th><td>${est}</td></tr>
             ${p.nearby_anomaly_ppb != null ? `<tr><th>Nearby anomaly</th><td>${(+p.nearby_anomaly_ppb).toFixed(1)} ppb</td></tr>` : ""}
             ${p.note ? `<tr><th>Note</th><td style="font-size:0.74rem">${p.note}</td></tr>` : ""}
           </table>`
        );
        return;
      }
      if (isTrajectories) {
        layer.bindPopup(
          `<div class="popup-header">Back-Trajectory</div>
           <table class="popup-table">
             <tr><th>Transport</th><td>${p.transport_hr} hr</td></tr>
             <tr><th>Receptor anomaly</th><td>${p.anomaly_ppb != null ? (+p.anomaly_ppb).toFixed(1) + " ppb" : "—"}</td></tr>
           </table>`
        );
        return;
      }
      if (!isRoad) {
        const keys = Object.keys(p).slice(0, 10).filter(k => p[k] != null);
        const rows = keys.map(k => `<tr><th>${k}</th><td>${formatVal(k, p[k])}</td></tr>`).join("");
        layer.bindPopup(`<div class="popup-header">${lm.label}</div><table class="popup-table">${rows}</table>`);
        return;
      }
      const name = p.name || p["name:en"] || "";
      const hw   = p.highway || "";
      layer.bindPopup(
        `<div class="popup-header">${name || hw}</div>
         <table class="popup-table">
           ${name ? `<tr><th>Name</th><td>${name}</td></tr>` : ""}
           <tr><th>Type</th><td>${hw}</td></tr>
         </table>`
      );
    },
  };
}

async function toggleRawLayer(lm, checked) {
  if (!checked) {
    const l = state.rawLayers.get(lm.key);
    if (l) rawLayerGroup.removeLayer(l);
    state.activeRawLayers.delete(lm.key);
    return;
  }
  if (!state.rawLayers.has(lm.key)) {
    setStatus(`Loading ${lm.label}…`);
    const data  = await fetchJson(lm.display_path);
    const range = lm.value_column ? computeRange(data.features, lm.value_column) : null;
    state.rawLayers.set(lm.key, L.geoJSON(data, buildOverlayStyle(lm, range)));
  }
  rawLayerGroup.addLayer(state.rawLayers.get(lm.key));
  state.activeRawLayers.add(lm.key);
  setStatus(`${lm.label} loaded.`);
}

const CH4_LAYER_KEYS = new Set(["ch4_hotspot_grid","ch4_sources","ch4_trajectories"]);

function renderLayerControls() {
  layerControlsEl.innerHTML = "";
  let ch4HeaderAdded = false;

  for (const lm of (state.manifest?.raw_layers ?? [])) {
    // Insert a sub-heading before the first CH4 source layer
    if (CH4_LAYER_KEYS.has(lm.key) && !ch4HeaderAdded) {
      const sep = document.createElement("div");
      sep.className = "layer-group-sep";
      sep.textContent = "Methane Source Analysis";
      layerControlsEl.appendChild(sep);
      ch4HeaderAdded = true;
    }

    const card = document.createElement("div");
    card.className = `control-card${lm.available ? "" : " disabled"}`;

    const row = document.createElement("div");
    row.className = "control-row";

    // Dot indicator for CH4 source layers
    const labelWrap = document.createElement("div");
    labelWrap.style.cssText = "display:flex;align-items:center;gap:6px;flex:1;min-width:0";

    if (CH4_LAYER_KEYS.has(lm.key)) {
      const dot = document.createElement("span");
      dot.className = "metric-dot";
      dot.style.background = lm.key === "ch4_hotspot_grid" ? "#a855f7"
                           : lm.key === "ch4_sources"      ? "#f59e0b"
                           : "#e879f9";
      labelWrap.appendChild(dot);
    }

    const label = document.createElement("span");
    label.className = "control-title";
    label.textContent = lm.label;
    labelWrap.appendChild(label);

    const sw  = document.createElement("label");
    sw.className = "toggle-switch";
    const chk = document.createElement("input");
    chk.type = "checkbox"; chk.disabled = !lm.available;
    chk.addEventListener("change", () => toggleRawLayer(lm, chk.checked).catch(e => setStatus(e.message)));
    const track = document.createElement("span");
    track.className = "toggle-track";
    sw.append(chk, track);

    row.append(labelWrap, sw);
    card.appendChild(row);

    const note = document.createElement("div");
    note.className = "control-note";
    if (lm.available) {
      note.textContent = lm.note
        ? `${lm.feature_count.toLocaleString()} features · ${lm.note}`
        : `${lm.feature_count.toLocaleString()} features`;
    } else {
      note.textContent = lm.note || "Run methane_sources.ipynb first.";
    }
    card.appendChild(note);

    // Source type colour legend for source inventory
    if (lm.key === "ch4_sources" && lm.available) {
      const legend = document.createElement("div");
      legend.style.cssText = "display:flex;flex-wrap:wrap;gap:5px 8px;margin-top:6px";
      for (const [type, color] of Object.entries(SOURCE_TYPE_COLORS)) {
        const pill = document.createElement("span");
        pill.style.cssText = `font-size:0.67rem;display:flex;align-items:center;gap:3px;color:var(--muted)`;
        const dot = document.createElement("span");
        dot.style.cssText = `width:7px;height:7px;border-radius:50%;background:${color};flex-shrink:0`;
        pill.append(dot, document.createTextNode(type.replace(/_/g," ")));
        legend.appendChild(pill);
      }
      card.appendChild(legend);
    }

    layerControlsEl.appendChild(card);
  }
}

// ── Custom index ──────────────────────────────────────────────────────────────
function getTotalWeight() {
  let t = 0;
  for (const c of state.metricControls.values()) if (c.metric.available) t += +c.slider.value;
  return t;
}

function updateWeightPercents() {
  const total = getTotalWeight();
  for (const ctrl of state.metricControls.values()) {
    const w   = +ctrl.slider.value;
    const pct = total > 0 ? Math.round((w / total) * 100) : 0;
    ctrl.weightDisplay.textContent = w.toFixed(2);
    ctrl.pctBadge.textContent      = `${pct}%`;
    const show = ctrl.metric.available && w > 0 && pct > 0;
    ctrl.pctBadge.classList.toggle("pct-zero", !show);
  }
}

// Dot color per metric (visual indicator in right panel)
const METRIC_DOT_COLORS = {
  ndvi:              "#2e8b57",
  lst:               "#e05c3a",
  aqi:               "#9b59b6",
  night_lights:      "#f39c12",
  poi_density:       "#2980b9",
  road_density:      "#795548",
  poi_access:        "#00838f",
  building_presence: "#e67e22",
  highrise_share:    "#c0392b",
  ch4:               "#6a4aa0",
};

function createMetricCard(metric) {
  const card = document.createElement("div");
  card.className = `metric-card-compact${metric.available ? "" : " disabled"}`;

  // Top row: colored dot + label + pct badge
  const topRow = document.createElement("div");
  topRow.className = "metric-compact-row";

  const dot = document.createElement("span");
  dot.className = "metric-dot";
  dot.style.background = METRIC_DOT_COLORS[metric.key] || "#888";

  const label = document.createElement("span");
  label.className = "metric-compact-label";
  label.textContent = metric.label;

  const pctBadge = document.createElement("span");
  pctBadge.className = "metric-compact-pct";
  if (!metric.available) pctBadge.classList.add("pct-zero");

  topRow.append(dot, label, pctBadge);
  card.appendChild(topRow);

  // Slider + direction row
  const sliderRow = document.createElement("div");
  sliderRow.className = "metric-slider-row";

  const slider = document.createElement("input");
  slider.type = "range"; slider.min = "0"; slider.max = "4"; slider.step = "0.05";
  slider.value = String(metric.default_weight);
  slider.disabled = !metric.available;

  const weightVal = document.createElement("span");
  weightVal.className = "metric-weight-val";
  weightVal.textContent = metric.default_weight.toFixed(2);

  slider.addEventListener("input", () => {
    weightVal.textContent = (+slider.value).toFixed(2);
    updateWeightPercents();
    if (state.indexVisible) renderIndexLayer();
  });

  sliderRow.append(slider, weightVal);
  card.appendChild(sliderRow);

  // Direction select
  const direction = document.createElement("select");
  direction.className = "metric-dir-select";
  direction.disabled = !metric.available;
  direction.innerHTML = `<option value="higher_better">↑ Higher is better</option><option value="lower_better">↓ Lower is better</option>`;
  direction.value = metric.direction;
  direction.addEventListener("change", () => { if (state.indexVisible) renderIndexLayer(); });
  card.appendChild(direction);

  // Note: range + resolution
  if (!metric.available) {
    const note = document.createElement("div");
    note.className = "control-note";
    note.textContent = "Data not available.";
    card.appendChild(note);
  } else {
    const noteWrap = document.createElement("div");
    noteWrap.style.cssText = "display:flex;justify-content:space-between;align-items:baseline;gap:4px;margin-top:3px";

    if (metric.q05 != null && metric.q95 != null) {
      const range = document.createElement("span");
      range.className = "control-note"; range.style.margin = "0";
      range.textContent = `${formatVal(metric.key, metric.q05)} – ${formatVal(metric.key, metric.q95)}`;
      noteWrap.appendChild(range);
    }
    if (metric.spatial_resolution) {
      const res = document.createElement("span");
      res.className = "control-note";
      res.style.cssText = "margin:0;flex-shrink:0;font-size:0.66rem;opacity:0.7;text-align:right;font-variant-numeric:tabular-nums";
      res.textContent = metric.spatial_resolution.split("·")[0].trim().split(" native")[0];
      noteWrap.appendChild(res);
    }
    card.appendChild(noteWrap);
  }

  state.metricControls.set(metric.key, { slider, direction, metric, weightDisplay: weightVal, pctBadge });
  return card;
}

function renderMetricControls() {
  metricControlsEl.innerHTML = "";
  state.metricControls.clear();
  for (const m of (state.manifest?.metrics ?? [])) {
    metricControlsEl.appendChild(createMetricCard(m));
  }
  updateWeightPercents();
}

function normalize(value, lo, hi, direction) {
  if (value == null || Number.isNaN(+value)) return null;
  let t = Math.max(0, Math.min(1, (+value - lo) / Math.max(hi - lo, 1e-9)));
  if (direction === "lower_better") t = 1 - t;
  return t;
}

function computeIndex(props) {
  let num = 0, den = 0, contributing = 0;
  for (const ctrl of state.metricControls.values()) {
    const w = +ctrl.slider.value;
    if (w <= 0 || !ctrl.metric.available) continue;
    const t = normalize(props[ctrl.metric.column], ctrl.metric.q05, ctrl.metric.q95, ctrl.direction.value);
    if (t == null) continue;
    num += t * w; den += w; contributing++;
  }
  return den === 0 ? { score:null, contributing:0 } : { score:(num/den)*100, contributing };
}

function renderIndexLayer() {
  indexLayerGroup.clearLayers();
  state.indexChoropleth = null;
  if (!state.indexVisible || !state.indexFeatures.length) return;

  // Pre-compute scores, inject as property
  const scored = state.indexFeatures.map(f => {
    const { score, contributing } = computeIndex(f.properties);
    return { ...f, properties: { ...f.properties, _score: score, _contributing: contributing } };
  });

  const schemeKey = layerStyle.colorScheme;
  const built     = buildChoropleth(scored, "_score", schemeKey, "HUDI Index");
  if (!built) return;

  // Override onEachFeature to show full metric breakdown
  built.layer.eachLayer(l => {
    const f = l.feature;
    if (!f) return;
    const score = f.properties._score;
    const contributing = f.properties._contributing;
    if (score == null) return;

    const metrics = state.manifest?.metrics ?? [];
    const metricRows = metrics.filter(m => m.available).map(m => {
      const v = f.properties[m.column];
      const disp = v == null
        ? `<span class="popup-missing">missing</span>`
        : formatVal(m.key, v);
      return `<tr><th>${m.label}</th><td>${disp}</td></tr>`;
    }).join("");

    l.bindPopup(`
      <div class="popup-score">
        <span class="popup-score-label">Index Score</span>
        <span class="popup-score-value">${score.toFixed(1)}</span>
        <span class="popup-score-sub">${contributing} metric${contributing!==1?"s":""} contributing</span>
      </div>
      <table class="popup-table">${metricRows}</table>`);
  });

  indexLayerGroup.addLayer(built.layer);
  state.indexChoropleth = built;

  stylePanelEl.style.display = "";
  state.styleTarget = "index";
  syncStylePanelToState("Custom Index", schemeKey);
  styleLayerNameEl.textContent = "Custom Index";
  renderLegend(built, "_score", "Index Score (0–100)");
  setStatus(`Index · ${state.indexFeatures.length.toLocaleString()} cells`);
}

// ── Style panel ───────────────────────────────────────────────────────────────
function syncStylePanelToState(layerLabel, schemeKey) {
  styleLayerNameEl.textContent = layerLabel;
  spOpacity.value              = Math.round(layerStyle.opacity * 100);
  spOpacityVal.textContent     = `${spOpacity.value}%`;
  spScale.value                = Math.round(layerStyle.cellScale * 100);
  spScaleVal.textContent       = `${spScale.value}%`;
  spScheme.value               = schemeKey || layerStyle.colorScheme;
  spOutlineToggle.checked      = layerStyle.outlineEnabled;
  spOutlineColor.value         = layerStyle.outlineColor;
  spOutlineWidth.value         = Math.round(layerStyle.outlineWidth * 10);
  spOutlineWidthVal.textContent = `${layerStyle.outlineWidth.toFixed(1)} px`;
  spOutlineOpts.style.display  = layerStyle.outlineEnabled ? "" : "none";

  document.querySelectorAll(".class-btn").forEach(b => {
    b.classList.toggle("active", +b.dataset.n === layerStyle.numClasses);
  });
}

// Live: opacity and outline (no rebuild needed)
function applyLiveStyle() {
  layerStyle.opacity       = +spOpacity.value / 100;
  layerStyle.outlineEnabled = spOutlineToggle.checked;
  layerStyle.outlineColor  = spOutlineColor.value;
  layerStyle.outlineWidth  = +spOutlineWidth.value / 10;

  const styleObj = {
    fillOpacity: layerStyle.opacity,
    color:  layerStyle.outlineEnabled ? layerStyle.outlineColor : "transparent",
    weight: layerStyle.outlineEnabled ? layerStyle.outlineWidth : 0,
  };

  // Apply to active metric choropleth
  if (state.activeHeatKey) {
    const cached = state.choroplethCache.get(state.activeHeatKey);
    if (cached) cached.layer.setStyle(styleObj);
  }
  // Apply to index choropleth
  if (state.indexChoropleth) {
    state.indexChoropleth.layer.setStyle(styleObj);
  }
}

// Full rebuild: cell size, num classes, color scheme
function applyRebuildStyle() {
  layerStyle.colorScheme = spScheme.value;
  layerStyle.cellScale   = +spScale.value / 100;

  if (state.activeHeatKey) {
    // Clear cache entry so it rebuilds
    const cached = state.choroplethCache.get(state.activeHeatKey);
    if (cached) choroplethGroup.removeLayer(cached.layer);
    state.choroplethCache.delete(state.activeHeatKey);
    const key = state.activeHeatKey;
    state.activeHeatKey = null;
    showMetricChoropleth(key);
  }
  if (state.indexVisible) {
    renderIndexLayer();
  }
}

// Style panel event wiring
spOpacity.addEventListener("input", () => {
  spOpacityVal.textContent = `${spOpacity.value}%`;
  applyLiveStyle();
});
spOutlineToggle.addEventListener("change", () => {
  spOutlineOpts.style.display = spOutlineToggle.checked ? "" : "none";
  applyLiveStyle();
});
spOutlineColor.addEventListener("input", applyLiveStyle);
spOutlineWidth.addEventListener("input", () => {
  spOutlineWidthVal.textContent = `${(+spOutlineWidth.value / 10).toFixed(1)} px`;
  applyLiveStyle();
});
spScaleVal && spScale.addEventListener("input", () => {
  spScaleVal.textContent = `${spScale.value}%`;
});
document.querySelectorAll(".class-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    layerStyle.numClasses = +btn.dataset.n;
    document.querySelectorAll(".class-btn").forEach(b => b.classList.toggle("active", b === btn));
  });
});
spApplyBtn.addEventListener("click", applyRebuildStyle);
spResetBtn.addEventListener("click", () => {
  Object.assign(layerStyle, DEFAULT_STYLE);
  const schemeKey = state.activeHeatKey
    ? HEATMAP_METRICS.find(m => m.key === state.activeHeatKey)?.scheme ?? "hudi"
    : "hudi";
  syncStylePanelToState(styleLayerNameEl.textContent, schemeKey);
  applyRebuildStyle();
});

// ── Legend ────────────────────────────────────────────────────────────────────
function renderLegend(built, col, label) {
  if (!built) {
    legendEl.innerHTML = `<p class="muted" style="font-size:0.76rem">Activate a layer to see its legend.</p>`;
    return;
  }

  const { breaks, classColors } = built;
  const rows = classColors.map((color, i) => {
    const lo = breaks[i];
    const hi = breaks[i + 1];
    const loStr = lo === hi ? formatVal(col, lo) : `${formatVal(col, lo)} – ${formatVal(col, hi)}`;
    return `<div class="legend-class-row">
      <span class="legend-swatch" style="background:${color}"></span>
      <span class="legend-class-label">${loStr}</span>
    </div>`;
  }).join("");

  legendEl.innerHTML = `
    <div class="legend-layer-title">${label}</div>
    <div class="legend-classes">${rows}</div>
  `;
}

// ── Basemap switcher ──────────────────────────────────────────────────────────
document.querySelectorAll(".basemap-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    const key = btn.dataset.basemap;
    if (key === state.currentBasemap) return;
    map.removeLayer(BASEMAPS[state.currentBasemap]);
    BASEMAPS[key].addTo(map);
    state.currentBasemap = key;
    document.querySelectorAll(".basemap-btn").forEach(b => b.classList.toggle("active", b === btn));
  });
});

// ── Index toggle ──────────────────────────────────────────────────────────────
toggleIndexBtn.addEventListener("click", () => {
  state.indexVisible = !state.indexVisible;
  toggleIndexBtn.textContent = state.indexVisible ? "Hide Index" : "Show Index";
  if (!state.indexVisible) {
    indexLayerGroup.clearLayers();
    state.indexChoropleth = null;
    if (state.styleTarget === "index") {
      state.styleTarget = null;
      if (!state.activeHeatKey) stylePanelEl.style.display = "none";
      renderLegend(null);
    }
  } else {
    renderIndexLayer();
  }
});

resetWeightsBtn && resetWeightsBtn.addEventListener("click", () => {
  for (const ctrl of state.metricControls.values()) {
    ctrl.slider.value    = String(ctrl.metric.default_weight);
    ctrl.direction.value = ctrl.metric.direction;
    ctrl.weightDisplay.textContent = ctrl.metric.default_weight.toFixed(2);
  }
  updateWeightPercents();
  if (state.indexVisible) renderIndexLayer();
});

// ── Init ──────────────────────────────────────────────────────────────────────
async function init() {
  try { state.manifest = await fetchJson("./data/manifest.json"); } catch { /* proceed */ }

  try {
    const gj            = await fetchJson("./data/index_grid_250m.geojson");
    state.indexGeoJson  = gj;
    state.indexFeatures = gj.features;
  } catch {
    toggleIndexBtn.disabled = true;
    toggleIndexBtn.textContent = "Index Unavailable";
    document.getElementById("index-desc").textContent = "Index grid could not be loaded.";
  }

  if (state.manifest?.boundary) await loadBoundary(state.manifest.boundary);

  renderHeatmapControls();
  renderLayerControls();
  renderMetricControls();

  const cells  = state.indexFeatures.length;
  const mAvail = (state.manifest?.metrics ?? []).filter(m => m.available).length;
  setStatus(`Ready · ${cells.toLocaleString()} cells · ${mAvail} metrics`);
}

init();
