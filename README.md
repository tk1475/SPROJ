# Lahore Real Estate Index Builder

A granular index project for Lahore and its societies, aggregating multiple datasets to provide deep insights into the property market. Currently, we are building society-level indexes using land, housing, and commercial price data from Zameen.com and Graana.com, along with population density and other relevant metrics.

## 📊 Current Data Progress

| Metric | Value | Status |
|--------|-------|--------|
| **Societies Indexed** | 42 | 🏗️ In Progress |
| **Data Sources** | Zameen.com, Graana.com | 🔗 Active |
| **Target Location** | Lahore, Pakistan (Society-level) | 🎯 Focused |
| **Main Dataset** | `lahore_society_index.csv` | 📄 Available |
| **Last Updated** | July 17, 2025 | 🕐 Current |

## 🗂️ Dataset Overview

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
├── lahore_index_builder.ipynb      # Main index builder notebook
├── lahore_society_index.csv        # Society-level index dataset
├── Data/
│   └── Source Data/                # Raw datasets from portals
├── README.md                       # This file
└── requirements.txt                # Dependencies
```

## 🚀 Quick Start

### 1. Build the Index
```python
# In lahore_index_builder.ipynb
df = build_lahore_society_index(['Zameen', 'Graana'])
```

### 2. Analyze Index Data
```python
analyze_index_data(df)
```

### 3. Load Existing Index
```python
df = load_existing_index('lahore_society_index.csv')
```

## 📈 Index Statistics

| Property Type | Societies Indexed | Data Coverage |
|---------------|------------------|--------------|
| Land Prices | 42 | 100% |
| Housing Prices | 39 | 93% |
| Commercial Prices | 28 | 67% |
| Population Density | 42 | 100% |

## 🗺️ Society Distribution

| Society | Properties Indexed | Population Density |
|---------|-------------------|-------------------|
| DHA | 8 | 4,200/km² |
| Gulberg | 5 | 6,100/km² |
| Johar Town | 6 | 7,800/km² |
| Model Town | 4 | 5,900/km² |
| Cantt | 3 | 3,500/km² |
| Others | 16 | Varies |

## 💰 Price Range Analysis

| Price Range | Societies | Coverage |
|-------------|-----------|----------|
| Under 50 Lac | 18 | 43% |
| 50 Lac - 1 Crore | 14 | 33% |
| 1-2 Crore | 7 | 17% |
| Above 2 Crore | 3 | 7% |

## 🔍 Data Quality Report

| Field | Completion Rate | Data Quality |
|-------|----------------|--------------|
| Society Name | 100% | ✅ Excellent |
| Price | 92% | ✅ Very Good |
| Population Density | 100% | ✅ Excellent |
| Location | 98% | ✅ Excellent |
| Property Type | 95% | ✅ Very Good |

## 🎯 Features

### ✅ Implemented
- **Society-level Indexing** - Granular data for Lahore societies
- **Multi-source Aggregation** - Zameen and Graana integration
- **Population Density Mapping** - Adds demographic context
- **Data Validation** - Cross-source checks for accuracy
- **CSV Export** - Automatic index saving

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



**Last Updated**: July 17, 2025  
**Societies Indexed**: 42  
**Status**: Active and expanding  
**Next Update**: Planned for July 24, 2025
