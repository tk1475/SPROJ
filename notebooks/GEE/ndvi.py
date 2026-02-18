import ee
import geemap
import pandas as pd

def compute_ndvi(ucs, start, end,
                    geojson_path="NDVI.geojson",
                    csv_path="NDVI.csv",
                    crs="EPSG:4326",
                    scale=10,
                    apply_reproject=False,   # default False to avoid unnecessary reprojection
                    max_cloud_pct=40):        # tweak as needed
    """
    Compute median Sentinel-2 NDVI over a collection of unit polygons (ucs) between start and end dates.
    """

    # Mask clouds & shadows using SCL (Level-2A)
    def mask_s2_sr_clouds(img):
        scl = img.select("SCL")
        # Keep everything except: cloud shadow(3), cloud(8), high prob cloud(9), thin cirrus(10), snow/ice(11)
        mask = (scl.neq(3)
                  .And(scl.neq(8))
                  .And(scl.neq(9))
                  .And(scl.neq(10))
                  .And(scl.neq(11)))
        return img.updateMask(mask).copyProperties(img, img.propertyNames())

    # Use harmonized collection to avoid deprecation
    s2 = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterDate(start, end)
        .filterBounds(ucs)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
        .map(mask_s2_sr_clouds)
        .select(["B4", "B8"])
    )

    # Compute NDVI per image, then take median NDVI
    def add_ndvi(img):
        ndvi = img.normalizedDifference(["B8", "B4"]).rename("NDVI")
        return img.addBands(ndvi)

    s2_ndvi = s2.map(add_ndvi).select("NDVI")
    ndvi_median = s2_ndvi.median()

    if apply_reproject:
        # Only do this if you have a specific reason to force CRS at the image level.
        ndvi_median = ndvi_median.reproject(crs=crs, scale=scale)

    # Summarize NDVI per polygon
    stats_fc = ndvi_median.reduceRegions(
        collection=ucs,
        reducer=ee.Reducer.mean(),
        scale=scale  # use the function argument, not a hard-coded 10
    )

    # Optional: write GeoJSON locally
    if geojson_path:
        geemap.ee_export_vector(stats_fc, filename=geojson_path)
        print(f"GeoJSON saved to {geojson_path}")


    # Pull features client-side and build DataFrame
    features = stats_fc.getInfo()["features"]
    rows = [f["properties"] for f in features]
    df = pd.DataFrame(rows)

    # Save CSV
    if csv_path:
        df.to_csv(csv_path, index=False)

    return {
        "ndvi_image": ndvi_median,
        "stats_fc": stats_fc,
        "dataframe": df
    }

# Example:
# result = compute_uc_ndvi(ucs=my_uc_feature_collection,
#                          start="2024-06-01",
#                          end="2024-08-31")
# df = result["dataframe"]
