# Data Inventory (Lahore UQI)

## Boundaries
| Dataset | Path | Resolution/Type | Source | Used In |
|---|---|---|---|---|
| Lahore UC boundaries | `notebooks/UC_boundaries.geojson` | Polygon | Local admin boundary dataset | AQI aggregation, summaries |
| Lahore study boundary | `notebooks/lahore.geojson` | Polygon | Local boundary file | Grid clipping |

## Environmental layers
| Dataset | Path | Resolution/Type | Source | Used In |
|---|---|---|---|---|
| NDVI points | `notebooks/NDVI/NDVI_Lahore_Oct2024_points_100m.geojson` | 100m points | Google Earth Engine (Landsat/Sentinel workflow) | EQ |
| LST points | `notebooks/LST/LST_Lahore_points_100m.geojson` | 100m points | Google Earth Engine (LST workflow) | EQ |
| Night lights points | `notebooks/NL/VIIRS_NL_Lahore_Oct2024_points_250m.geojson` | 250m points | VIIRS via GEE | EQ (250m model) |
| AQI interpolated by UC | `notebooks/AQI/AQI_2024_10_UC_interpolated.geojson` | Polygon (UC) | OpenAQ + interpolation pipeline | EQ |

## Urban form and access layers
| Dataset | Path | Resolution/Type | Source | Used In |
|---|---|---|---|---|
| Buildings/highrise | `notebooks/Building+Highrise/OpenBuildings_Lahore_2023.geojson` | Points | Open Buildings-derived processing | UD |
| OSM roads | `notebooks/OSM/lahore_roads.gpkg` | Line network | OpenStreetMap | UD + POI access routing |
| POI access heatmap | `notebooks/POI/lahore_poi_access_heatmap.geojson` | Grid + travel-time fields | OSM POIs + road network shortest-path workflow | EQ (`POI_access_sc`) |

## Index outputs
| Output | Path | Resolution | Notes |
|---|---|---|---|
| 250m index (geojson) | `notebooks/lahore_index_250m.geojson` | 250m | Includes NL in EQ |
| 100m index (geojson) | `notebooks/lahore_index_100m.geojson` | 100m | No NL term |
| 250m index (csv) | `notebooks/lahore_index_250m.csv` | 250m | Attribute table export |
| 100m index (csv) | `notebooks/lahore_index_100m.csv` | 100m | Attribute table export |

## Ablation outputs
| Type | Path | Notes |
|---|---|---|
| Metric-drop ablations | `notebooks/ablations/` | One metric/component removed at a time |
| Weight-scenario ablations | `notebooks/ablations_weight_scenarios/` | Alternate weighting schemes (20+ scenarios) |

## Rebuild note
If any input layer above changes, rerun `notebooks/index.ipynb` from start and regenerate outputs + ablations.
