#!/usr/bin/env python3
"""
plot_dha_map.py

Builds an interactive Folium map from all available vector layers under
society-maps (SHP, GPKG, GeoJSON). Saves to society-maps/full_map.html.

- Automatically discovers layers recursively (DHA, Private Schemes, etc.).
- Reprojects to WGS84 (EPSG:4326) for web mapping.
- Adds each layer with a distinct color and a tooltip for key attributes.
- Includes a layer control and centers/zooms to the data extent.

Requirements:
    pip install geopandas folium fiona

Usage:
    python plot_dha_map.py
"""
from __future__ import annotations

import sys
import logging
from pathlib import Path
from typing import List, Tuple

import geopandas as gpd
import pandas as pd

# Folium is optional at import time; we'll fail fast with guidance if missing
try:
    import folium
except Exception as e:
    print("Folium is required. Install with: pip install folium")
    raise

try:
    import fiona
except Exception:
    print("Fiona is recommended for listing GPKG layers. Install with: pip install fiona")

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# Colors to cycle through for layers
PALETTE = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

VECTOR_EXTS = {".shp", ".geojson", ".json", ".gpkg"}


def find_vector_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for p in root.rglob('*'):
        if p.is_file() and p.suffix.lower() in VECTOR_EXTS:
            files.append(p)
    return files


def list_gpkg_layers(gpkg_path: Path) -> List[str]:
    try:
        import fiona
        return list(fiona.listlayers(str(gpkg_path)))
    except Exception as e:
        logging.warning(f"Could not list GPKG layers for {gpkg_path.name}: {e}")
        return []


def read_layer(path: Path) -> List[Tuple[str, gpd.GeoDataFrame]]:
    """Return a list of (layer_name, GeoDataFrame) from a file path.
    For GPKG, returns one entry per layer. For SHP/GeoJSON, returns a single entry.
    """
    layers: List[Tuple[str, gpd.GeoDataFrame]] = []
    suffix = path.suffix.lower()
    if suffix == ".gpkg":
        layer_names = list_gpkg_layers(path) or [None]
        for lname in layer_names:
            try:
                gdf = gpd.read_file(path, layer=lname) if lname else gpd.read_file(path)
                if len(gdf) == 0:
                    continue
                layers.append((f"{path.stem}:{lname}" if lname else path.stem, gdf))
            except Exception as e:
                logging.warning(f"Failed reading layer '{lname}' from {path.name}: {e}")
    else:
        try:
            gdf = gpd.read_file(path)
            if len(gdf) > 0:
                layers.append((path.stem, gdf))
        except Exception as e:
            logging.warning(f"Failed reading {path.name}: {e}")
    return layers


def to_wgs84(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    try:
        if gdf.crs is None:
            return gdf  # assume already lon/lat or unknown; avoid crashing
        if str(gdf.crs).upper() != "EPSG:4326":
            return gdf.to_crs(epsg=4326)
        return gdf
    except Exception as e:
        logging.warning(f"CRS transform warning: {e}")
        return gdf


def bounds_union(b1, b2):
    if b1 is None:
        return b2
    if b2 is None:
        return b1
    minx = min(b1[0], b2[0])
    miny = min(b1[1], b2[1])
    maxx = max(b1[2], b2[2])
    maxy = max(b1[3], b2[3])
    return (minx, miny, maxx, maxy)


def add_geojson_layer(m: folium.Map, gdf: gpd.GeoDataFrame, name: str, color: str):
    # Sanitize properties to ensure JSON serializable (convert datetimes, periods, categories, objects)
    from pandas.api.types import (
        is_datetime64_any_dtype,
        is_timedelta64_dtype,
        is_period_dtype,
        is_categorical_dtype,
    )

    gdf_sanitized = gdf.copy()
    for col in gdf_sanitized.columns:
        if col == 'geometry':
            continue
        s = gdf_sanitized[col]
        try:
            if is_datetime64_any_dtype(s):
                gdf_sanitized[col] = s.dt.strftime('%Y-%m-%d %H:%M:%S').fillna('')
            elif is_timedelta64_dtype(s):
                gdf_sanitized[col] = s.astype(str)
            elif is_period_dtype(s) or is_categorical_dtype(s):
                gdf_sanitized[col] = s.astype(str)
            elif s.dtype == 'object':
                # Convert non-serializable objects to string, preserve basic types
                def _to_jsonable(v):
                    if isinstance(v, (str, int, float, bool)) or v is None:
                        return v
                    if isinstance(v, (pd.Timestamp,)):
                        return v.isoformat()
                    try:
                        # numpy scalar
                        return v.item()
                    except Exception:
                        return str(v)
                gdf_sanitized[col] = s.apply(_to_jsonable)
        except Exception:
            gdf_sanitized[col] = s.astype(str)

    # Limit columns in tooltip for readability
    non_geom_cols = [c for c in gdf_sanitized.columns if c != 'geometry'][:10]
    try:
        gj = folium.GeoJson(
            data=gdf_sanitized.__geo_interface__,
            name=name,
            style_function=lambda f: {"color": color, "weight": 1, "fillOpacity": 0.2},
            tooltip=folium.features.GeoJsonTooltip(fields=non_geom_cols) if non_geom_cols else None,
            control=True,
            show=True,
        )
        gj.add_to(m)
    except Exception as e:
        logging.warning(f"Skipping layer '{name}' due to serialization error: {e}")


def main():
    project_root = Path(__file__).resolve().parent
    maps_root = project_root / "society-maps"
    out_html = maps_root / "full_map.html"

    if not maps_root.exists():
        logging.error(f"Folder not found: {maps_root}")
        sys.exit(1)

    logging.info(f"Scanning for vector layers under: {maps_root}")
    vector_files = find_vector_files(maps_root)

    # Prefer DHA/Split_Areas layers first if present
    split_areas = [p for p in vector_files if 'split_areas' in p.parent.as_posix().lower()]
    other_files = [p for p in vector_files if p not in split_areas]
    ordered_files = split_areas + other_files

    if not ordered_files:
        logging.warning("No vector files (SHP/GPKG/GeoJSON) found. Output will be a base map only.")

    # Read layers
    layers: List[Tuple[str, gpd.GeoDataFrame]] = []
    for path in ordered_files:
        for name, gdf in read_layer(path):
            if gdf is None or gdf.empty:
                continue
            gdf = to_wgs84(gdf)
            layers.append((name, gdf))
            logging.info(f"Loaded layer: {name} ({len(gdf)} features) from {path.name}")

    # Build map
    # Default center: Lahore
    center = (31.5204, 74.3587)
    data_bounds = None
    for _, gdf in layers:
        try:
            b = gdf.total_bounds  # (minx, miny, maxx, maxy)
            if all(x is not None for x in b):
                data_bounds = bounds_union(data_bounds, b)
        except Exception:
            pass

    if data_bounds:
        minx, miny, maxx, maxy = data_bounds
        center = ((miny + maxy) / 2.0, (minx + maxx) / 2.0)

    m = folium.Map(location=center, zoom_start=12, tiles="cartodbpositron")

    # Add layers with styling and controls
    for idx, (name, gdf) in enumerate(layers):
        color = PALETTE[idx % len(PALETTE)]
        add_geojson_layer(m, gdf, name=name, color=color)

    folium.LayerControl(collapsed=False).add_to(m)

    m.save(str(out_html))
    logging.info(f"Map saved to: {out_html}")
    print(out_html)


if __name__ == "__main__":
    main()
