import ee
try:
    import geemap
except ImportError:
    print("Warning: geemap not available, some functionality may be limited")
    geemap = None

def compute_lppi(ucs, start, end, include_osm=True, export_path="LPPI.geojson"):
    """
    Compute Land Pollution Proxy Index (LPPI) for given union councils (ucs) and date range.
    
    Params:
        ucs (ee.FeatureCollection): Area units (must have geometry).
        start (str): Start date (YYYY-MM-DD).
        end (str): End date (YYYY-MM-DD).
        include_osm (bool): Whether to add proximity boost from OSM waste sites.
        export_path (str): GeoJSON filename to export per-UC LPPI means.
    
    Returns:
        (uc_lp: ee.FeatureCollection, lppi_image: ee.Image)
    """
    
    # Conservative approach: use only the most reliable bands
    def safe_s2_processing(img):
        # Select only essential spectral bands - avoid SCL for now
        essential_bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
        return img.select(essential_bands)
    
    # Simple cloud filtering using B2 threshold instead of SCL
    def simple_cloud_mask(img):
        # Basic cloud mask using blue band threshold
        cloud_mask = img.select('B2').lt(3000)  # Typical cloud threshold
        return img.updateMask(cloud_mask)
    
    try:
        # Most conservative approach - use only Sentinel-2 L1C which has more consistent bands
        s2 = (ee.ImageCollection("COPERNICUS/S2")
                .filterDate(start, end)
                .filterBounds(ucs)
                .map(safe_s2_processing)
                .map(simple_cloud_mask)
                .median()
                .clip(ucs))
                
        print("Using Sentinel-2 L1C with basic cloud masking")
        
    except Exception as e:
        print(f"L1C failed, trying harmonized: {e}")
        # Fallback to harmonized with even more conservative selection
        s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
                .filterDate(start, end)
                .filterBounds(ucs)
                .map(safe_s2_processing)
                .median()
                .clip(ucs))

    # Indices using available bands
    ndvi = s2.normalizedDifference(['B8','B4']).rename('NDVI')
    ndbi = s2.normalizedDifference(['B11','B8']).rename('NDBI')
    
    # Simplified BSI calculation
    bsi = (s2.select('B11').add(s2.select('B4'))
             .subtract(s2.select('B8').add(s2.select('B2')))
             .divide(s2.select('B11').add(s2.select('B4'))
                     .add(s2.select('B8').add(s2.select('B2'))))
             .rename('BSI'))

    stack = ndvi.addBands([ndbi, bsi]).clip(ucs)

    # Compute statistics for Z-score normalization
    stats = stack.reduceRegion(
        reducer=ee.Reducer.mean().combine(ee.Reducer.stdDev(), sharedInputs=True),
        geometry=ucs.geometry(),
        scale=30,
        maxPixels=1e12
    )

    def z_score(name):
        mean = ee.Number(stats.get(f"{name}_mean"))
        std  = ee.Number(stats.get(f"{name}_stdDev"))
        return stack.select(name).subtract(mean).divide(std)

    ndvi_z = z_score('NDVI')
    ndbi_z = z_score('NDBI')
    bsi_z  = z_score('BSI')

    # Compute LPPI
    lppi = (bsi_z.multiply(0.4)
            .add(ndbi_z.multiply(0.4))
            .add(ndvi_z.multiply(-0.2))
            .rename('LPPI'))

    # Optional OSM waste site proximity boost
    if include_osm and geemap is not None:
        try:
            osm_waste = geemap.osm_to_ee(
                north=32.6, south=31.0, east=75.2, west=73.5,
                tags={'landuse': 'landfill', 'amenity': 'waste_disposal'}
            )
            waste_img = ee.Image().byte().paint(osm_waste, 1)
            waste_dist = waste_img.fastDistanceTransform(30, 'pixels').sqrt().multiply(30)
            waste_boost = waste_dist.multiply(-1).divide(500).exp()
            lppi = lppi.add(waste_boost.rename('WASTE_BOOST').multiply(0.2))
            print("Added OSM waste site proximity boost")
        except Exception as e:
            print(f"OSM boost failed: {e}")
    
    # Reduce regions to get per-UC values
    uc_lp = lppi.reduceRegions(collection=ucs, reducer=ee.Reducer.mean(), scale=30)

    # Export if requested
    if export_path and geemap is not None:
        try:
            geemap.ee_export_vector(uc_lp, filename=export_path)
            print(f"Exported to {export_path}")
        except Exception as e:
            print(f"Export failed: {e}")

    return uc_lp, lppi
