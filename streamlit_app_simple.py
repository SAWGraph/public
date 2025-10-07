import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
from shapely import wkt
from SPARQLWrapper import SPARQLWrapper, JSON, GET, DIGEST
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="SAWGraph Spatial Query Demo - Simplified",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🗺️ SAWGraph Spatial Query Demo - Simplified Version")
st.markdown("Optimized queries for better performance")

# Initialize session state
if 'query_results' not in st.session_state:
    st.session_state.query_results = {}

# SPARQL endpoint configuration
@st.cache_resource
def setup_sparql_endpoint():
    """Setup SPARQL endpoint with authentication"""
    endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
    sparql = SPARQLWrapper(endpoint)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials('sawgraph-endpoint', 'skailab')
    sparql.setMethod(GET)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(30)
    return sparql

def execute_query(query_string):
    """Execute SPARQL query and return results"""
    sparql = setup_sparql_endpoint()
    sparql.setQuery(query_string)
    try:
        results = sparql.query().convert()
        
        # Convert to DataFrame
        if "results" in results and "bindings" in results["results"]:
            data = []
            for binding in results["results"]["bindings"]:
                row = {}
                for var, value in binding.items():
                    row[var] = value['value']
                data.append(row)
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.header("🔍 Query Options")
    
    query_type = st.selectbox(
        "Select Query Type",
        ["Simple: Sample Points Only",
         "Simple: Facilities Only", 
         "Simple: Sample Points near Facilities",
         "Counties: Knox and Penobscot boundaries"],
        key="query_selector"
    )
    
    st.markdown("---")
    st.subheader("⚡ Performance Options")
    
    result_limit = st.slider(
        "Result Limit",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        help="Number of results to fetch"
    )
    
    st.info("💡 These are simplified queries that run faster. Start with lower limits.")

# Query builders
def build_simple_samples_query(limit=20):
    """Get sample points with their locations"""
    return f"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?samplePoint ?spWKT ?sampleId WHERE {{
    ?samplePoint rdf:type coso:SamplePoint;
                 geo:hasGeometry/geo:asWKT ?spWKT .
    OPTIONAL {{
        ?sample coso:fromSamplePoint ?samplePoint;
                dcterms:identifier ?sampleId .
    }}
}} 
LIMIT {limit}
"""

def build_simple_facilities_query(limit=50):
    """Get facilities with their locations"""
    return f"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>

SELECT DISTINCT ?facility ?facWKT ?facilityName ?industryName WHERE {{
    SERVICE <repository:FIO> {{
        ?facility fio:ofIndustry ?industry;
                  geo:hasGeometry/geo:asWKT ?facWKT;
                  rdfs:label ?facilityName.
        ?industry rdfs:label ?industryName.
        VALUES ?industry {{naics:NAICS-562212 naics:NAICS-928110}}
    }}
}}
LIMIT {limit}
"""

def build_nearby_samples_query(limit=20):
    """Get sample points that are in S2 cells containing facilities"""
    return f"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?samplePoint ?spWKT ?sampleId WHERE {{
    # First, find S2 cells that contain facilities
    SERVICE <repository:FIO> {{
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry {{naics:NAICS-562212 naics:NAICS-928110}}
    }}
    
    SERVICE <repository:Spatial> {{
        ?s2 kwg-ont:sfContains ?facility;
            rdf:type kwg-ont:S2Cell_Level13.
    }}
    
    # Then find sample points in those S2 cells
    ?samplePoint kwg-ont:sfWithin ?s2;
                 rdf:type coso:SamplePoint;
                 geo:hasGeometry/geo:asWKT ?spWKT.
    
    OPTIONAL {{
        ?sample coso:fromSamplePoint ?samplePoint;
                dcterms:identifier ?sampleId.
    }}
}}
LIMIT {limit}
"""

def build_counties_query():
    """Get Knox and Penobscot county boundaries"""
    return """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

SELECT ?county ?countyWKT ?countyName WHERE {
    SERVICE <repository:Spatial> {
        VALUES ?county {kwgr:administrativeRegion.USA.23013 kwgr:administrativeRegion.USA.23019}
        ?county geo:hasGeometry/geo:asWKT ?countyWKT;
                rdfs:label ?countyName.
    }
}
"""

# Main execution area
if st.button("🚀 Execute Query", type="primary", use_container_width=True):
    with st.spinner("Executing query..."):
        try:
            results = {}
            
            if query_type == "Simple: Sample Points Only":
                st.info("Fetching sample points...")
                query = build_simple_samples_query(result_limit)
                df = execute_query(query)
                results['samplepoints'] = df
                results['query_type'] = 'samples_only'
                
            elif query_type == "Simple: Facilities Only":
                st.info("Fetching facilities...")
                query = build_simple_facilities_query(result_limit)
                df = execute_query(query)
                results['facilities'] = df
                results['query_type'] = 'facilities_only'
                
            elif query_type == "Simple: Sample Points near Facilities":
                st.info("Fetching sample points near facilities...")
                
                # Get sample points
                samples_query = build_nearby_samples_query(result_limit)
                samples_df = execute_query(samples_query)
                results['samplepoints'] = samples_df
                
                # Also get facilities for the map
                facilities_query = build_simple_facilities_query(50)
                facilities_df = execute_query(facilities_query)
                results['facilities'] = facilities_df
                
                results['query_type'] = 'samples_near_facilities'
                
            elif query_type == "Counties: Knox and Penobscot boundaries":
                st.info("Fetching county boundaries...")
                query = build_counties_query()
                df = execute_query(query)
                results['counties'] = df
                results['query_type'] = 'counties_only'
            
            st.session_state.query_results = results
            
            # Show success with result counts
            total_results = sum(len(df) for df in results.values() if isinstance(df, pd.DataFrame))
            st.success(f"✅ Query completed! Retrieved {total_results} results.")
            
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Display results
if st.session_state.query_results:
    results = st.session_state.query_results
    
    # Metrics
    st.markdown("### 📊 Results Summary")
    cols = st.columns(4)
    
    if 'samplepoints' in results:
        cols[0].metric("Sample Points", len(results['samplepoints']))
    if 'facilities' in results:
        cols[1].metric("Facilities", len(results['facilities']))
    if 'counties' in results:
        cols[2].metric("Counties", len(results['counties']))
    cols[3].metric("Query Type", results.get('query_type', 'N/A'))
    
    st.markdown("---")
    
    # Create map
    st.subheader("📍 Interactive Map")
    
    # Initialize map
    m = folium.Map(location=[45.2538, -69.4455], zoom_start=7)
    
    # Add sample points if available
    if 'samplepoints' in results and not results['samplepoints'].empty:
        try:
            samples_df = results['samplepoints'].copy()
            samples_df['geometry'] = samples_df['spWKT'].apply(wkt.loads)
            samples_gdf = gpd.GeoDataFrame(samples_df, geometry='geometry')
            samples_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
            
            # Add markers
            sample_group = folium.FeatureGroup(name='Sample Points')
            for idx, row in samples_gdf.iterrows():
                folium.CircleMarker(
                    location=[row.geometry.y, row.geometry.x],
                    radius=8,
                    popup=f"Sample Point<br>ID: {row.get('sampleId', 'Unknown')}",
                    color='darkblue',
                    fill=True,
                    fillOpacity=0.7
                ).add_to(sample_group)
            sample_group.add_to(m)
            
            # Zoom to samples
            bounds = samples_gdf.total_bounds
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
        except Exception as e:
            st.warning(f"Could not plot sample points: {e}")
    
    # Add facilities if available
    if 'facilities' in results and not results['facilities'].empty:
        try:
            facilities_df = results['facilities'].copy()
            facilities_df['geometry'] = facilities_df['facWKT'].apply(wkt.loads)
            facilities_gdf = gpd.GeoDataFrame(facilities_df, geometry='geometry')
            facilities_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
            
            # Add markers by industry type
            for industry_name in facilities_gdf['industryName'].unique():
                industry_group = folium.FeatureGroup(name=industry_name)
                industry_facilities = facilities_gdf[facilities_gdf['industryName'] == industry_name]
                
                color = 'red' if 'Landfill' in industry_name else 'green'
                
                for idx, row in industry_facilities.iterrows():
                    folium.Marker(
                        location=[row.geometry.y, row.geometry.x],
                        popup=f"<b>{row['facilityName']}</b><br>{row['industryName']}",
                        icon=folium.Icon(color=color, icon='info-sign')
                    ).add_to(industry_group)
                industry_group.add_to(m)
                
        except Exception as e:
            st.warning(f"Could not plot facilities: {e}")
    
    # Add counties if available
    if 'counties' in results and not results['counties'].empty:
        try:
            counties_df = results['counties'].copy()
            counties_df['geometry'] = counties_df['countyWKT'].apply(wkt.loads)
            counties_gdf = gpd.GeoDataFrame(counties_df, geometry='geometry')
            counties_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
            
            # Add county boundaries
            for idx, row in counties_gdf.iterrows():
                folium.GeoJson(
                    row.geometry,
                    name=f"County: {row['countyName']}",
                    style_function=lambda feature: {
                        'fillColor': 'lightblue',
                        'color': 'black',
                        'weight': 2,
                        'fillOpacity': 0.1
                    }
                ).add_to(m)
            
            # Zoom to counties
            bounds = counties_gdf.total_bounds
            m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
        except Exception as e:
            st.warning(f"Could not plot counties: {e}")
    
    # Add layer control if we have multiple layers
    if len([k for k in ['samplepoints', 'facilities', 'counties'] if k in results]) > 1:
        folium.LayerControl(collapsed=False).add_to(m)
    
    # Display map
    st_folium(m, height=600, width='100%', returned_objects=[])
    
    # Show data tables
    st.markdown("---")
    st.subheader("📋 Data Tables")
    
    if 'samplepoints' in results and not results['samplepoints'].empty:
        with st.expander("Sample Points Data"):
            display_df = results['samplepoints'].drop(columns=['spWKT'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)
    
    if 'facilities' in results and not results['facilities'].empty:
        with st.expander("Facilities Data"):
            display_df = results['facilities'].drop(columns=['facWKT'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)
    
    if 'counties' in results and not results['counties'].empty:
        with st.expander("Counties Data"):
            display_df = results['counties'].drop(columns=['countyWKT'], errors='ignore')
            st.dataframe(display_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🔬 **SAWGraph Spatial Query Demo - Simplified** | Optimized for performance")
