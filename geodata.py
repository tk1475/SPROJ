geodata# %%
import pandas as pd
import geopandas as gpd
from pathlib import Path
from dbfread import DBF
import folium


# %%

base = Path('society-maps/DHA')
dbf_path = base / 'Merged_PCT_Vectorized.dbf'
if not dbf_path.exists():
    raise FileNotFoundError(f"DBF not found: {dbf_path}")

# Load DBF attributes (no geometry)
records = list(DBF(str(dbf_path), load=True))
dha = pd.DataFrame(records)
print(f'Loaded DBF attributes only (no geometry): {dbf_path.name}')

# Quick preview
print(dha.shape)
dha.head(3)

# %%


split_base = Path("society-maps/DHA/Split_Areas")
shp_path = split_base / "DHA_AREA_split.shp"

# Read shapefile
gdf = gpd.read_file(shp_path)

# Optional: inspect the data
print(gdf.head())
print(gdf.crs)  # Check projection

# If CRS is not WGS84, convert so folium works properly
if gdf.crs and gdf.crs.to_string() != "EPSG:4326":
    gdf = gdf.to_crs(epsg=4326)

# Save to GeoJSON
geojson_path = split_base / "DHA_AREA_split.geojson"
gdf.to_file(geojson_path, driver="GeoJSON")
print(f"GeoJSON saved to: {geojson_path}")

# Create folium map centered on the data
m = folium.Map(location=[gdf.geometry.centroid.y.mean(),
                         gdf.geometry.centroid.x.mean()],
               zoom_start=14)

gdf["Name"] = gdf["id"].astype(str).map(id_mappings) if gdf["id"].astype(str).map(id_mappings).notna().any() else gdf["id"].astype(str)

# Add the GeoJSON layer
folium.GeoJson(
    gdf,
    name="DHA Areas",
    popup=folium.GeoJsonPopup(fields=["Name"], aliases=["Area ID:"])
).add_to(m)

# Add layer control
folium.LayerControl().add_to(m)

# Save map to HTML
map_path = split_base / "dha_map.html"
m.save(map_path)
print(f"Map saved to: {map_path}")


# %%
id_mappings = {
    "1": "DHA Phase 3",
    "2": "DHA Phase 2",
    "3": "DHA Phase 4",

    "4": "DHA Phase 5",

    "5": "DHA Phase 9",

    "6": "Askari 11",

    "7": "DHA Phase 7",

    "8": "DHA Phase 8",
    "9": "DHA Phase 8",
    "10": "DHA Phase 8",

    "11": "DHA Phase 7",
    "12": "DHA Phase 7"
}

# %%
df = pd.read_csv("./data/zameen_lahore_data.csv")
gdf = gpd.read_file("society-maps/DHA/Split_Areas/DHA_AREA_split.geojson")

societies = ["DHA Phase 1", "DHA Phase 2", "DHA Phase 3", "DHA Phase 4", "DHA Phase 5", "DHA Phase 6", "DHA Phase 7", "DHA Phase 8", "DHA Phase 9"]
for index, row in df.iterrows():
    for society in societies:
        if society in row['Location']:
            df.at[index, 'Society Name'] = society
import re

def parse_price(price_str):
    """
    Convert prices like '2.25 Crore', '70 Lac', '70 Lakh' into PKR (float).
    """
    if pd.isna(price_str):
        return None

    price_str = str(price_str).strip().lower()

    # Extract the numeric value
    match = re.search(r"([\d.]+)", price_str)
    if not match:
        return None

    value = float(match.group(1))

    # Decide multiplier
    if "crore" in price_str:
        return value * 10_000_00     # 1 crore = 1e7
    elif "lac" in price_str or "lakh" in price_str:
        return value * 100_000       # 1 lakh = 1e5
    else:
        return value                 # assume already in PKR

# Apply to DataFrame
df['Price'] = df['Price'].apply(parse_price)

# Now get averages
averages = df.groupby('Society Name')['Price'].mean().reset_index()

# Map polygon IDs to names
gdf["Name"] = gdf["id"].astype(str).map(id_mappings)

# Merge average prices into GeoDataFrame
gdf = gdf.merge(averages, left_on="Name", right_on="Society Name", how="left")

# Drop NA Names and keep only needed cols
gdf = gdf.dropna(subset=["Name"])
gdf = gdf[["Name", "Price", "geometry"]]  # now Price exists

# Create folium map
m = folium.Map(location=[31.4700, 74.4120], zoom_start=13, tiles="cartodbpositron")

choropleth = folium.Choropleth(
    geo_data=gdf.to_json(),
    data=gdf,
    columns=["Name", "Price"],
    key_on="feature.properties.Name",
    fill_color="YlOrRd",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Average Price (PKR)"
).add_to(m)

folium.GeoJsonTooltip(
    fields=["Name", "Price"],
    aliases=["Society", "Average Price (PKR)"],
    localize=True
).add_to(choropleth.geojson)

m.save("dha_price_heatmap.html")


