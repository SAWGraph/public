import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import pandas as pd
from shapely import wkt
from SPARQLWrapper import SPARQLWrapper2, JSON, GET, DIGEST
import rdflib
from branca.element import Figure
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="SAWGraph Spatial Query Demo",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🗺️ SAWGraph Spatial Query Demo")
st.markdown("Interactive visualization of contamination data near facilities in Maine")

# Initialize session state
if 'query_results' not in st.session_state:
    st.session_state.query_results = {}
if 'last_query' not in st.session_state:
    st.session_state.last_query = None

# SPARQL endpoint configuration
@st.cache_resource
def setup_sparql_endpoint():
    """Setup SPARQL endpoint with authentication"""
    endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
    sparql = SPARQLWrapper2(endpoint)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials('sawgraph-endpoint', 'skailab')
    sparql.setMethod(GET)
    sparql.setReturnFormat(JSON)
    return sparql

# Helper functions
def convertToDataframe(results):
    """Convert SPARQL results to pandas DataFrame"""
    d = []
    for x in results.bindings:
        row = {}
        for k in x:
            v = x[k]
            vv = rdflib.term.Literal(v.value, datatype=v.datatype).toPython()
            row[k] = vv
        d.append(row)
    df = pd.DataFrame(d)
    return df

def execute_query(query_string):
    """Execute SPARQL query"""
    sparql = setup_sparql_endpoint()
    sparql.setQuery(query_string)
    try:
        result = sparql.query()
        df = convertToDataframe(result)
        return df
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return pd.DataFrame()

def truncate_results(results_str):
    """Truncate long result strings for display"""
    if pd.isna(results_str):
        return ""
    results_list = results_str.split('<br>')
    if len(results_list) > 16:
        return "<br>".join(results_list[0:20]) + "<br> ... "
    return results_str

# Sidebar with filters
with st.sidebar:
    st.header("🔍 Query Options")
    
    # Query selection
    query_type = st.selectbox(
        "Select Query Type",
        ["Q1: Samples near landfill/DOD sites (All Maine)",
         "Q2: Samples near facilities (Knox/Penobscot Counties)",
         "Q3: Surface water near facilities (Knox/Penobscot)",
         "Q4: Downstream surface water (Knox/Penobscot)"],
        key="query_selector"
    )
    
    st.markdown("---")
    
    # Common filters
    st.subheader("🏭 Industry Selection")
    
    # For Q1 and Q2, show all industry options
    if query_type.startswith("Q1") or query_type.startswith("Q2"):
        industry_options = {
            "Solid Waste Landfill": "naics:NAICS-562212",
            "National Security": "naics:NAICS-928110"
        }
        
        selected_industries = st.multiselect(
            "Select Industries",
            options=list(industry_options.keys()),
            default=list(industry_options.keys()),
            key="industry_filter"
        )
    else:
        # For Q3 and Q4, use the same default industries
        selected_industries = ["Solid Waste Landfill", "National Security"]
        industry_options = {
            "Solid Waste Landfill": "naics:NAICS-562212",
            "National Security": "naics:NAICS-928110"
        }

# Query builders
def build_q1_query():
    """Build Q1 query - modified with new variable handling"""
    industry_values = " ".join([industry_options[ind] for ind in selected_industries])
    
    query = f'''
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX spatial: <http://purl.org/spatialai/spatial/spatial-full#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?samplePoint ?spWKT ?sample 
    (GROUP_CONCAT(DISTINCT ?sampleId; separator="; ") as ?samples) 
    (COUNT(DISTINCT ?subVal) as ?resultCount) 
    (MAX(?result) as ?Max) ?unit 
    (GROUP_CONCAT(DISTINCT ?subVal; separator=" <br> ") as ?results)
WHERE {{
    SERVICE <repository:FIO>{{
        ?s2neighbor kwg-ont:sfContains ?facility.
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry {{ {industry_values} }}.
    }}
    SERVICE <repository:Spatial>{{
        ?s2 kwg-ont:sfTouches|owl:sameAs ?s2neighbor.
        ?s2neighbor rdf:type kwg-ont:S2Cell_Level13.
    }}
    
    ?samplePoint kwg-ont:sfWithin ?s2;
        rdf:type coso:SamplePoint;
        geo:hasGeometry/geo:asWKT ?spWKT.
    ?s2 rdf:type kwg-ont:S2Cell_Level13.
    
    ?sample coso:fromSamplePoint ?samplePoint;
        dcterms:identifier ?sampleId;
        coso:sampleOfMaterialType ?type.
    ?type rdfs:label ?type_label.
    
    ?observation rdf:type coso:ContaminantObservation;
        coso:observedAtSamplePoint ?samplePoint;
        coso:ofSubstance ?substance;
        coso:hasResult/coso:measurementValue ?result;
        coso:hasResult/coso:measurementUnit/qudt:symbol ?unit.
    ?substance skos:altLabel ?substance_label.
    
    BIND((CONCAT(?substance_label, ": ", str(?result) , " ", ?unit) ) as ?subVal)
}} 
GROUP BY ?samplePoint ?spWKT ?sample ?unit
'''
    return query

def build_q2_query():
    """Build Q2 query - Knox/Penobscot counties"""
    industry_values = " ".join([industry_options[ind] for ind in selected_industries])
    
    query = f'''
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX qudt: <http://qudt.org/schema/qudt/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX spatial: <http://purl.org/spatialai/spatial/spatial-full#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT DISTINCT ?samplePoint ?spWKT ?sample 
    (GROUP_CONCAT(DISTINCT ?sampleId; separator="; ") as ?samples) 
    (COUNT(DISTINCT ?subVal) as ?resultCount) 
    (MAX(?result) as ?Max) ?unit 
    (GROUP_CONCAT(DISTINCT ?subVal; separator=" <br> ") as ?results)
WHERE {{
    SERVICE <repository:FIO>{{
        ?s2neighbor kwg-ont:sfContains ?facility.
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry {{ {industry_values} }}.
    }}
    SERVICE <repository:Spatial>{{
        ?s2 kwg-ont:sfTouches|owl:sameAs ?s2neighbor.
        ?s2neighbor rdf:type kwg-ont:S2Cell_Level13.
        ?countySub rdf:type kwg-ont:AdministrativeRegion_3;
            kwg-ont:administrativePartOf ?county.
        VALUES ?county {{kwgr:administrativeRegion.USA.23013 kwgr:administrativeRegion.USA.23019}}
    }}
    
    ?samplePoint kwg-ont:sfWithin ?s2;
        kwg-ont:sfWithin ?countySub;
        rdf:type coso:SamplePoint;
        geo:hasGeometry/geo:asWKT ?spWKT.
    ?s2 rdf:type kwg-ont:S2Cell_Level13.
    
    ?sample coso:fromSamplePoint ?samplePoint;
        dcterms:identifier ?sampleId;
        coso:sampleOfMaterialType ?type.
    ?type rdfs:label ?type_label.
    
    ?observation rdf:type coso:ContaminantObservation;
        coso:observedAtSamplePoint ?samplePoint;
        coso:ofSubstance ?substance;
        coso:hasResult/coso:measurementValue ?result;
        coso:hasResult/coso:measurementUnit/qudt:symbol ?unit.
    ?substance skos:altLabel ?substance_label.
    
    BIND((CONCAT(?substance_label, ": ", str(?result) , " ", ?unit) ) as ?subVal)
}} 
GROUP BY ?samplePoint ?spWKT ?sample ?unit
'''
    return query

def build_q3_query():
    """Build Q3 query - Surface water near facilities"""
    industry_values = " ".join([industry_options[ind] for ind in selected_industries])
    
    query = f'''
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX spatial: <http://purl.org/spatialai/spatial/spatial-full#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX hyf: <https://www.opengis.net/def/schema/hy_features/hyf/>
PREFIX nhdplusv2: <http://nhdplusv2.spatialai.org/v1/nhdplusv2#>
PREFIX hyfo: <http://hyfo.spatialai.org/v1/hyfo#>

SELECT DISTINCT ?surfacewater ?surfacewatername ?waterType ?swWKT ?reachCode ?COMID
WHERE {{
    SERVICE <repository:FIO>{{
        ?s2neighbor kwg-ont:sfContains ?facility.
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry {{ {industry_values} }}.
    }}
    SERVICE <repository:Spatial>{{
        ?s2 kwg-ont:sfTouches|owl:sameAs ?s2neighbor.
        ?s2neighbor rdf:type kwg-ont:S2Cell_Level13;
            spatial:connectedTo ?countySub.
        ?countySub rdf:type kwg-ont:AdministrativeRegion_3;
            kwg-ont:administrativePartOf ?county.
        VALUES ?county {{kwgr:administrativeRegion.USA.23013 kwgr:administrativeRegion.USA.23019}}
    }}
    SERVICE <repository:Hydrology>{{
        ?surfacewater rdf:type ?watertype;
            spatial:connectedTo ?s2neighbor;
            geo:hasGeometry/ geo:asWKT ?swWKT.
        OPTIONAL {{
            ?surfacewater rdfs:label ?surfacewatername;
                nhdplusv2:hasFTYPE ?waterType;
                nhdplusv2:hasCOMID ?COMID;
                nhdplusv2:hasReachCode ?reachCode.
        }}
        VALUES ?watertype {{hyf:HY_HydroFeature hyfo:WaterFeatureRepresentation}}
    }}
}}
'''
    return query

def build_q4_query():
    """Build Q4 query - Downstream surface water"""
    industry_values = " ".join([industry_options[ind] for ind in selected_industries])
    
    query = f'''
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX spatial: <http://purl.org/spatialai/spatial/spatial-full#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX hyf: <https://www.opengis.net/def/schema/hy_features/hyf/>
PREFIX nhdplusv2: <http://nhdplusv2.spatialai.org/v1/nhdplusv2#>
PREFIX hyfo: <http://hyfo.spatialai.org/v1/hyfo#>

SELECT DISTINCT ?surfacewater ?surfacewatername ?waterType ?swWKT ?reachCode ?COMID
WHERE {{
    SERVICE <repository:FIO>{{
        ?s2neighbor kwg-ont:sfContains ?facility.
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry {{ {industry_values} }}.
    }}
    SERVICE <repository:Spatial>{{
        ?s2 kwg-ont:sfTouches|owl:sameAs ?s2neighbor.
        ?s2neighbor rdf:type kwg-ont:S2Cell_Level13;
            spatial:connectedTo ?countySub.
        ?countySub rdf:type kwg-ont:AdministrativeRegion_3;
            kwg-ont:administrativePartOf ?county.
        VALUES ?county {{kwgr:administrativeRegion.USA.23013 kwgr:administrativeRegion.USA.23019}}
    }}
    SERVICE <repository:Hydrology>{{
        ?stream rdf:type hyfo:WaterFeatureRepresentation;
            spatial:connectedTo ?s2neighbor;
            hyf:downstreamWaterBody+ ?surfacewater.
        ?surfacewater geo:hasGeometry/ geo:asWKT ?swWKT.
        OPTIONAL {{
            ?surfacewater rdfs:label ?surfacewatername;
                nhdplusv2:hasFTYPE ?waterType;
                nhdplusv2:hasCOMID ?COMID;
                nhdplusv2:hasReachCode ?reachCode.
        }}
    }}
}}
'''
    return query

def build_facilities_query():
    """Build facilities query"""
    industry_values = " ".join([industry_options[ind] for ind in selected_industries])
    
    query = f'''
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>

SELECT DISTINCT ?facility ?facWKT ?facilityName ?industry ?industryName WHERE {{
    SERVICE <repository:FIO>{{
        ?facility fio:ofIndustry ?industry;
                geo:hasGeometry/geo:asWKT ?facWKT;
                rdfs:label ?facilityName.
        ?industry rdfs:label ?industryName.
        VALUES ?industry {{ {industry_values} }}.
    }}
}}
'''
    return query

def build_counties_query():
    """Build counties query for Knox and Penobscot"""
    query = '''
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT * WHERE {
    SERVICE <repository:Spatial>{
        VALUES ?county {kwgr:administrativeRegion.USA.23013 kwgr:administrativeRegion.USA.23019}
        ?county geo:hasGeometry/geo:asWKT ?countyWKT;
                rdfs:label ?countyName.
    }
}
'''
    return query

# Main content area
if st.button("🚀 Execute Query", type="primary", use_container_width=True):
    with st.spinner("Executing queries..."):
        try:
            # Execute appropriate queries based on selection
            if query_type.startswith("Q1"):
                # Q1: All Maine samples
                st.info("Executing Q1: Samples near facilities across all of Maine...")
                q1 = build_q1_query()
                samplepoints = execute_query(q1)
                
                # Execute facilities query
                q2 = build_facilities_query()
                facilities = execute_query(q2)
                
                st.session_state.query_results = {
                    'samplepoints': samplepoints,
                    'facilities': facilities,
                    'query_type': 'Q1'
                }
                st.session_state.last_query = query_type
                
            elif query_type.startswith("Q2"):
                # Q2: Knox/Penobscot samples
                st.info("Executing Q2: Samples in Knox/Penobscot counties...")
                q1 = build_q2_query()
                samplepoints = execute_query(q1)
                
                q2 = build_facilities_query()
                facilities = execute_query(q2)
                
                q3 = build_counties_query()
                counties = execute_query(q3)
                
                st.session_state.query_results = {
                    'samplepoints': samplepoints,
                    'facilities': facilities,
                    'counties': counties,
                    'query_type': 'Q2'
                }
                st.session_state.last_query = query_type
                
            elif query_type.startswith("Q3"):
                # Q3: Surface water near facilities
                st.info("Executing Q3: Surface water near facilities...")
                q1 = build_q3_query()
                surfacewater = execute_query(q1)
                
                q2 = build_facilities_query()
                facilities = execute_query(q2)
                
                q3 = build_counties_query()
                counties = execute_query(q3)
                
                st.session_state.query_results = {
                    'surfacewater': surfacewater,
                    'facilities': facilities,
                    'counties': counties,
                    'query_type': 'Q3'
                }
                st.session_state.last_query = query_type
                
            elif query_type.startswith("Q4"):
                # Q4: Downstream surface water
                st.info("Executing Q4: Downstream surface water...")
                q1 = build_q4_query()
                surfacewater = execute_query(q1)
                
                q2 = build_facilities_query()
                facilities = execute_query(q2)
                
                q3 = build_counties_query()
                counties = execute_query(q3)
                
                st.session_state.query_results = {
                    'surfacewater': surfacewater,
                    'facilities': facilities,
                    'counties': counties,
                    'query_type': 'Q4'
                }
                st.session_state.last_query = query_type
                
            st.success("Query executed successfully!")
            
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")

# Display results
if 'query_results' in st.session_state and st.session_state.query_results:
    results = st.session_state.query_results
    
    # Display metrics
    st.markdown("### 📊 Query Results")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if 'samplepoints' in results:
            st.metric("Sample Points", len(results['samplepoints']))
        elif 'surfacewater' in results:
            st.metric("Water Bodies", len(results['surfacewater']))
    with col2:
        st.metric("Facilities", len(results.get('facilities', [])))
    with col3:
        st.metric("Query Type", results.get('query_type', 'N/A'))
    with col4:
        if st.session_state.last_query:
            st.metric("Last Query", st.session_state.last_query.split(':')[0])
    
    st.markdown("---")
    
    # Process and display map based on query type
    if results.get('query_type') in ['Q1', 'Q2'] and not results.get('samplepoints', pd.DataFrame()).empty:
        # Process sample points
        st.subheader("📍 Interactive Map - Sample Points")
        
        samplepoints_df = results['samplepoints'].copy()
        samplepoints_df['results'] = samplepoints_df['results'].apply(truncate_results)
        samplepoints_df['spWKT'] = samplepoints_df['spWKT'].apply(wkt.loads)
        samplepoints_gdf = gpd.GeoDataFrame(samplepoints_df, geometry='spWKT')
        samplepoints_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Process facilities
        facilities_df = results['facilities'].copy()
        if not facilities_df.empty:
            facilities_df['facWKT'] = facilities_df['facWKT'].apply(wkt.loads)
            facilities_gdf = gpd.GeoDataFrame(facilities_df, geometry='facWKT')
            facilities_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Process counties if Q2
        if results.get('query_type') == 'Q2' and 'counties' in results:
            counties_df = results['counties'].copy()
            counties_df['countyWKT'] = counties_df['countyWKT'].apply(wkt.loads)
            counties_gdf = gpd.GeoDataFrame(counties_df, geometry='countyWKT')
            counties_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Create map
        if results.get('query_type') == 'Q2' and 'counties' in results:
            # For Q2, start with county boundaries
            bounds = counties_gdf.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
            
            # Add county boundaries
            for idx, row in counties_gdf.iterrows():
                folium.GeoJson(
                    row.geometry,
                    name=f"County: {row['countyName']}",
                    style_function=lambda feature: {
                        'fillColor': 'none',
                        'color': 'gray',
                        'weight': 2,
                        'dashArray': '5, 5'
                    }
                ).add_to(m)
        else:
            # For Q1, center on Maine
            m = folium.Map(location=[45.2538, -69.4455], zoom_start=7)
        
        # Add sample points
        sample_group = folium.FeatureGroup(name='Sample Points')
        for idx, row in samplepoints_gdf.iterrows():
            folium.CircleMarker(
                location=[row.geometry.y, row.geometry.x],
                radius=min(float(row['Max']) if float(row['Max']) < 10 else 12, 20),
                popup=folium.Popup(
                    f"""<b>Samples:</b> {row['samples']}<br>
                    <b>Max Concentration:</b> {row['Max']} {row['unit']}<br>
                    <b>Results:</b><br>{row['results']}""",
                    max_width=400
                ),
                color='DarkOrange',
                fill=True,
                fillOpacity=0.6,
                weight=2
            ).add_to(sample_group)
        sample_group.add_to(m)
        
        # Add facilities
        if not facilities_df.empty:
            colors = {'Solid Waste Landfill': 'brown', 'National Security': 'darkblue'}
            
            for industry_name in facilities_gdf['industryName'].unique():
                industry_group = folium.FeatureGroup(name=industry_name)
                industry_facilities = facilities_gdf[facilities_gdf['industryName'] == industry_name]
                
                for idx, row in industry_facilities.iterrows():
                    color = colors.get(row['industryName'], 'gray')
                    folium.CircleMarker(
                        location=[row.geometry.y, row.geometry.x],
                        radius=6,
                        popup=f"<b>{row['facilityName']}</b><br>{row['industryName']}",
                        color=color,
                        fill=True,
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(industry_group)
                industry_group.add_to(m)
        
        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Display map
        st_folium(m, height=600, width='100%', returned_objects=[])
        
        # Display data tables
        with st.expander("📊 Sample Points Data"):
            display_df = samplepoints_df.drop(columns=['spWKT'])
            st.dataframe(display_df, use_container_width=True)
        
        if not facilities_df.empty:
            with st.expander("🏭 Facilities Data"):
                display_df = facilities_df.drop(columns=['facWKT'])
                st.dataframe(display_df, use_container_width=True)
    
    elif results.get('query_type') in ['Q3', 'Q4'] and 'surfacewater' in results:
        # Process surface water
        st.subheader("💧 Interactive Map - Surface Water Bodies")
        
        surfacewater_df = results['surfacewater'].copy()
        if not surfacewater_df.empty:
            surfacewater_df['swWKT'] = surfacewater_df['swWKT'].apply(wkt.loads)
            surfacewater_gdf = gpd.GeoDataFrame(surfacewater_df, geometry='swWKT')
            surfacewater_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Process facilities
        facilities_df = results['facilities'].copy()
        if not facilities_df.empty:
            facilities_df['facWKT'] = facilities_df['facWKT'].apply(wkt.loads)
            facilities_gdf = gpd.GeoDataFrame(facilities_df, geometry='facWKT')
            facilities_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Process counties
        if 'counties' in results:
            counties_df = results['counties'].copy()
            counties_df['countyWKT'] = counties_df['countyWKT'].apply(wkt.loads)
            counties_gdf = gpd.GeoDataFrame(counties_df, geometry='countyWKT')
            counties_gdf.set_crs(epsg=4326, inplace=True, allow_override=True)
        
        # Create map centered on counties
        if 'counties' in results:
            bounds = counties_gdf.total_bounds
            center_lat = (bounds[1] + bounds[3]) / 2
            center_lon = (bounds[0] + bounds[2]) / 2
            m = folium.Map(location=[center_lat, center_lon], zoom_start=8)
            
            # Add county boundaries
            for idx, row in counties_gdf.iterrows():
                folium.GeoJson(
                    row.geometry,
                    name=f"County: {row['countyName']}",
                    style_function=lambda feature: {
                        'fillColor': 'none',
                        'color': 'gray',
                        'weight': 2,
                        'dashArray': '5, 5'
                    }
                ).add_to(m)
        
        # Add surface water
        if not surfacewater_df.empty:
            water_group = folium.FeatureGroup(name='Surface Water')
            for idx, row in surfacewater_gdf.iterrows():
                popup_text = f"<b>Water Body</b><br>"
                if pd.notna(row.get('surfacewatername')):
                    popup_text += f"Name: {row['surfacewatername']}<br>"
                if pd.notna(row.get('waterType')):
                    popup_text += f"Type: {row['waterType']}<br>"
                if pd.notna(row.get('COMID')):
                    popup_text += f"COMID: {row['COMID']}<br>"
                if pd.notna(row.get('reachCode')):
                    popup_text += f"Reach Code: {row['reachCode']}"
                
                folium.GeoJson(
                    row.geometry,
                    style_function=lambda feature: {
                        'fillColor': 'blue',
                        'color': 'blue',
                        'weight': 2,
                        'fillOpacity': 0.5
                    },
                    popup=folium.Popup(popup_text, max_width=300)
                ).add_to(water_group)
            water_group.add_to(m)
        
        # Add facilities
        if not facilities_df.empty:
            colors = {'Solid Waste Landfill': 'brown', 'National Security': 'darkblue'}
            
            for industry_name in facilities_gdf['industryName'].unique():
                industry_group = folium.FeatureGroup(name=industry_name, show=False)
                industry_facilities = facilities_gdf[facilities_gdf['industryName'] == industry_name]
                
                for idx, row in industry_facilities.iterrows():
                    color = colors.get(row['industryName'], 'gray')
                    folium.CircleMarker(
                        location=[row.geometry.y, row.geometry.x],
                        radius=6,
                        popup=f"<b>{row['facilityName']}</b><br>{row['industryName']}",
                        color=color,
                        fill=True,
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(industry_group)
                industry_group.add_to(m)
        
        # Add layer control
        folium.LayerControl(collapsed=False).add_to(m)
        
        # Display map
        st_folium(m, height=600, width='100%', returned_objects=[])
        
        # Display data tables
        with st.expander("💧 Surface Water Data"):
            display_df = surfacewater_df.drop(columns=['swWKT'])
            st.dataframe(display_df, use_container_width=True)
        
        if not facilities_df.empty:
            with st.expander("🏭 Facilities Data"):
                display_df = facilities_df.drop(columns=['facWKT'])
                st.dataframe(display_df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("🔬 **SAWGraph Spatial Query Demo** | Built with Streamlit & Folium | Maine PFAS Data Visualization")
