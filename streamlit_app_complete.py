import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
from shapely import wkt
from SPARQLWrapper import SPARQLWrapper, JSON, GET, DIGEST
import warnings
import time
from datetime import datetime
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="SAWGraph Spatial Query Demo - Debug Version",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🗺️ SAWGraph Spatial Query Demo - Debug Version")
st.markdown("With detailed execution logging")

# Initialize session state
if 'query_results' not in st.session_state:
    st.session_state.query_results = {}
if 'debug_log' not in st.session_state:
    st.session_state.debug_log = []

# Debug log display area
debug_container = st.expander("🐛 Debug Log", expanded=True)

def log_debug(message, level="INFO"):
    """Add message to debug log with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log_entry = f"[{timestamp}] {level}: {message}"
    st.session_state.debug_log.append(log_entry)
    # Update the debug display
    with debug_container:
        st.text(log_entry)
    print(log_entry)  # Also print to console

# SPARQL endpoint configuration
@st.cache_resource
def setup_sparql_endpoint():
    """Setup SPARQL endpoint with authentication"""
    log_debug("Setting up SPARQL endpoint connection...")
    endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
    sparql = SPARQLWrapper(endpoint)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials('sawgraph-endpoint', 'skailab')
    sparql.setMethod(GET)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(100030)
    log_debug("SPARQL endpoint configured successfully")
    return sparql

def execute_query(query_string, query_name="Query"):
    """Execute SPARQL query and return results with detailed logging"""
    log_debug(f"Starting execution of {query_name}")
    log_debug(f"Query length: {len(query_string)} characters")
    
    # Show first 500 chars of query for debugging
    log_debug(f"Query preview: {query_string[:500]}...")
    
    sparql = setup_sparql_endpoint()
    sparql.setQuery(query_string)
    
    try:
        # Time the query execution
        start_time = time.time()
        log_debug(f"Sending {query_name} to endpoint...")
        
        results = sparql.query()
        
        query_time = time.time() - start_time
        log_debug(f"{query_name} executed in {query_time:.2f} seconds")
        
        # Convert results
        log_debug(f"Converting {query_name} results to JSON...")
        json_results = results.convert()
        
        # Check if we got results
        if "results" in json_results and "bindings" in json_results["results"]:
            num_results = len(json_results["results"]["bindings"])
            log_debug(f"{query_name} returned {num_results} results")
            
            # Convert to DataFrame
            log_debug(f"Converting {query_name} to DataFrame...")
            data = []
            for binding in json_results["results"]["bindings"]:
                row = {}
                for var, value in binding.items():
                    row[var] = value['value']
                data.append(row)
            
            df = pd.DataFrame(data)
            log_debug(f"{query_name} DataFrame created with shape {df.shape}")
            return df
        else:
            log_debug(f"WARNING: {query_name} returned no results", "WARNING")
            return pd.DataFrame()
            
    except Exception as e:
        log_debug(f"ERROR in {query_name}: {str(e)}", "ERROR")
        log_debug(f"Error type: {type(e).__name__}", "ERROR")
        return pd.DataFrame()

# Define all options
INDUSTRY_OPTIONS = {
    "Waste Treatment and Disposal": "naics:NAICS-5622",
    "National Security": "naics:NAICS-92811", 
    "Sewage Treatment Facilities": "naics:NAICS-22132",
    "Water Supply and Irrigation": "naics:NAICS-22131",
    "Paper Product Manufacturing": "naics:NAICS-3222",
    "Plastics Product Manufacturing": "naics:NAICS-3261",
    "Textile Finishing and Coating": "naics:NAICS-3133",
    "Basic Chemical Manufacturing": "naics:NAICS-3251"
}

SAMPLE_TYPE_OPTIONS = {
    "Groundwater": "me_egad_data:sampleMaterialTypeQualifier.GW",
    "Surface Water": "me_egad_data:sampleMaterialTypeQualifier.SW",
    "Soil": "me_egad_data:sampleMaterialTypeQualifier.SL",
    "Sediment": "me_egad_data:sampleMaterialTypeQualifier.SD",
    "Vegetation": "me_egad_data:sampleMaterialTypeQualifier.V",
    "Leachate": "me_egad_data:sampleMaterialTypeQualifier.L",
    "Waste Water": "me_egad_data:sampleMaterialTypeQualifier.WW",
    "Sludge": "me_egad_data:sampleMaterialTypeQualifier.SU",
    "Process Water": "me_egad_data:sampleMaterialTypeQualifier.PW",
    "Stormwater Runoff": "me_egad_data:sampleMaterialTypeQualifier.SR",
    "Whole Fish": "me_egad_data:sampleMaterialTypeQualifier.WH",
    "Skinless Fish Fillet": "me_egad_data:sampleMaterialTypeQualifier.SF",
    "Liver": "me_egad_data:sampleMaterialTypeQualifier.LV"
}

SUBSTANCE_OPTIONS = {
    "PFOS": "me_egad_data:parameter.PFOS_A",
    "PFOA": "me_egad_data:parameter.PFOA_A",
    "PFBA": "me_egad_data:parameter.PFBA_A",
    "PFBEA": "me_egad_data:parameter.PFBEA_A",
    "PFBS": "me_egad_data:parameter.PFBS_A",
    "PFHPA": "me_egad_data:parameter.PFHPA_A",
    "PFHXS": "me_egad_data:parameter.PFHXS_A",
    "PFHXA": "me_egad_data:parameter.PFHXA_A",
    "PFHPS": "me_egad_data:parameter.PFHPS_A",
    "PFNA": "me_egad_data:parameter.PFNA_A",
    "PFDA": "me_egad_data:parameter.PFDA_A"
}

COUNTY_OPTIONS = {
    "Knox County": "kwgr:administrativeRegion.USA.23013",
    "Penobscot County": "kwgr:administrativeRegion.USA.23019",
    "All Maine": None
}

# Sidebar with all filters
with st.sidebar:
    st.header("🔍 Query Filters")
    
    # Clear debug log button
    if st.button("Clear Debug Log"):
        st.session_state.debug_log = []
        log_debug("Debug log cleared")
    
    # Administrative Region
    st.subheader("📍 Administrative Region")
    selected_county = st.selectbox(
        "Select County",
        options=list(COUNTY_OPTIONS.keys()),
        index=2,  # Default to "All Maine"
        help="Filter by county or search all of Maine"
    )
    
    # Industry Selection
    st.subheader("🏭 Facility Type")
    selected_industries = st.multiselect(
        "Select Industries",
        options=list(INDUSTRY_OPTIONS.keys()),
        default=["Waste Treatment and Disposal", "National Security"],
        help="Select one or more industry types"
    )
    
    # Sample Type
    st.subheader("🧪 Sample Type")
    selected_sample_types = st.multiselect(
        "Select Sample Types",
        options=list(SAMPLE_TYPE_OPTIONS.keys()),
        default=["Groundwater", "Surface Water"],
        help="Filter by sample material type"
    )
    
    # Chemical/Substance
    st.subheader("⚗️ Chemical Substances")
    selected_substances = st.multiselect(
        "Select Substances",
        options=list(SUBSTANCE_OPTIONS.keys()),
        default=["PFOS", "PFOA"],
        help="Filter by specific PFAS chemicals"
    )
    
    # Concentration Range
    st.subheader("📊 Concentration Range")
    col1, col2 = st.columns(2)
    with col1:
        min_concentration = st.number_input(
            "Min (ng/L)",
            min_value=0.0,
            value=4.0,
            step=0.1
        )
    with col2:
        max_concentration = st.number_input(
            "Max (ng/L)",
            min_value=0.0,
            value=1000.0,
            step=1.0
        )
    
    # Performance Options
    st.markdown("---")
    st.subheader("⚡ Performance")
    result_limit = st.slider(
        "Result Limit",
        min_value=5,
        max_value=100,
        value=25,
        step=5,
        help="Limit results for faster queries"
    )

# Query builders
def build_filtered_samples_query(
    industries, sample_types, substances, min_conc, max_conc, county, limit=25
):
    """Build query with all filters applied"""
    log_debug("Building filtered samples query...")
    
    # Log the filters being applied
    log_debug(f"Industries: {industries}")
    log_debug(f"Sample types: {sample_types}")
    log_debug(f"Substances: {substances}")
    log_debug(f"Concentration range: {min_conc} - {max_conc}")
    log_debug(f"County: {county}")
    log_debug(f"Limit: {limit}")
    
    # Build VALUES clauses
    industry_values = " ".join([INDUSTRY_OPTIONS[ind] for ind in industries]) if industries else ""
    sample_type_values = " ".join([f"<{SAMPLE_TYPE_OPTIONS[st]}>" for st in sample_types]) if sample_types else ""
    substance_values = " ".join([f"<{SUBSTANCE_OPTIONS[sub]}>" for sub in substances]) if substances else ""
    
    log_debug(f"Industry VALUES: {industry_values}")
    log_debug(f"Sample type VALUES: {sample_type_values}")
    log_debug(f"Substance VALUES: {substance_values}")
    
    # County filter
    county_filter = ""
    if county != "All Maine" and COUNTY_OPTIONS[county]:
        county_filter = f"""
        # County filter
        SERVICE <repository:Spatial> {{
            ?countySub rdf:type kwg-ont:AdministrativeRegion_3;
                       kwg-ont:administrativePartOf <{COUNTY_OPTIONS[county]}>.
        }}
        ?samplePoint kwg-ont:sfWithin ?countySub.
        """
        log_debug(f"County filter applied for: {county}")
    
    query = f"""
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX me_egad_data: <http://sawgraph.spatialai.org/v1/me-egad-data#>

SELECT DISTINCT ?samplePoint ?spWKT ?sampleId ?substance_label ?result ?unit ?type_label
WHERE {{
    # Find facilities
    SERVICE <repository:FIO> {{
        ?facility fio:ofIndustry ?industry.
        {f"VALUES ?industry {{ {industry_values} }}" if industry_values else ""}
    }}
    
    # Find S2 cells containing facilities
    SERVICE <repository:Spatial> {{
        ?s2 kwg-ont:sfContains ?facility;
            rdf:type kwg-ont:S2Cell_Level13.
    }}
    
    # Find sample points in those S2 cells
    ?samplePoint kwg-ont:sfWithin ?s2;
                 rdf:type coso:SamplePoint;
                 geo:hasGeometry/geo:asWKT ?spWKT.
    
    {county_filter}
    
    # Get sample details
    ?sample coso:fromSamplePoint ?samplePoint;
            dcterms:identifier ?sampleId;
            coso:sampleOfMaterialType ?type.
    ?type rdfs:label ?type_label.
    {f"VALUES ?type {{ {sample_type_values} }}" if sample_type_values else ""}
    
    # Get observations
    ?observation rdf:type coso:ContaminantObservation;
                 coso:observedAtSamplePoint ?samplePoint;
                 coso:ofSubstance ?substance;
                 coso:hasResult/coso:measurementValue ?result;
                 coso:hasResult/coso:measurementUnit/qudt:symbol ?unit.
    ?substance skos:altLabel ?substance_label.
    {f"VALUES ?substance {{ {substance_values} }}" if substance_values else ""}
    
    # Concentration filter
    FILTER(?result >= {min_conc} && ?result <= {max_conc})
}}
LIMIT {limit}
"""
    log_debug("Filtered samples query built successfully")
    return query

def build_facilities_query(industries, county, limit=100):
    """Build facilities query with filters"""
    log_debug("Building facilities query...")
    log_debug(f"Industries for facilities: {industries}")
    log_debug(f"County for facilities: {county}")
    
    industry_values = " ".join([INDUSTRY_OPTIONS[ind] for ind in industries]) if industries else ""
    
    # County filter for facilities
    county_filter = ""
    if county != "All Maine" and COUNTY_OPTIONS[county]:
        county_filter = f"""
        SERVICE <repository:Spatial> {{
            ?s2 kwg-ont:sfContains ?facility;
                rdf:type kwg-ont:S2Cell_Level13.
            ?countySub rdf:type kwg-ont:AdministrativeRegion_3;
                       kwg-ont:administrativePartOf <{COUNTY_OPTIONS[county]}>;
                       kwg-ont:sfOverlaps ?s2.
        }}
        """
        log_debug(f"Facilities county filter applied")
    
    query = f"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?facility ?facWKT ?facilityName ?industryName WHERE {{
    SERVICE <repository:FIO> {{
        ?facility fio:ofIndustry ?industry;
                  geo:hasGeometry/geo:asWKT ?facWKT;
                  rdfs:label ?facilityName.
        ?industry rdfs:label ?industryName.
        {f"VALUES ?industry {{ {industry_values} }}" if industry_values else ""}
    }}
    {county_filter}
}}
LIMIT {limit}
"""
    log_debug("Facilities query built successfully")
    return query

def build_county_query(county):
    """Get county boundaries"""
    log_debug(f"Building county query for: {county}")
    
    if county == "All Maine" or not COUNTY_OPTIONS[county]:
        # Return all Maine counties
        log_debug("Building query for all Maine counties")
        return """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?county ?countyWKT ?countyName WHERE {
    SERVICE <repository:Spatial> {
        ?county rdf:type kwg-ont:AdministrativeRegion_2;
                kwg-ont:administrativePartOf kwgr:administrativeRegion.USA.ME;
                geo:hasGeometry/geo:asWKT ?countyWKT;
                rdfs:label ?countyName.
    }
} LIMIT 20
"""
    else:
        log_debug(f"Building query for specific county: {county}")
        return f"""
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>

SELECT ?county ?countyWKT ?countyName WHERE {{
    SERVICE <repository:Spatial> {{
        VALUES ?county {{<{COUNTY_OPTIONS[county]}>}}
        ?county geo:hasGeometry/geo:asWKT ?countyWKT;
                rdfs:label ?countyName.
    }}
}}
"""

# Main execution
if st.button("🚀 Execute Query", type="primary", use_container_width=True):
    if not selected_industries:
        st.error("Please select at least one industry type")
        log_debug("ERROR: No industries selected", "ERROR")
    else:
        # Clear previous debug log for this execution
        st.session_state.debug_log = []
        log_debug("="*50)
        log_debug("STARTING NEW QUERY EXECUTION")
        log_debug("="*50)
        
        with st.spinner("Executing queries..."):
            try:
                overall_start = time.time()
                progress_bar = st.progress(0)
                status = st.empty()
                
                results = {}
                
                # Query 1: Filtered samples
                status.text("Building filtered samples query...")
                log_debug("QUERY 1: Filtered Samples")
                log_debug("-"*30)
                progress_bar.progress(10)
                
                samples_query = build_filtered_samples_query(
                    selected_industries,
                    selected_sample_types,
                    selected_substances,
                    min_concentration,
                    max_concentration,
                    selected_county,
                    result_limit
                )
                
                status.text("Executing filtered samples query...")
                progress_bar.progress(20)
                samples_df = execute_query(samples_query, "Samples Query")
                results['samples'] = samples_df
                progress_bar.progress(35)
                
                # Query 2: Facilities
                status.text("Building facilities query...")
                log_debug("QUERY 2: Facilities")
                log_debug("-"*30)
                progress_bar.progress(40)
                
                facilities_query = build_facilities_query(
                    selected_industries,
                    selected_county,
                    100
                )
                
                status.text("Executing facilities query...")
                progress_bar.progress(50)
                facilities_df = execute_query(facilities_query, "Facilities Query")
                results['facilities'] = facilities_df
                progress_bar.progress(65)
                
                # Query 3: County boundaries (if needed)
                if selected_county != "All Maine":
                    status.text("Building county boundaries query...")
                    log_debug("QUERY 3: County Boundaries")
                    log_debug("-"*30)
                    progress_bar.progress(70)
                    
                    county_query = build_county_query(selected_county)
                    
                    status.text("Executing county boundaries query...")
                    progress_bar.progress(75)
                    counties_df = execute_query(county_query, "Counties Query")
                    results['counties'] = counties_df
                    progress_bar.progress(90)
                
                progress_bar.progress(100)
                status.empty()
                progress_bar.empty()
                
                # Store results
                st.session_state.query_results = results
                
                # Summary
                total_time = time.time() - overall_start
                total_samples = len(samples_df)
                total_facilities = len(facilities_df)
                
                log_debug("="*50)
                log_debug(f"EXECUTION COMPLETE in {total_time:.2f} seconds")
                log_debug(f"Total samples: {total_samples}")
                log_debug(f"Total facilities: {total_facilities}")
                log_debug("="*50)
                
                st.success(f"✅ Query completed in {total_time:.1f}s! Found {total_samples} sample results and {total_facilities} facilities.")
                
                # Show applied filters
                with st.expander("Applied Filters"):
                    st.write(f"**County:** {selected_county}")
                    st.write(f"**Industries:** {', '.join(selected_industries)}")
                    st.write(f"**Sample Types:** {', '.join(selected_sample_types)}")
                    st.write(f"**Substances:** {', '.join(selected_substances)}")
                    st.write(f"**Concentration Range:** {min_concentration} - {max_concentration} ng/L")
                
            except Exception as e:
                progress_bar.empty()
                status.empty()
                log_debug(f"FATAL ERROR: {str(e)}", "ERROR")
                st.error(f"Error: {str(e)}")
                st.info("Try reducing the result limit or selecting fewer filters")

# Display results (rest of the code remains the same)
if st.session_state.query_results:
    results = st.session_state.query_results
    
    # Metrics
    st.markdown("### 📊 Results Summary")
    cols = st.columns(4)
    
    if 'samples' in results:
        # Count unique sample points
        unique_samples = results['samples']['samplePoint'].nunique() if not results['samples'].empty else 0
        cols[0].metric("Sample Points", unique_samples)
        cols[1].metric("Total Observations", len(results['samples']))
    
    if 'facilities' in results:
        cols[2].metric("Facilities", len(results['facilities']))
    
    if 'counties' in results:
        cols[3].metric("Counties", len(results['counties']))
    
    st.markdown("---")
    
    # Create map (mapping code remains unchanged)
    st.subheader("📍 Interactive Map")
    
    # Initialize map
    if selected_county != "All Maine":
        m = folium.Map(location=[44.5, -69.0], zoom_start=8)
    else:
        m = folium.Map(location=[45.2538, -69.4455], zoom_start=7)
    
    # (Rest of the mapping code remains the same as original...)
    
# Footer
st.markdown("---")
st.markdown("🔬 **SAWGraph Spatial Query Demo** | Debug version with execution logging")