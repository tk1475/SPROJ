Senior Year Project HUDI for Lahore

Overview
- Repository for extracting and analyzing urban data for Lahore using Google Earth Engine (GEE) and OpenStreetMap (OSM).

Structure
- notebooks/
	- GEE/ — scripts to extract NDVI (vegetation), LST (land surface temperature), and NL (nighttime lights) via GEE.
	- OSM/ — scripts to extract Lahore road network data.
	- _archive/ — older notebooks kept for reference.
- data/
	- Lahore Union Council (UC) and Society-level shapefiles.
	- Other project datasets.

Requirements
- Python 3.10+
- Packages: earthengine-api, geemap, geopandas, rasterio, osmnx, pandas, numpy

Setup
- Install requirements and authenticate with GEE (earthengine authenticate).
- Place shapefiles under data/.
- Run scripts/notebooks in notebooks/GEE and notebooks/OSM.

Data inventory
- See DATA_INVENTORY.md for the key datasets, sources, and index outputs.

Naming conventions
- Use snake_case and include resolution or date when relevant (e.g., source_layer_2024_100m.geojson).
- Keep derived outputs in notebooks/ with clear suffixes (e.g., *_index_250m.csv).

Notes
- Keep all spatial data in a consistent CRS (e.g., EPSG:4326) unless noted.
- Use clear file naming: source_layer_year_extent.ext
- Commit only lightweight artifacts; store large rasters/vectors via Git LFS or external storage.

Outputs
- GEE: NDVI/LST/NL rasters and summaries for Lahore.
- OSM: cleaned road network layers and derived metrics.
- Data products aligned to UC and Society boundaries in data/.
