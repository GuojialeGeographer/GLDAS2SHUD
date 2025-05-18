# GLDAS2SHUD - GLDAS Data Conversion Tool for SHUD Model

[![English](https://img.shields.io/badge/language-English-blue.svg)](README_EN.md)
[![中文](https://img.shields.io/badge/语言-中文-red.svg)](README.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Installation](#2-installation)
- [3. Usage Guide](#3-usage-guide)
  - [3.1 Download GLDAS Data](#31-download-gldas-data)
  - [3.2 Define Study Area](#32-define-study-area)
  - [3.3 Process Data for SHUD Format](#33-process-data-for-shud-format)
  - [3.4 Visualize Results](#34-visualize-results)
- [4. FAQ](#4-faq)
- [5. Extended Tools](#5-extended-tools)
- [6. Data Format Specifications](#6-data-format-specifications)
- [7. Command Parameters](#7-command-parameters)
- [8. Directory Structure](#8-directory-structure)
- [9. License and Citation](#9-license-and-citation)
- [10. Contact and Support](#10-contact-and-support)

## 1. Project Overview

GLDAS2SHUD is a professional toolkit designed to process GLDAS (Global Land Data Assimilation System) meteorological data and convert it to the format required by the SHUD (Simulator for Hydrologic Unstructured Domains) hydrological model. This tool can be used for hydrological research in any region globally, enabling researchers to conveniently prepare meteorological driving data.

**Main Features:**
- Download GLDAS meteorological data for any global region
- Extract meteorological data for user-defined locations
- Process and convert data to SHUD model format
- Generate data visualization charts
- Check data integrity and quality

## 2. Installation

### 2.1 Requirements

- Python 3.6+ 
- Git (optional, for cloning the repository)
- Operating System: Windows, macOS, or Linux

### 2.2 Get the Code

```bash
# Clone the repository (skip if already downloaded)
git clone https://github.com/yourusername/GLDAS2SHUD.git
cd GLDAS2SHUD
```

### 2.3 Install Dependencies

**Method 1: Using Conda (Recommended)**

```bash
# Install Anaconda or Miniconda (skip if already installed)
# Visit https://docs.conda.io/en/latest/miniconda.html to download and install

# Create and activate environment
conda env create -f environment.yml
conda activate gldas-env
```

**Method 2: Using pip**

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2.4 Verify Installation

```bash
# Check if necessary modules can be imported
python -c "import numpy; import pandas; import xarray; import matplotlib; print('Installation successful!')"
```

## 3. Usage Guide

### 3.1 Download GLDAS Data

Before downloading, you **must** register for a NASA Earthdata account:

1. Visit [NASA Earthdata Login Page](https://urs.earthdata.nasa.gov/)
2. Click "Register" to create a new account
3. After logging in, go to Applications -> Authorized Apps, click "Approve More Applications"
4. Find and add "NASA GESDISC DATA ARCHIVE" from the list

**Method 1: Using Python Script (Recommended)**

```bash
# Download GLDAS data (NASA account required)
python scripts/download_gldas.py \
    --username YOUR_NASA_USERNAME \
    --password YOUR_NASA_PASSWORD \
    --data-dir data/gldas_data \
    --start-date 20200101 \
    --end-date 20201231
```

**Method 2: Using Shell Script**

```bash
# Download data (interactive username/password input)
./bin/download_gldas.sh
```

**Download Specific Time Period**

```bash
# Use link file to download specific time period
python scripts/download_gldas.py --list-only --start-date 20220101 --end-date 20220131 > my_links.txt
python scripts/download_gldas.py --list-file my_links.txt --data-dir data/gldas_data
```

### 3.2 Define Study Area

GLDAS2SHUD supports two methods for specifying the study area:

**Method 1: Using Coordinate Point List (Simple and Direct)**

Create a text file containing coordinate points:

```bash
# Create points.txt file
cat > points.txt << EOF
# Format: longitude,latitude
# Example: The following are four points in the Hangzhou Bay area, China
120.5,30.5
121.0,30.5
120.5,30.0
121.0,30.0
EOF
```

**Method 2: Using Shapefile (Suitable for GIS Users)**

If you have your own study area shapefile, you can use it directly. The file should contain point features, each representing a meteorological data extraction location.

### 3.3 Process Data for SHUD Format

**Method 1: Using Coordinate Point File**

```bash
# Process data using coordinate point file
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points-file points.txt
```

**Method 2: Specify Coordinate Points Directly in Command Line**

```bash
# Specify point coordinates directly
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points "120.5,30.5" "121.0,30.5" "120.5,30.0" "121.0,30.0"
```

**Method 3: Using Shapefile**

```bash
# Process data using shapefile
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --shp-file data/your_study_area.shp
```

**Advanced Options: Specify Date Range**

```bash
# Specify time range, force overwrite existing files, etc.
python src/process_gldas_for_shud.py \
    --data-dir data/gldas_data \
    --output-dir output \
    --points-file points.txt \
    --start-date 20200101 \
    --end-date 20201231 \
    --force
```

### 3.4 Visualize Results

```bash
# Generate charts for all variables
python scripts/visualize_gldas.py \
    --csv-dir output/csv \
    --fig-dir output/fig \
    --all

# View precipitation data for a specific point location
python scripts/visualize_gldas.py \
    --csv-dir output/csv \
    --fig-dir output/fig \
    --point X120.5Y30.5 \
    --variable precip
```

### 3.5 Check Generated Files

```bash
# View generated files
ls -la output/
```

After processing, you should see the following directories and files:

- `output/csv/`: Contains CSV files with meteorological data for each point
- `output/fig/`: Contains generated charts
- `output/meteo.tsd.forc`: SHUD model configuration file
- `output/meteo_locations.csv`: Point location information
- `output/shud_project/`: Directory ready for use with SHUD model

### 3.6 Integration with SHUD Model

```bash
# Copy data to SHUD project
cp -r output/shud_project/* /path/to/your/SHUD_project/

# Or create symbolic links (better option)
ln -s $(pwd)/output/shud_project /path/to/your/SHUD_project/meteo
```

## 4. FAQ

### 4.1 Installation Issues

**Problem**: Installation error `ModuleNotFoundError: No module named 'xxx'`  
**Solution**: Manually install the missing package `pip install xxx` or check if the correct environment is activated

**Problem**: GDAL library installation failure  
**Solution**:
- Ubuntu: `sudo apt-get install libgdal-dev`
- macOS: `brew install gdal`
- Windows: Use pre-compiled wheels `pip install GDAL==$(gdal-config --version) --find-links=https://wheelhouse.sisyphe.calc.fr/`

### 4.2 Data Download Issues

**Problem**: NASA authorization failure  
**Solution**: Ensure you have correctly added "NASA GESDISC DATA ARCHIVE" authorization

**Problem**: Download interruption  
**Solution**: Use the resume download tool `tools/download/resume_download.sh`

**Problem**: Slow download speed  
**Solution**:
- Try downloading in a better network environment
- Use single file download tool to download in batches
- Configure proxy `export https_proxy=http://your_proxy:port`

### 4.3 Data Processing Issues

**Problem**: Coordinate points not within GLDAS range  
**Solution**: Ensure coordinates are within GLDAS coverage range: -60°S to 90°N, -180°W to 180°E

**Problem**: NC4 file reading error  
**Solution**: Check netCDF4 library version, update to latest: `pip install netCDF4 --upgrade`

**Problem**: Insufficient memory during processing  
**Solution**: Reduce the number of points processed simultaneously or increase system memory

### 4.4 Output Issues

**Problem**: CSV file format does not meet expectations  
**Solution**: Check input parameters, especially coordinate point format

**Problem**: Chart generation failure  
**Solution**: Ensure matplotlib is working properly, for remote servers use `export MATPLOTLIB_BACKEND=Agg`

## 5. Extended Tools

GLDAS2SHUD includes three sets of extended tools located in the `tools/` directory:

### 5.1 GIS Tools (`tools/gis/`)

A set of tools for processing geospatial data:

```bash
# Visualize study area
python tools/gis/visualize_shp.py data/watershed.shp output/watershed_map.png

# Calculate study area
python tools/gis/calculate_shp_area.py data/watershed.shp

# Generate hydrological station shapefile
python tools/gis/generate_hydro_stations_shp.py

# Convert format to shapefile
python tools/gis/convert_geo_to_shp.py data/map.json data/map.shp
```

### 5.2 Download Optimization Tools (`tools/download/`)

Tools to improve download efficiency and reliability:

```bash
# Download single GLDAS file (edit script to set date first)
vi tools/download/download_single_file.sh  # Modify TARGET_DATE and TARGET_TIME
./tools/download/download_single_file.sh

# Downloader with resume support
./tools/download/resume_download.sh data/links.txt data/gldas_data

# Fix download links
./tools/download/fix_links_download.sh data/bad_links.txt data/gldas_data
```

### 5.3 SHUD Integration Tools (`tools/shud/`)

Tools to help integrate with SHUD model:

```bash
# Use in R environment
R -e "source('tools/shud/Sub2.3_Forcing_LDAS.R')"
```

## 6. Data Format Specifications

### 6.1 GLDAS Original Data Format

GLDAS data is stored in NetCDF4 format and includes the following main variables:

| Variable | Description | Original Unit |
|----------|-------------|---------------|
| Rainf_tavg | Precipitation rate | kg m-2 s-1 |
| Tair_f_inst | 2m air temperature | K |
| Qair_f_inst | 2m specific humidity | kg kg-1 |
| Wind_f_inst | 10m wind speed | m s-1 |
| SWdown_f_tavg | Shortwave radiation | W m-2 |
| Psurf_f_inst | Surface pressure | Pa |

### 6.2 SHUD Model Required Format

The SHUD model requires meteorological data in the following format:

**CSV File Format**:
```
# DATE, PRECIP, TEMP, RH, WIND, SOLAR, PRESSURE
2023-01-01 00:00, 0.0, 10.5, 0.75, 2.3, 150.0, 101.3
...
```

**meteo.tsd.forc File Format**:
```
# MeteoStationID, Longitude, Latitude, TSDB_file, nx, ny
1, 120.5, 30.5, meteo/csv/X120.5Y30.5.csv, 1, 1
...
```

### 6.3 Unit Conversion

| Variable | GLDAS Unit | SHUD Unit | Conversion Method |
|----------|------------|-----------|-------------------|
| Precipitation | kg m-2 s-1 | mm/day | × 86400 |
| Temperature | K | ℃ | - 273.15 |
| Specific Humidity | kg kg-1 | Relative Humidity(0-1) | Special conversion formula |
| Wind Speed | m s-1 | m s-1 | Unchanged |
| Radiation | W m-2 | W m-2 | Unchanged |
| Pressure | Pa | kPa | ÷ 1000 |

## 7. Command Parameters

### 7.1 Download Command Parameters

```
python scripts/download_gldas.py 
  --username <USERNAME>    # NASA Earthdata username
  --password <PASSWORD>    # NASA Earthdata password
  --data-dir <DIRECTORY>   # Data save directory (default: data/gldas_data)
  --start-date <YYYYMMDD>  # Start date (default: recent)
  --end-date <YYYYMMDD>    # End date (default: one month after start-date)
  --list-file <FILENAME>   # File containing download links
  --list-only              # Generate links only without downloading
  --skip-auth              # Skip authentication (use existing .netrc file)
```

### 7.2 Processing Command Parameters

```
python src/process_gldas_for_shud.py
  --data-dir <DIRECTORY>   # GLDAS data directory
  --output-dir <DIRECTORY> # Output directory
  --points "lon1,lat1" "lon2,lat2" ... # List of coordinate points
  --points-file <FILENAME> # File containing coordinate points
  --shp-file <FILENAME>    # Shapefile containing point features
  --start-date <YYYYMMDD>  # Start processing date (default: all available data)
  --end-date <YYYYMMDD>    # End processing date (default: all available data)
  --force                  # Force overwrite existing files
```

### 7.3 Visualization Command Parameters

```
python scripts/visualize_gldas.py
  --csv-dir <DIRECTORY>    # CSV file directory
  --fig-dir <DIRECTORY>    # Image output directory
  --point <POINT_ID>       # Specify point ID to visualize (e.g., X120.5Y30.5)
  --variable <VARIABLE>    # Variable to visualize (precip/temp/rh/wind/radiation/pressure)
  --all                    # Visualize all variables
  --dpi <DPI>              # Image resolution (default: 100)
```

## 8. Directory Structure

```
GLDAS2SHUD/
├── bin/                    # Executable scripts
│   ├── check_data_integrity.sh  # Check data integrity
│   ├── download_gldas.sh        # Download data
│   ├── run_gldas.sh             # Run GLDAS processing
│   ├── run_gldas_points.sh      # Point data processing
│   └── run_process_gldas.sh     # Main processing script
├── data/                   # Data storage directory
│   └── gldas_data/         # GLDAS raw data storage
├── docs/                   # Detailed documentation
│   └── Complete_Tutorial.md     # Complete usage tutorial
├── example/                # Usage examples
│   ├── example_workflow.sh # Example workflow script
│   └── sample_points.txt   # Example coordinate points file
├── output/                 # Output results directory
│   ├── csv/                # Generated CSV files
│   ├── fig/                # Generated charts
│   └── shud_project/       # SHUD project files
├── scripts/                # Helper scripts
│   ├── download_gldas.py   # Download GLDAS data
│   ├── process_gldas.py    # Process GLDAS data
│   └── visualize_gldas.py  # Visualization tool
├── src/                    # Core source code
│   ├── extract_from_date.py      # Extract by date
│   ├── extract_points.py         # Extract point data
│   ├── gldas_to_shud.py          # GLDAS to SHUD
│   ├── process_gldas_for_shud.py # Main processing flow
│   └── visualize_gldas.py        # Visualization core
├── tools/                  # Extended toolset
│   ├── gis/                # Geographic Information System tools
│   ├── download/           # Download optimization tools
│   ├── shud/               # SHUD model integration tools
│   └── README.md           # Tool description
├── environment.yml         # Conda environment configuration
├── requirements.txt        # Python dependencies
├── Quick_Start_Guide.md    # Quick start guide
└── README.md               # This document
```

## 9. License and Citation

### 9.1 License

This project is open source under the MIT License.

### 9.2 How to Cite

If you use this tool in your research, please cite:

```
Rodell, M., et al. (2004). The Global Land Data Assimilation System. Bulletin of the American Meteorological Society, 85(3), 381-394.

Shu, L. (2020). SHUD: A Simulator for Hydrologic Unstructured Domains. Journal of Open Source Software, 5(51), 2317.
```

### 9.3 Data Source

GLDAS data is provided by NASA and distributed through GESDISC (Goddard Earth Sciences Data and Information Services Center):
https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_3H_EP_2.1/summary

## 10. Contact and Support

### 10.1 Get Help

If you encounter problems, please refer to:
- README.md (this document)
- [Complete Tutorial](docs/Complete_Tutorial.md)
- [Quick Start Guide](Quick_Start_Guide.md)

### 10.2 Report Issues

If you find bugs or have suggestions for improvements, please contact us through:
- GitHub Issues: [https://github.com/yourusername/GLDAS2SHUD/issues](https://github.com/yourusername/GLDAS2SHUD/issues)
- Email: jiale.guo@mail.polimi.it

### 10.3 Contribute Code

Pull Requests are welcome. Please ensure your code complies with project standards and includes adequate documentation. 