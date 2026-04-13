from __future__ import annotations

import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point, box


ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
DATA_DIR = FRONTEND_DIR / "data"
LAYERS_DIR = DATA_DIR / "layers"
BOUNDARY_PATH = ROOT / "notebooks" / "lahore.geojson"
ROADS_PATH = ROOT / "notebooks" / "OSM" / "lahore_roads.gpkg"
CRS_METRIC = "EPSG:32643"
GRID_SIZE_M = 250


RAW_LAYER_CONFIGS = [
    {
        "key": "aqi",
        "label": "AQI Monitors",
        "pattern": "notebooks/AQI/AQI_Lahore_*_points.geojson",
        "kind": "points",
        "value_column": "pm25_aqi",
        "display_columns": ["location", "pm25_monthly_avg", "pm25_aqi", "pm25_aqi_category", "month"],
        "max_features": 5000,
        "metric": {
            "key": "aqi", "label": "AQI", "column": "aqi",
            "direction": "lower_better", "default_weight": 1.0,
            "spatial_resolution": "64 station points → 250 m (interpolated)",
            "data_source": "OpenAQ / WAQI",
        },
    },
    {
        "key": "lst",
        "label": "LST Points",
        "pattern": "notebooks/LST/LST_Lahore_*_points_100m.geojson",
        "kind": "points",
        "value_column": "val",
        "display_columns": ["val"],
        "max_features": 15000,
        "metric": {
            "key": "lst", "label": "Land Surface Temp", "column": "lst",
            "direction": "lower_better", "default_weight": 1.0,
            "spatial_resolution": "100 m native (Landsat 8/9) → 250 m",
            "data_source": "Landsat 8/9 · GEE",
        },
    },
    {
        "key": "ndvi",
        "label": "NDVI Points",
        "pattern": "notebooks/NDVI/NDVI_Lahore_*_points_100m.geojson",
        "kind": "points",
        "value_column": "val",
        "display_columns": ["val"],
        "max_features": 15000,
        "metric": {
            "key": "ndvi", "label": "NDVI", "column": "ndvi",
            "direction": "higher_better", "default_weight": 1.0,
            "spatial_resolution": "100 m native (Landsat 8/9) → 250 m",
            "data_source": "Landsat 8/9 · GEE",
        },
    },
    {
        "key": "night_lights",
        "label": "Night Lights",
        "pattern": "notebooks/NL/VIIRS_NL_Lahore_*_points_250m.geojson",
        "kind": "points",
        "value_column": "val",
        "display_columns": ["val"],
        "max_features": 15000,
        "metric": {
            "key": "night_lights", "label": "Night Lights", "column": "night_lights",
            "direction": "lower_better", "default_weight": 1.0,
            "spatial_resolution": "500 m native (VIIRS/SNPP) → 250 m",
            "data_source": "VIIRS / SNPP · GEE",
        },
    },
    {
        "key": "pois",
        "label": "POIs",
        "pattern": "notebooks/POI/data/pois_lahore.geojson",
        "kind": "points",
        "value_column": None,
        "display_columns": ["basic_category", "confidence", "operating_status"],
        "max_features": 12000,
        "metric": {
            "key": "poi_density", "label": "POI Density", "column": "poi_density",
            "direction": "higher_better", "default_weight": 1.0,
            "spatial_resolution": "Point data → 250 m density (POIs/ha)",
            "data_source": "Overture Maps / OSM",
        },
    },
    {
        "key": "building_footprint",
        "label": "Building Footprint",
        "pattern": "notebooks/buildings/building_footprint_lahore_openbuildings_*_points_*m.geojson",
        "kind": "points",
        "value_column": "presence_mean",
        "display_columns": ["presence_mean", "built_share"],
        "max_features": 15000,
        "metric": {
            "key": "building_presence", "label": "Building Presence", "column": "building_presence",
            "direction": "higher_better", "default_weight": 0.5,
            "spatial_resolution": "250 m grid (Google Open Buildings)",
            "data_source": "Google Open Buildings v3",
        },
    },
    {
        "key": "highrise",
        "label": "High-Rise",
        "pattern": "notebooks/buildings/highrise_lahore_openbuildings_*_points_*m.geojson",
        "kind": "points",
        "value_column": "highrise_share",
        "display_columns": ["height_mean", "highrise_share"],
        "max_features": 15000,
        "metric": {
            "key": "highrise_share", "label": "High-Rise Share", "column": "highrise_share",
            "direction": "higher_better", "default_weight": 0.25,
            "spatial_resolution": "250 m grid (Google Open Buildings)",
            "data_source": "Google Open Buildings v3",
        },
    },
    {
        "key": "poi_access",
        "label": "POI Access",
        "pattern": "notebooks/POI/lahore_poi_access_heatmap.geojson",
        "kind": "points",
        "value_column": "n3_min",
        "display_columns": ["n1_min", "n3_min", "snap_dist_m", "k_found", "valid_snap"],
        "max_features": 15000,
        "metric": {
            "key": "poi_access", "label": "POI Accessibility", "column": "poi_access",
            "direction": "lower_better", "default_weight": 1.0,
            "spatial_resolution": "250 m grid · walk-time on OSM road network",
            "data_source": "OSM road graph · Overture/OSM POIs",
        },
    },
    {
        "key": "ch4",
        "label": "Methane (CH₄)",
        "pattern": "notebooks/Methane/CH4_Lahore_*_points_250m.geojson",
        "kind": "points",
        "value_column": "val",
        "display_columns": ["val"],
        "max_features": 15000,
        "metric": {
            "key": "ch4", "label": "Methane (CH₄)", "column": "ch4",
            "direction": "lower_better", "default_weight": 0.5,
            "spatial_resolution": "~5,500 m native (TROPOMI/S5P) → 250 m",
            "data_source": "Sentinel-5P TROPOMI · GEE",
        },
    },
]

ROADS_METRIC = {
    "key": "road_density",
    "label": "Road Density",
    "column": "road_density",
    "direction": "higher_better",
    "default_weight": 0.5,
    "spatial_resolution": "Line data → 250 m (m road / ha)",
    "data_source": "OpenStreetMap",
}


def latest_match(pattern: str) -> Path | None:
    matches = sorted(ROOT.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def read_gdf(path: Path) -> gpd.GeoDataFrame:
    return gpd.read_file(path)


def restore_openbuildings_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.empty:
        return gdf
    if "cell_id" not in gdf.columns:
        return gdf
    if not gdf.geometry.is_empty.all():
        return gdf

    cell_ids = gdf["cell_id"].astype(str).str.extract(r"^\s*(\d+),(\d+)\s*$")
    if cell_ids.isna().any().any():
        return gdf

    x = cell_ids[0].astype(float) * GRID_SIZE_M + (GRID_SIZE_M / 2.0)
    y = cell_ids[1].astype(float) * GRID_SIZE_M + (GRID_SIZE_M / 2.0)
    repaired = gdf.drop(columns="geometry").copy()
    repaired = gpd.GeoDataFrame(
        repaired,
        geometry=gpd.points_from_xy(x, y, crs=CRS_METRIC),
        crs=CRS_METRIC,
    )
    return repaired.to_crs(4326)


def ensure_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        return gdf.set_crs(4326)
    if gdf.crs.to_epsg() != 4326:
        return gdf.to_crs(4326)
    return gdf


def sample_gdf(gdf: gpd.GeoDataFrame, max_features: int) -> gpd.GeoDataFrame:
    if len(gdf) <= max_features:
        return gdf.copy()
    step = max(1, math.ceil(len(gdf) / max_features))
    return gdf.iloc[::step].copy()


def build_grid(boundary_wgs84: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    boundary_m = boundary_wgs84.to_crs(CRS_METRIC)
    boundary_union = boundary_m.union_all()
    minx, miny, maxx, maxy = boundary_m.total_bounds

    xs = np.arange(math.floor(minx / GRID_SIZE_M) * GRID_SIZE_M, math.ceil(maxx / GRID_SIZE_M) * GRID_SIZE_M, GRID_SIZE_M)
    ys = np.arange(math.floor(miny / GRID_SIZE_M) * GRID_SIZE_M, math.ceil(maxy / GRID_SIZE_M) * GRID_SIZE_M, GRID_SIZE_M)
    cells = [box(x, y, x + GRID_SIZE_M, y + GRID_SIZE_M) for x in xs for y in ys]

    grid = gpd.GeoDataFrame({"geometry": cells}, crs=CRS_METRIC)
    grid = grid[grid.intersects(boundary_union)].copy()
    grid["cell_id"] = np.arange(len(grid))
    grid["area_m2"] = grid.geometry.area
    grid["area_ha"] = grid["area_m2"] / 10000.0
    return grid


def aggregate_point_mean(points: gpd.GeoDataFrame, value_column: str, grid_m: gpd.GeoDataFrame, output_column: str) -> pd.Series:
    if points.empty or value_column not in points.columns:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    points_m = ensure_wgs84(points).to_crs(CRS_METRIC)[[value_column, "geometry"]].dropna(subset=["geometry"])
    joined = gpd.sjoin(points_m, grid_m[["cell_id", "geometry"]], how="inner", predicate="within")
    if joined.empty:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    values = joined.groupby("cell_id")[value_column].mean()
    return grid_m["cell_id"].map(values).rename(output_column)


def aggregate_point_count_density(points: gpd.GeoDataFrame, grid_m: gpd.GeoDataFrame, output_column: str) -> pd.Series:
    if points.empty:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    points_m = ensure_wgs84(points).to_crs(CRS_METRIC)[["geometry"]].dropna(subset=["geometry"])
    joined = gpd.sjoin(points_m, grid_m[["cell_id", "geometry"]], how="inner", predicate="within")
    counts = joined.groupby("cell_id").size()
    out = grid_m["cell_id"].map(counts).fillna(0.0) / grid_m["area_ha"]
    return out.rename(output_column)


def aggregate_nearest_value(points: gpd.GeoDataFrame, value_column: str, grid_m: gpd.GeoDataFrame, output_column: str) -> pd.Series:
    if points.empty or value_column not in points.columns:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    points_m = ensure_wgs84(points).to_crs(CRS_METRIC)[[value_column, "geometry"]].dropna(subset=[value_column, "geometry"])
    if points_m.empty:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    centroids = grid_m[["cell_id", "geometry"]].copy()
    centroids["geometry"] = centroids.geometry.centroid
    joined = gpd.sjoin_nearest(centroids, points_m, how="left", distance_col="dist_m")
    values = joined.groupby("cell_id")[value_column].mean()
    return grid_m["cell_id"].map(values).rename(output_column)


def aggregate_line_density(roads: gpd.GeoDataFrame, grid_m: gpd.GeoDataFrame, output_column: str) -> pd.Series:
    if roads.empty:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    roads_m = roads.to_crs(CRS_METRIC)[["geometry"]].dropna(subset=["geometry"])
    overlay = gpd.overlay(roads_m, grid_m[["cell_id", "geometry"]], how="intersection", keep_geom_type=False)
    if overlay.empty:
        return pd.Series(np.nan, index=grid_m.index, name=output_column)

    overlay["len_m"] = overlay.geometry.length
    length_by_cell = overlay.groupby("cell_id")["len_m"].sum()
    out = grid_m["cell_id"].map(length_by_cell).fillna(0.0) / grid_m["area_ha"]
    return out.rename(output_column)


def metric_summary(values: pd.Series) -> dict:
    clean = pd.to_numeric(values, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return {"available": False, "min": None, "max": None, "q05": None, "q95": None}
    return {
        "available": True,
        "min": float(clean.min()),
        "max": float(clean.max()),
        "q05": float(clean.quantile(0.05)),
        "q95": float(clean.quantile(0.95)),
    }


def write_geojson(gdf: gpd.GeoDataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(path, driver="GeoJSON")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LAYERS_DIR.mkdir(parents=True, exist_ok=True)

    boundary = ensure_wgs84(read_gdf(BOUNDARY_PATH))
    grid_m = build_grid(boundary)
    centroids = grid_m[["cell_id", "area_ha", "geometry"]].copy()
    centroids["geometry"] = centroids.geometry.centroid
    centroids = centroids.set_crs(CRS_METRIC).to_crs(4326)

    manifest = {
        "boundary": "../notebooks/lahore.geojson",
        "grid_size_m": GRID_SIZE_M,
        "raw_layers": [],
        "metrics": [],
    }

    layer_data = {}
    for config in RAW_LAYER_CONFIGS:
        path = latest_match(config["pattern"])
        layer_entry = {
            "key": config["key"],
            "label": config["label"],
            "kind": config["kind"],
            "source_path": str(path.relative_to(ROOT)) if path else None,
            "display_path": None,
            "value_column": config["value_column"],
            "available": False,
            "feature_count": 0,
        }

        metric = dict(config["metric"])
        metric["available"] = False

        if path and path.exists():
            try:
                gdf = ensure_wgs84(read_gdf(path))
            except Exception as exc:
                print(f"Skipping unreadable layer {path}: {exc}")
                gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
            if config["key"] in {"building_footprint", "highrise"}:
                gdf = restore_openbuildings_geometry(gdf)
            layer_entry["feature_count"] = int(len(gdf))
            layer_data[config["key"]] = gdf

            if not gdf.empty:
                keep_cols = [col for col in config["display_columns"] if col in gdf.columns]
                sampled = sample_gdf(gdf[keep_cols + ["geometry"]], config["max_features"])
                out_path = LAYERS_DIR / f"{config['key']}.geojson"
                write_geojson(sampled, out_path)
                layer_entry["display_path"] = f"./data/layers/{config['key']}.geojson"
                layer_entry["available"] = True

                if config["key"] == "pois":
                    centroids[metric["column"]] = aggregate_point_count_density(gdf, grid_m, metric["column"])
                elif config["key"] == "aqi":
                    centroids[metric["column"]] = aggregate_nearest_value(gdf, "pm25_aqi", grid_m, metric["column"])
                elif config["key"] == "poi_access":
                    centroids[metric["column"]] = aggregate_point_mean(gdf, "n3_min", grid_m, metric["column"])
                    centroids["poi_access_n1"] = aggregate_point_mean(gdf, "n1_min", grid_m, "poi_access_n1")
                elif config["key"] == "highrise":
                    centroids[metric["column"]] = aggregate_point_mean(gdf, "highrise_share", grid_m, metric["column"])
                    centroids["height_avg"] = aggregate_point_mean(gdf, "height_mean", grid_m, "height_avg")
                elif config["key"] == "building_footprint":
                    centroids[metric["column"]] = aggregate_point_mean(gdf, "presence_mean", grid_m, metric["column"])
                else:
                    centroids[metric["column"]] = aggregate_point_mean(gdf, config["value_column"], grid_m, metric["column"])

                metric.update(metric_summary(centroids[metric["column"]]))
            else:
                if metric["column"] not in centroids.columns:
                    centroids[metric["column"]] = np.nan
        else:
            if metric["column"] not in centroids.columns:
                centroids[metric["column"]] = np.nan

        manifest["raw_layers"].append(layer_entry)
        manifest["metrics"].append(metric)

    roads = read_gdf(ROADS_PATH)
    roads = ensure_wgs84(roads)

    MAIN_ROAD_TYPES  = "motorway|trunk|primary|secondary|tertiary"
    LOCAL_ROAD_TYPES = "residential|living_street|service|unclassified"

    if "highway" in roads.columns:
        hw = roads["highway"].astype(str)
        roads_main  = roads[hw.str.contains(MAIN_ROAD_TYPES,  regex=True, na=False)].copy()
        roads_local = roads[hw.str.contains(LOCAL_ROAD_TYPES, regex=True, na=False)].copy()
    else:
        roads_main  = roads.iloc[:0].copy()
        roads_local = roads.copy()

    keep_cols = [c for c in ["highway", "name", "geometry"] if c in roads.columns]
    roads_main_out  = sample_gdf(roads_main[keep_cols],  8000)
    roads_local_out = sample_gdf(roads_local[keep_cols], 10000)

    write_geojson(roads_main_out.to_crs(4326),  LAYERS_DIR / "roads_main.geojson")
    write_geojson(roads_local_out.to_crs(4326), LAYERS_DIR / "roads_local.geojson")

    manifest["raw_layers"].append({
        "key": "roads_main",
        "label": "Main Roads",
        "kind": "lines",
        "source_path": str(ROADS_PATH.relative_to(ROOT)),
        "display_path": "./data/layers/roads_main.geojson",
        "value_column": None,
        "available": True,
        "feature_count": int(len(roads_main)),
    })
    manifest["raw_layers"].append({
        "key": "roads_local",
        "label": "Local Streets",
        "kind": "lines",
        "source_path": str(ROADS_PATH.relative_to(ROOT)),
        "display_path": "./data/layers/roads_local.geojson",
        "value_column": None,
        "available": True,
        "feature_count": int(len(roads_local)),
    })

    centroids[ROADS_METRIC["column"]] = aggregate_line_density(roads, grid_m, ROADS_METRIC["column"])
    roads_metric = dict(ROADS_METRIC)
    roads_metric.update(metric_summary(centroids[ROADS_METRIC["column"]]))
    manifest["metrics"].append(roads_metric)

    # ── Methane source attribution layers ─────────────────────────────────────
    METHANE_LAYERS = [
        {
            "key": "ch4_hotspot_grid",
            "label": "CH₄ Hotspot Grid",
            "kind": "points",
            "src": ROOT / "notebooks" / "methane" / "CH4_hotspot_grid_250m.geojson",
            "keep_cols": ["hotspot_label", "hotspot_level", "ch4_anomaly_ppb",
                          "ch4_mean_ppb", "ch4_std_ppb", "persistence_months", "geometry"],
            "max_features": 33678,
            "note": "5-month TROPOMI anomaly grid (Oct 2025–Feb 2026)",
        },
        {
            "key": "ch4_sources",
            "label": "CH₄ Source Inventory",
            "kind": "points",
            "src": ROOT / "notebooks" / "methane" / "CH4_source_inventory.geojson",
            "keep_cols": ["source_type", "name", "source", "note",
                          "nearby_anomaly_ppb", "emission_est_t_yr", "geometry"],
            "max_features": 500,
            "note": "Landfills, wastewater, industrial — OSM + literature",
        },
        {
            "key": "ch4_trajectories",
            "label": "CH₄ Back-Trajectories",
            "kind": "lines",
            "src": ROOT / "notebooks" / "methane" / "CH4_back_trajectories.geojson",
            "keep_cols": ["transport_hr", "anomaly_ppb", "geometry"],
            "max_features": 5000,   # sample — 20K is too heavy for browser
            "note": "ERA5 wind back-trajectories from persistent hotspots",
        },
    ]

    for ml in METHANE_LAYERS:
        path = ml["src"]
        entry = {
            "key": ml["key"],
            "label": ml["label"],
            "kind": ml["kind"],
            "source_path": str(path.relative_to(ROOT)) if path.exists() else None,
            "display_path": None,
            "value_column": None,
            "available": False,
            "feature_count": 0,
            "note": ml["note"],
        }
        if path.exists():
            try:
                gdf = ensure_wgs84(read_gdf(path))
                keep = [c for c in ml["keep_cols"] if c in gdf.columns or c == "geometry"]
                sampled = sample_gdf(gdf[keep], ml["max_features"])
                out_path = LAYERS_DIR / f"{ml['key']}.geojson"
                write_geojson(sampled, out_path)
                entry["display_path"] = f"./data/layers/{ml['key']}.geojson"
                entry["available"] = True
                entry["feature_count"] = int(len(gdf))
                print(f"  {ml['key']}: {len(gdf):,} → {len(sampled):,} features written")
            except Exception as exc:
                print(f"  {ml['key']}: skipped ({exc})")
        else:
            print(f"  {ml['key']}: source not found (run methane_sources.ipynb first)")
        manifest["raw_layers"].append(entry)

    index_cols = [metric["column"] for metric in manifest["metrics"] if metric["column"] in centroids.columns]
    index_gdf = centroids[["cell_id", "area_ha", "geometry"] + index_cols].copy()
    write_geojson(index_gdf, DATA_DIR / "index_grid_250m.geojson")

    with (DATA_DIR / "manifest.json").open("w") as fh:
        json.dump(manifest, fh, indent=2)

    print(f"Wrote {DATA_DIR / 'manifest.json'}")
    print(f"Wrote {DATA_DIR / 'index_grid_250m.geojson'}")


if __name__ == "__main__":
    main()
