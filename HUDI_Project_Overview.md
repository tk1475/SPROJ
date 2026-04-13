# HUDI Lahore — Project Overview
## Housing Urban Development Index · Senior Project · Spring 2026

**Advisor:** Dr. Tahir  
**Date:** April 2026  
**Status:** Data collection complete · Index operational · Methane source attribution complete

---

## 1 — What Is HUDI?

HUDI (Housing Urban Development Index) is a composite spatial index that quantifies urban livability and environmental quality across Lahore at **250 m grid resolution** (29,492 cells). It combines two sub-indices:

| Sub-index | Weight | Captures |
|---|---|---|
| **EQ** (Environmental Quality) | 40% | Green space, thermal comfort, air quality, light pollution, walkability, methane |
| **UD** (Urban Density) | 60% | Building presence, high-rise density, height, road network density |

Each metric is normalized to a 0–10 scale (robust 5th–95th percentile). The final score is a weighted average that gracefully handles missing data — cells with partial data still render using available metrics.

---

## 2 — Data Collected

### 2.1 Spatial Coverage

| Parameter | Value |
|---|---|
| City | Lahore, Pakistan |
| Admin units | 171 Union Councils |
| Grid resolution | 250 m × 250 m |
| Total cells | 29,492 |
| Coordinate system | WGS84 (EPSG:4326) / UTM 43N (EPSG:32643) |
| Temporal window | Oct 2025 – Feb 2026 (most layers) |

### 2.2 Environmental Quality (EQ) Metrics

| Metric | Source | Native Resolution | File | Features | Coverage |
|---|---|---|---|---|---|
| **NDVI** (vegetation) | Landsat 8/9 via GEE | 100 m | `NDVI_Lahore_Feb2026_points_100m.geojson` | 210,461 | 91% |
| **LST** (land surface temp) | Landsat 8/9 via GEE | 100 m | `LST_Lahore_Feb2026_points_100m.geojson` | 209,567 | 91% |
| **AQI** (PM₂.₅) | OpenAQ / WAQI | 64 stations | `AQI_Lahore_Feb2026_points.geojson` | 64 | 100% interpolated |
| **CH₄** (methane column) | TROPOMI/Sentinel-5P via GEE | ~5,500 m | `CH4_Lahore_Feb2026_points_250m.geojson` | 33,678 | 91% |
| **POI Accessibility** | Overture Maps + OSM road graph | 250 m | `lahore_poi_access_heatmap.geojson` | 28,804 | 86% |
| **Night Lights** | VIIRS/SNPP via GEE | 500 m | `VIIRS_NL_Lahore_Feb2026_points_250m.geojson` | 33,678 | 91% |

**EQ value ranges (in index grid):**
- NDVI: −0.45 to +0.88 (median ~0.3 — typical semi-arid urban fringe)
- LST: 19.2°C to 34.0°C (range reflects Feb winter; summer would be 35–55°C)
- AQI (PM₂.₅): 171–259 (all "Very Unhealthy" to "Hazardous" — severe pollution city)
- CH₄: 1,940–1,988 ppb (above 1,920 ppb global background; landfill/sewage signal)
- POI access: 0–18.6 min walk to nearest POI (median ~2 min in dense areas)
- Night Lights: 0.73–200 nW/cm²/sr (bright core, dark periphery)

### 2.3 Urban Density (UD) Metrics

| Metric | Source | Resolution | File | Features |
|---|---|---|---|---|
| **Building Presence** | Google Open Buildings v3 | 250 m | `building_footprint_lahore_openbuildings_2023_points_250m.geojson` | 29,510 |
| **High-Rise Share** | Google Open Buildings v3 | 250 m | `highrise_lahore_openbuildings_2023_points_250m.geojson` | 29,510 |
| **Road Density** | OpenStreetMap | Lines → 250 m | `lahore_roads.gpkg` | 96,495 segments / 18,937 km |
| **POI Density** | Overture Maps | Points → 250 m | `pois_lahore.geojson` | 36,645 |

**POI breakdown (top categories):** Restaurant (2,510), Real estate (2,190), Fashion (1,965), Professional services (1,526), Events (1,145), Beauty (1,065), Hardware/home (912), Education (909) — 298 unique categories total.

### 2.4 Composite Index Grid

**File:** `frontend/data/index_grid_250m.geojson` (13.1 MB, 29,492 cells)

| Column | Description |
|---|---|
| `cell_id` | Unique cell identifier |
| `area_ha` | Cell area in hectares |
| `aqi`, `lst`, `ndvi`, `night_lights`, `poi_density`, `building_presence`, `highrise_share`, `poi_access`, `ch4`, `road_density` | Raw metric values |

### 2.5 Methane Source Attribution (separate analysis)

**Directory:** `notebooks/methane/`

| File | Contents |
|---|---|
| `CH4_Lahore_Feb2026_points_250m.geojson` | Single-month TROPOMI CH₄ at 250 m (33,678 pts) |
| `CH4_Lahore_Feb2026_5500m.tif` | GeoTIFF at native 5.5 km resolution |
| `ch4_stack_250m.geojson` | 5-month stack: mean, std, min, max, anomaly, persistence |
| `CH4_hotspot_grid_250m.geojson` | Hotspot classification (background/moderate/high/extreme) |
| `CH4_source_inventory.geojson` | 160 source locations (OSM + literature) with emission estimates |
| `CH4_back_trajectories.geojson` | 20,268 back-trajectory line segments (1/2/3/6 hr transport) |
| `wind_field.geojson` | 5-month ERA5 10-m wind field |

### 2.6 Supporting / Administrative Data

| File | Description |
|---|---|
| `data/Lahore UCs/Lahore UC.shp` | 171 Union Council polygons |
| `notebooks/lahore.geojson` | Merged city boundary |
| `notebooks/OSM/lahore_roads.gpkg` | Full OSM road network (96,495 segments, 18,937 km) |
| `notebooks/scrapers/graana_scraper.ipynb` | Graana.com property price scraper |
| `notebooks/scrapers/zameen_scraper.ipynb` | Zameen.com property price scraper |

### 2.7 Frontend Application

**Directory:** `frontend/`

A Leaflet.js web map with:
- 3-column layout: Layers panel | Map | Index controls
- 9 metric choropleth layers (QGIS-style discrete grid cells, plasma/custom color schemes)
- QGIS-equivalent layer styling: opacity, cell size, color classes (3/5/7), outline
- 2 road overlays: Main Roads (7,103 segments) and Local Streets (9,933 segments)
- Custom index composer with per-metric weight sliders, direction toggles, live recalculation
- Spatial resolution badge on every metric card
- Dark-mode plasma visualization for CH₄

---

## 3 — Notebooks

| Notebook | Purpose | Status |
|---|---|---|
| `notebooks/LST/LST.ipynb` | Landsat LST fetch + export via GEE | Complete |
| `notebooks/NDVI/NDVI.ipynb` | Landsat NDVI fetch + export via GEE | Complete |
| `notebooks/NL/NL.ipynb` | VIIRS Night Lights via GEE | Complete |
| `notebooks/AQI/AQI.ipynb` | OpenAQ/WAQI station scrape + UC interpolation | Complete |
| `notebooks/OSM/osm.ipynb` | OSM road network extraction | Complete |
| `notebooks/POI/poi.ipynb` | Overture Maps POI download + processing | Complete |
| `notebooks/POI/access.ipynb` | POI accessibility (walk-time on road graph) | Complete |
| `notebooks/buildings/building_footprint.ipynb` | Google Open Buildings processing | Complete |
| `notebooks/buildings/highrise_2023.ipynb` | High-rise classification from building heights | Complete |
| `notebooks/methane/methane.ipynb` | TROPOMI CH₄ single-month export | Complete |
| `notebooks/methane/methane_sources.ipynb` | 5-month stack + back-trajectories + source attribution | Complete |
| `notebooks/index.ipynb` | Full HUDI index construction (250 m + 100 m) | Complete |
| `notebooks/scrapers/graana_scraper.ipynb` | Property price data scraper | Partial |
| `notebooks/scrapers/zameen_scraper.ipynb` | Property price data scraper | Partial |

---

## 4 — Index Formula

```
EQ (with NL)  = 0.35×NDVI_sc + 0.15×LST_sc + 0.10×NL_sc + 0.20×AQI_sc + 0.10×POI_access_sc + 0.10×CH4_sc

UD            = 0.10×BFP_presence_sc + 0.30×Highrise_decay_sc + 0.20×Height_sc
              + 0.20×BFP_density_sc + 0.20×Road_density_sc

Overall HUDI  = 0.40×EQ + 0.60×UD
```

All metrics scaled 0–10 (robust 5–95th percentile). Missing cells handled by renormalizing weights over available data.

---

## 5 — Potential Directions: HUDI

### 5.1 Data Enhancements

**A. Property price integration (high value)**
The scrapers for Zameen.com and Graana.com are partially built. Linking property prices to HUDI scores would be the most impactful near-term addition — creates an econometric linkage between environmental quality, urban density, and real estate valuation. This alone is a publishable result.

**B. Temporal multi-year index**
Currently single-month (Feb 2026). Running the same pipeline for Feb 2024 and Feb 2025 would produce a 3-year trend. LST, NDVI, and NL are available going back to ~2014 on GEE. This enables urban change detection — quantifying how specific neighborhoods have changed in livability over time.

**C. NO₂ / SO₂ from TROPOMI**
Lahore has severe traffic-related NO₂ pollution. `COPERNICUS/S5P/OFFL/L3_NO2` is available on GEE with the same workflow as CH₄. NO₂ is at ~3.5 km native resolution, finer than CH₄. This would strengthen the EQ sub-index considerably.

**D. Flood risk layer**
Lahore lies on the Ravi floodplain. JRC global surface water and SRTM DEM slope data are both on GEE. A flood risk score (low-lying + near-water + historical inundation) would add a climate resilience dimension to the EQ component.

**E. Urban Heat Island (UHI) characterization**
Instead of raw LST, compute UHI intensity = LST(cell) − LST(city_mean). This removes the seasonal bias and isolates the local cooling/heating effect of vegetation and impervious surfaces. More interpretable for urban planning audiences.

**F. Overture Maps POI upgrade**
The professor shared the Overture Maps link. Replacing OSM POIs with the full Overture 72M POI catalog would significantly improve POI density and accessibility accuracy, especially for smaller amenities not well-mapped in OSM.

### 5.2 Methodological Enhancements

**G. Spatial autocorrelation analysis (Moran's I)**
Test whether HUDI scores are spatially clustered. If Moran's I is high (expected), this validates that the index captures real urban structure rather than noise. Also identifies spatial outliers — cells that are anomalously high/low vs. their neighbors.

**H. PCA / factor analysis for weight optimization**
Instead of assumed weights, use PCA on the 10 metric layers to derive empirical weights. This is defensible for a paper — you can show the first principal component captures 60–70% of variance and aligns with intuitive urban quality gradients.

**I. Union-Council level aggregation**
Aggregate the 250 m grid to the 171 UC level. Compare with PDMA/LDA administrative indicators where available. This creates a product directly usable by Lahore Development Authority (LDA) planners.

**J. Machine learning equity analysis**
Train a regression model predicting property prices from HUDI components. SHAP values reveal which components drive prices in which neighborhoods — connecting environmental quality to economic inequality.

### 5.3 Visualization Enhancements

**K. Time-slider for temporal index**
If multi-year data is added, a Leaflet time-slider plugin would let users scrub through 2014–2026 and watch urban quality change.

**L. Neighborhood comparison tool**
Click two cells → side-by-side radar chart comparing their metric profiles. Useful for demonstrating the index to non-technical stakeholders.

---

## 6 — Potential Directions: Methane

### 6.1 Immediate Improvements

**A. Seasonal stack (full year)**
The current stack covers 5 months. Running Oct 2024 – Sep 2025 (12 months) would reveal seasonal patterns — rice harvest burning (Oct–Nov), winter inversion trapping (Dec–Feb), and monsoon ventilation (Jul–Sep). This is the most tractable near-term improvement.

**B. NO₂ co-analysis for combustion fingerprinting**
Landfill/sewage CH₄ has low NO₂ (microbial source). Industrial/traffic CH₄ has high co-located NO₂ (combustion). Plotting the CH₄/NO₂ ratio over Lahore creates a source fingerprint map that distinguishes biogenic from thermogenic emissions — directly analogous to what GHGSat does with multi-species observations.

**C. Improved Gaussian inversion with actual ERA5 hourly profiles**
The current inversion uses monthly mean wind. Using hourly ERA5 wind profiles (available in GEE) with a proper Pasquill-Gifford stability classification based on solar radiation and wind speed would give more accurate σ_y, σ_z and significantly better emission rate estimates.

**D. HYSPLIT back-trajectory validation**
NOAA's HYSPLIT model (free, online API) computes proper 3D atmospheric back-trajectories. Comparing HYSPLIT results against our simple linear back-trajectory would validate or correct the source attribution. HYSPLIT handles vertical mixing that the simple model ignores.

**E. Calibration against known emission factors**
Mahmood Booti landfill receives ~2,500 tonnes/day of waste. Using IPCC Tier 2 landfill emission factors (0.26 Mg CH₄/Mg waste), the expected emission is ~650 tonnes CH₄/yr. Comparing this against the Gaussian inversion result provides a calibration check for the method.

### 6.2 Data Upgrades

**F. GOSAT-2 Japan column data**
GOSAT-2 has ~10 km resolution but higher radiometric precision than TROPOMI, especially over bright urban surfaces. The National Institute for Environmental Studies (NIES) Japan provides free Level 2 data. Over-sampling GOSAT-2 with TROPOMI creates a multi-sensor ensemble with reduced uncertainty.

**G. Methane emission inventory for Pakistan**
Pakistan has no published city-level CH₄ emission inventory. Combining the TROPOMI-derived hotspot map with an OSM-based emission inventory (waste + wastewater + industrial sector using IPCC Tier 1 factors) would produce the first such estimate for Lahore. High novelty for a Pakistani audience.

**H. EDGAR global inventory comparison**
JRC EDGAR provides gridded global CH₄ emissions at 0.1° (~11 km). Comparing EDGAR's sectoral attribution (agriculture, waste, fossil fuels) against the TROPOMI-derived anomaly map would validate or challenge EDGAR's assumptions for Lahore — publishable as a methods comparison.

---

## 7 — Paper Ideas

### Paper 1 (Core, near-term)
**"HUDI: A Multi-Dimensional Urban Quality Index for Lahore, Pakistan at 250 m Resolution Using Open Satellite and Geospatial Data"**

- Audience: Remote sensing, urban planning, GIScience
- Core contribution: First fine-grained composite urban quality index for a major South Asian megacity using entirely open data
- Key results: Spatial distribution of HUDI across 29,492 cells; EQ vs. UD spatial patterns; correlation between metrics
- Validation: Comparison with known affluent/deprived neighborhoods, property prices if scrapers complete
- Length: ~8,000 words, 6–8 figures

### Paper 2 (Methane, standalone)
**"City-Scale Methane Emission Source Attribution Using TROPOMI/Sentinel-5P and ERA5 Wind Back-Trajectories: A Case Study of Lahore, Pakistan"**

- Audience: Atmospheric science, environmental engineering, GHG monitoring
- Core contribution: First satellite-based CH₄ source attribution for a major South Asian city; demonstrates Gaussian plume inversion with publicly available data
- Key results: Persistent hotspot locations; emission rate estimates (tonne CH₄/yr) per source type; OSM + literature source correlation
- Novelty: Pakistan has no published city-level CH₄ inventory — this would be the first
- Length: ~7,000 words, 5–7 figures

### Paper 3 (Joint HUDI + property prices, if scrapers complete)
**"Urban Environmental Quality and Property Valuation: A Spatial Hedonic Analysis Using the HUDI Index for Lahore"**

- Audience: Urban economics, real estate, planning policy
- Core contribution: Econometric linkage between satellite-derived environmental quality and real estate markets in a developing-country megacity
- Method: Spatial hedonic regression (OLS + spatial lag model); SHAP analysis of which HUDI components drive prices in which neighborhoods
- Key results: EQ coefficient on property prices; spatial heterogeneity — environmental premium varies by neighborhood type
- Policy relevance: Direct input for LDA / urban planning bodies

### Paper 4 (Methods paper, if temporal data added)
**"Temporal Urban Quality Monitoring with Open Remote Sensing Data: Tracking Lahore's Environmental and Density Changes 2014–2026"**

- Audience: GIScience, urban remote sensing
- Core contribution: Systematic methodology for reproducible annual urban quality monitoring at sub-km scale using only GEE + OSM
- Can be framed as a transferable framework applicable to any South/Southeast Asian city

---

## 8 — Target Conferences and Journals

### Conferences

| Event | Deadline (typical) | Fit |
|---|---|---|
| **IEEE IGARSS 2026** (International Geoscience & Remote Sensing Symposium) | ~Jan 2026 | Core venue for satellite RS work; Paper 1 or 2 |
| **ACM SIGSPATIAL 2026** | ~Jun 2026 | GIScience, spatial analysis; Paper 1 or 3 |
| **ISPRS Congress 2024** (quadrennial, next ~2028) | — | Flagship photogrammetry/RS conference |
| **AGU Fall Meeting 2026** (Dec, San Francisco) | ~Jul 2026 | Earth science; Paper 2 (methane) |
| **EGU General Assembly 2027** (Vienna) | ~Jan 2027 | Atmospheric/geoscience; Paper 2 |
| **Urban Climate Conference 2026** | TBD | Urban heat, EQ; Papers 1 and 4 |
| **ASCE/CRC Smart Cities** | Rolling | Urban systems; Paper 1 or 3 |
| **Pakistan Engineering Congress (PEC)** | Nov | Local high-impact; all papers |
| **ICET (NUST)** | Sep–Oct | Leading Pakistan engineering conference; all papers |

### Journals

| Journal | IF | Fit |
|---|---|---|
| **Remote Sensing of Environment** | ~13 | Best fit for Papers 1, 2, 4 |
| **ISPRS Journal of Photogrammetry and Remote Sensing** | ~12.7 | Papers 1, 2, 4 |
| **Atmospheric Measurement Techniques (AMT)** | ~5.4 | Paper 2 (methane) |
| **Science of the Total Environment** | ~9.8 | Papers 1, 2, 3 — multidisciplinary |
| **Urban Climate** | ~6.5 | Paper 1 (HUDI) |
| **Computers, Environment and Urban Systems (CEUS)** | ~7.3 | Papers 1, 3 |
| **International Journal of Applied Earth Observation (JAG)** | ~7.5 | Papers 1, 2 |
| **Environmental Science & Technology (ES&T)** | ~11.4 | Paper 2 (methane, strong results needed) |
| **PLOS ONE** | ~3.7 | Open access, broad; any paper |
| **Environmental Challenges (Elsevier)** | ~3.5 | South Asia environmental focus; Papers 1–3 |

**Recommendation for first submission:** Remote Sensing of Environment for Papers 1 or 2; Urban Climate for Paper 1 as a backup. For methane specifically, Atmospheric Measurement Techniques is highly credible for satellite-based emission work.

---

## 9 — Priority Roadmap

**Immediate (to finish the project as-is):**
1. Run `methane_sources.ipynb` to completion — generate hotspot grid, source inventory, attribution map
2. Complete property price scrapers (Zameen/Graana) — even partial data is useful for Paper 3
3. Write Paper 1 draft — the data and index are complete enough now

**Short-term (1–2 months):**
4. Add NO₂ layer from TROPOMI (1 day of work, same pipeline as CH₄)
5. Add UHI intensity (replace raw LST with LST anomaly relative to city mean)
6. Seasonal CH₄ stack (Oct 2024 – Sep 2025) — Paper 2 upgrade

**Medium-term (3–6 months):**
7. Multi-year NDVI/LST stack (2018–2026) — enables Paper 4
8. Overture Maps POI upgrade — better POI accuracy
9. HYSPLIT validation of back-trajectories — Paper 2 credibility

---

*Document prepared April 2026. All data, notebooks, and the frontend application are in the project repository at `SPROJ - Dr Tahir/SPROJ/`.*
