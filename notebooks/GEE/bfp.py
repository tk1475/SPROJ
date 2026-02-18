import ee
import geemap


def compute_building_footprint(
    ucs,
    building_min_conf=0.75,
    use_exact_intersection=False,
    export_path="UC_Buildings_OpenBuildings.geojson",
    export_geojson=False  # Set to True only if you want to try GeoJSON export
):
    """
    Compute building footprint metrics for each Union Council.
    
    Parameters
    ----------
    ucs : ee.FeatureCollection
        Union Council boundaries (must be an Earth Engine FeatureCollection)
    building_min_conf : float, default=0.75
        Minimum confidence threshold for building detection (0-1)
        Higher values = fewer false positives but may miss some buildings
    use_exact_intersection : bool, default=False
        If True, clip buildings to UC boundaries before calculating area (slower but more accurate)
        If False, use building's full area if center is within UC (faster)
    export_path : str, default="UC_Buildings_OpenBuildings.geojson"
        Path to save the output GeoJSON file
    export_geojson : bool, default=False
        If True, attempts to export GeoJSON (may timeout for large regions)
        If False, only exports CSV (recommended for large regions like Lahore)
 
   
    """
    
    print(f"🏢 Computing building footprint metrics...")
    print(f"   Confidence threshold: {building_min_conf}")
    print(f"   Exact intersection: {use_exact_intersection}")
    
    # Load Google Open Buildings v3 dataset
    # Filter by bounds and confidence threshold
    bld = (ee.FeatureCollection("GOOGLE/Research/open-buildings/v3/polygons")
             .filterBounds(ucs.geometry())
             .filter(ee.Filter.gte("confidence", building_min_conf)))
    
    # Skip the slow building count check - proceed directly to computation
    print(f"   Processing Union Councils...")
    
    def per_uc_building_metrics(feat):
        """Calculate building metrics for a single UC"""
        geom = feat.geometry()
        b = bld.filterBounds(geom)
        count = ee.Number(b.size())
        
        if use_exact_intersection:
            # Exact footprint within the UC (slower but more accurate)
            def clip_area(f):
                ia = f.geometry().intersection(geom, 1).area(1)
                return f.set({"clip_area_m2": ia})
            area_sum = ee.Number(b.map(clip_area).aggregate_sum("clip_area_m2"))
        else:
            # Fast: sum footprint areas from property
            # (counts buildings that straddle boundaries fully)
            area_sum = ee.Number(b.aggregate_sum("area_in_meters"))
        
        # Calculate derived metrics
        uc_area = geom.area(1)  # UC area in square meters
        density_per_km2 = count.divide(uc_area.divide(1e6))
        coverage_pct = area_sum.divide(uc_area).multiply(100)
        mean_area = ee.Algorithms.If(count.gt(0), area_sum.divide(count), 0)
        
        return (feat
                .set("bld_count", count)
                .set("bld_area_m2", area_sum)
                .set("bld_mean_m2", mean_area)
                .set("bld_density_km2", density_per_km2)
                .set("bld_coverage_pct", coverage_pct)
                .set("bld_conf_min", building_min_conf)
                .set("bld_exact", int(use_exact_intersection))
               )
    
    # Map the function over all UCs (computation happens server-side, very fast)
    uc_buildings = ucs.map(per_uc_building_metrics)
    
    # Export results
    if export_path:
        print(f"   Exporting results...")
        
        # ALWAYS export CSV first (faster and more reliable) - no geometries
        csv_path = export_path.replace('.geojson', '.csv')
        print(f"   Creating {csv_path}...")
        geemap.ee_export_vector(uc_buildings, filename=csv_path)
        print(f"   ✅ CSV exported: {csv_path}")
        
        # Only try GeoJSON if explicitly requested (often times out for large regions)
        if export_geojson:
            try:
                print(f"   Creating {export_path}...")
                print(f"   ⚠️  This may take 5-10 minutes or timeout for large regions...")
                geemap.ee_export_vector(
                    uc_buildings, 
                    filename=export_path,
                    timeout=600  # 10 minute timeout
                )
                print(f"   ✅ GeoJSON exported: {export_path}")
            except Exception as e:
                print(f"   ❌ GeoJSON export failed: {str(e)[:100]}")
                print(f"   💡 Run the merge cell instead to create GeoJSON from CSV + shapefile")
        else:
            print(f"   ℹ️  Skipping GeoJSON export (use export_geojson=True to enable)")
            print(f"   💡 Run the merge cell to create {export_path} from CSV + shapefile")
        
        print(f"\n✅ Building footprint analysis complete!")
        print(f"   📊 Data saved to: {csv_path}")
    
    return uc_buildings


def merge_buildings_with_uc_shapefile(
    csv_path="UC_Buildings_OpenBuildings.csv",
    uc_shapefile="../../data/Lahore UCs/Lahore UC.shp",
    output_path="UC_Buildings_OpenBuildings.geojson"
):
    """
    Merge building metrics CSV with UC shapefile for visualization.
    Use this when GeoJSON export times out.
    
    Parameters
    ----------
    csv_path : str
        Path to the CSV file with building metrics
    uc_shapefile : str
        Path to the UC shapefile with geometries
    output_path : str
        Path to save the merged GeoJSON
        
    Returns
    -------
    geopandas.GeoDataFrame
        Merged data with geometries and building metrics
    """
    import geopandas as gpd
    import pandas as pd
    
    print(f"🔗 Merging building metrics with UC boundaries...")
    
    # Load CSV with metrics
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} UCs from CSV")
    
    # Load shapefile with geometries
    gdf = gpd.read_file(uc_shapefile)
    print(f"   Loaded {len(gdf)} UC geometries from shapefile")
    
    # Ensure CRS
    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    
    # Find common join key
    join_key = "UC"
    if join_key not in df.columns or join_key not in gdf.columns:
        for alt in ["uc", "uc_name", "UC_NAME", "uc_id"]:
            if alt in df.columns and alt in gdf.columns:
                join_key = alt
                break
    
    # Merge
    merged = gdf.merge(df, on=join_key, how="left")
    print(f"   Merged {len(merged)} records")
    
    # Save
    merged.to_file(output_path, driver="GeoJSON")
    print(f"✅ Saved merged data to: {output_path}")
    
    return merged


def compute_building_footprint_stats(data_path="UC_Buildings_OpenBuildings.geojson"):
    """
    Calculate summary statistics from building footprint results.
    Works with both GeoJSON and CSV files.
    """
    import geopandas as gpd
    import pandas as pd
    from pathlib import Path
    
    # Detect file type
    if data_path.endswith('.csv'):
        df = pd.read_csv(data_path)
        gdf = pd.DataFrame(df)  # Treat as regular DataFrame
    else:
        gdf = gpd.read_file(data_path)
    
    stats = {
        'total_ucs': len(gdf),
        'total_buildings': int(gdf['bld_count'].sum()),
        'total_building_area_km2': float(gdf['bld_area_m2'].sum() / 1e6),
        'mean_coverage_pct': float(gdf['bld_coverage_pct'].mean()),
        'median_coverage_pct': float(gdf['bld_coverage_pct'].median()),
        'mean_density_km2': float(gdf['bld_density_km2'].mean()),
        'max_density_uc': gdf.loc[gdf['bld_density_km2'].idxmax(), 'UC'],
        'max_coverage_uc': gdf.loc[gdf['bld_coverage_pct'].idxmax(), 'UC'],
    }
    
    print("📊 BUILDING FOOTPRINT SUMMARY STATISTICS")
    print("=" * 50)
    print(f"Total Union Councils: {stats['total_ucs']}")
    print(f"Total Buildings: {stats['total_buildings']:,}")
    print(f"Total Building Area: {stats['total_building_area_km2']:.2f} km²")
    print(f"\nCoverage:")
    print(f"  Mean: {stats['mean_coverage_pct']:.2f}%")
    print(f"  Median: {stats['median_coverage_pct']:.2f}%")
    print(f"  Highest: {gdf['bld_coverage_pct'].max():.2f}% ({stats['max_coverage_uc']})")
    print(f"\nDensity:")
    print(f"  Mean: {stats['mean_density_km2']:.0f} buildings/km²")
    print(f"  Highest: {gdf['bld_density_km2'].max():.0f} buildings/km² ({stats['max_density_uc']})")
    
    return stats
