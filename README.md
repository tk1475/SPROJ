# Lahore Real Estate Index Builder

A granular index project for Lahore and its societies, aggregating multiple datasets to provide deep insights into the property market. Currently, we are building society-level indexes using land, housing, and commercial price data from Zameen.com and Graana.com, along with population density and other relevant metrics.

## 📊 Current Data Progress

- Graana Data for Societies Lahore
- Zameen Data for Socieites Lahore
- Society Maps (in Progress)
- OSM Graph Data


### Data Fields Captured:
- **Society Name** - Lahore societies and neighborhoods
- **Property Type** - Land, House, Commercial
- **Price** - Latest prices (PKR, Lac/Crore format)
- **Population Density** - Estimated residents per area
- **Location** - Geo-coordinates and area details
- **Scraped Date** - Data collection timestamp
- **Source** - Zameen.com, Graana.com

## 🔧 Technical Stack

- **Language**: Python 3.x
- **Web Scraping**: Selenium WebDriver, Requests
- **Data Processing**: Pandas
- **Browser**: Chrome (Headless mode)
- **Storage**: CSV format

## 📁 Project Structure

```
c:\Rayn\SPROJ\
├── geo-data.ipynb                  # Process all geospatial datasets for now
├── graana_scraper.ipynb            # scrape graana fata (need to add coordinates too)
├── zameen_scraper.ipynb            # same as above but for zameen data
├── geo-data/
│   └── road-network/               # OSM scraped data (evaluate it)
│   └── lahore-boundary/            # GIS geojson of Lahore boundary
├── README.md                       # This file
└── requirements.txt                # Dependencies
```

## Stable Environment (macOS)

To avoid kernel crashes (GEOS/Shapely/PROJ mismatches) and ensure packages like OSMnx and Earth Engine work reliably, use a dedicated environment and Jupyter kernel.

- Conda (recommended):
	- `conda create -n sproj python=3.11 -y`
	- `conda activate sproj`
	- `conda install -c conda-forge geopandas shapely pyproj rtree osmnx folium -y`
	- `pip install earthengine-api`
	- `python -m ipykernel install --user --name sproj --display-name "Python (sproj)"`
	- In notebooks, select the kernel "Python (sproj)".

- venv (alternative):
	- `python3 -m venv .venv`
	- `source .venv/bin/activate`
	- `pip install --upgrade pip`
	- `pip install geopandas shapely pyproj rtree osmnx folium earthengine-api ipykernel`
	- `python -m ipykernel install --user --name sproj --display-name "Python (sproj)"`

Earth Engine setup (in the selected kernel):

```python
import ee
ee.Authenticate()
ee.Initialize()
```

Notes:
- Avoid using the system Python on macOS for geospatial stacks.
- Do not install packages inside notebook cells—install them in the environment instead.
- If OSM queries are large, start with a small subset by setting `MAX_UCS = 5` in `notebooks/osm.ipynb` parameters cell.

### 🔄 In Progress
- Enhanced society boundary mapping
- Commercial property feature extraction
- Price trend analysis by society

### 📋 Planned
- Integration with additional portals
- Real-time index updates
- Interactive dashboard for market analysis
- Investment recommendation engine


## 🔧 Dependencies

```
selenium>=4.0.0
pandas>=1.3.0
beautifulsoup4>=4.9.0
webdriver-manager>=3.8.0
requests>=2.25.0
```



**Last Updated**: August 16th, 2025  
**Status**: Active and expanding  

