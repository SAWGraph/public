# SAWGraph Spatial Query Demo

This is a Streamlit application that demonstrates spatial queries for the SAWGraph project, visualizing contamination data near facilities in Maine.

## Available Versions

### 1. `streamlit_app.py` - Original Full Version
- Complete implementation with all 4 query types
- Uses GROUP_CONCAT for aggregating results
- May be slow due to query complexity

### 2. `streamlit_app_optimized.py` - Optimized Version  
- Adds LIMIT clauses to queries
- Includes query limit slider (10-500 results)
- Progress indicators for better UX
- Still uses complex GROUP_CONCAT operations

### 3. `streamlit_app_simple.py` - Simplified Version (RECOMMENDED)
- Simplified queries without GROUP_CONCAT
- Faster execution times
- Basic functionality preserved
- Best for testing and demonstrations

### Debug Tools
- `streamlit_debug.py` - Query debugging interface
- `test_simple.py` - Test endpoint connectivity
- `test_endpoint.py` - Comprehensive endpoint tests

## Features

- **Q1**: Samples near landfill/DOD sites across all of Maine
- **Q2**: Samples near facilities filtered to Knox/Penobscot Counties
- **Q3**: Surface water bodies near facilities in Knox/Penobscot
- **Q4**: Surface water bodies downstream from facilities in Knox/Penobscot

## Requirements

- Python 3.8+
- All dependencies listed in `requirements.txt`

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
streamlit run streamlit_app.py
```

## Usage

1. Select a query type from the dropdown in the sidebar
2. Configure industry filters (for Q1 and Q2)
3. Click "Execute Query" to run the query and display results
4. Interact with the map and explore the data tables

## Query Modifications

The application implements the requested variable modifications:
- Substance queries now expose the substance URI as a separate variable using `?substance skos:altLabel ?substance_label`
- Type queries now expose the material type URI as a separate variable using `?type rdfs:label ?type_label`

## Notes

- The application connects to a secured SPARQL endpoint with authentication
- Query results are displayed on interactive Folium maps
- Maps include layer controls to show/hide different data types
- Data tables are available in expandable sections below the map

## Troubleshooting

If you encounter any issues with package installation, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

For issues with geospatial packages on macOS, you might need to install GDAL first:
```bash
brew install gdal
```
