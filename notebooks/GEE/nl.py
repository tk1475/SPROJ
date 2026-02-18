import pandas as pd
from pathlib import Path
import ee

try:
    import geemap
except ImportError:
    geemap = None


def compute_nl(
    ucs,
    start,
    end,
    output_basename="NL",
    primary_id="NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG",
    fallback_id="NOAA/VIIRS/DNB/MONTHLY_V1/VCMCFG",
    scale=500,
    export_geojson=True,
    export_csv=True,
    out_dir=".",
    verbose=True
):
    """
    Compute mean VIIRS nightlights over a feature collection (e.g., UCs) for a date range.

    Params:
        ucs: ee.FeatureCollection (polygons) to aggregate over. Must contain identifying properties.
        start, end: ISO date strings or ee.Date compatible.
        output_basename: Base name for output files (without extension).
        primary_id, fallback_id: VIIRS collection IDs (primary first, fallback if empty).
        scale: Reducer scale in meters.
        export_geojson, export_csv: Whether to write local files.
        out_dir: Directory to place outputs.
        verbose: Print progress.

    Returns:
        pandas.DataFrame of aggregated stats (columns = original properties + avg_rad).
    """
    if not isinstance(ucs, ee.featurecollection.FeatureCollection):
        raise TypeError("ucs must be an ee.FeatureCollection")

    # Normalize dates
    if not isinstance(start, ee.Date):
        start = ee.Date(start)
    if not isinstance(end, ee.Date):
        end = ee.Date(end)

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    def viirs_collection(col_id):
        return (ee.ImageCollection(col_id)
                .filterDate(start, end)
                .filterBounds(ucs.geometry())
                .select(["avg_rad"]))

    col = viirs_collection(primary_id)
    count = col.size().getInfo()
    if count == 0:
        col = viirs_collection(fallback_id)
        if verbose:
            print("Primary VIIRS collection empty for range; using fallback VCMCFG.")

    viirs_mean = col.mean().rename("avg_rad")

    nl_stats = viirs_mean.reduceRegions(
        collection=ucs,
        reducer=ee.Reducer.mean(),
        scale=scale
    )

    # Export GeoJSON if requested
    geojson_file = out_path / f"{output_basename}.geojson"
    if export_geojson:
        if geemap is None:
            if verbose:
                print("geemap not installed; skipping GeoJSON export. Install with 'pip install geemap'.")
        else:
            geemap.ee_export_vector(nl_stats, filename=str(geojson_file))
            if verbose:
                print(f"Wrote {geojson_file}")

    # Pull features to client
    features_info = nl_stats.getInfo()
    features = features_info.get("features", []) if features_info else []
    rows = [f.get("properties", {}) for f in features]
    df = pd.DataFrame(rows)

    # Export CSV if requested
    csv_file = out_path / f"{output_basename}.csv"
    if export_csv:
        df.to_csv(csv_file, index=False)
        if verbose:
            print(f"Wrote {csv_file}")

    if verbose:
        print("Completed UC Nightlights aggregation.")
    return df

# Example usage (comment out or remove in production):
# df_nl = compute_nl(ucs, "2024-01-01", "2024-03-31")
