import streamlit as st
from SPARQLWrapper import SPARQLWrapper2, JSON, GET, DIGEST
import time
import pandas as pd
import rdflib

st.set_page_config(page_title="SPARQL Debug Tool", layout="wide")
st.title("🔍 SPARQL Query Debug Tool")
st.markdown("Test queries and see execution details")

# Initialize session state
if 'query_log' not in st.session_state:
    st.session_state.query_log = []

# Sidebar
with st.sidebar:
    st.header("Query Options")
    
    query_choice = st.selectbox(
        "Select Test Query",
        [
            "1. Simple COUNT",
            "2. Basic Sample Points",
            "3. Facilities Only",
            "4. Simple Join",
            "5. Custom Query"
        ]
    )
    
    if query_choice == "5. Custom Query":
        custom_query = st.text_area("Enter SPARQL Query", height=200)
    
    timeout = st.slider("Query Timeout (seconds)", 5, 60, 30)
    
    st.markdown("---")
    if st.button("Clear Log"):
        st.session_state.query_log = []

# Query definitions
queries = {
    "1. Simple COUNT": """
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
SELECT (COUNT(?s) as ?count) WHERE {
    ?s a coso:SamplePoint .
} LIMIT 1
""",
    "2. Basic Sample Points": """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?samplePoint ?spWKT WHERE {
    ?samplePoint rdf:type coso:SamplePoint;
                 geo:hasGeometry/geo:asWKT ?spWKT .
} LIMIT 10
""",
    "3. Facilities Only": """
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>

SELECT ?facility ?facilityName WHERE {
    SERVICE <repository:FIO> {
        ?facility fio:ofIndustry naics:NAICS-562212 ;
                  rdfs:label ?facilityName .
    }
} LIMIT 10
""",
    "4. Simple Join": """
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT DISTINCT ?s2 ?samplePoint WHERE {
    ?s2 rdf:type kwg-ont:S2Cell_Level13 .
    ?samplePoint kwg-ont:sfWithin ?s2 ;
                 rdf:type coso:SamplePoint .
} LIMIT 5
"""
}

# Main area
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Query Execution")
    
    if st.button("🚀 Execute Query", type="primary"):
        # Get the query
        if query_choice == "5. Custom Query":
            query = custom_query if 'custom_query' in locals() else ""
        else:
            query = queries[query_choice]
        
        if not query:
            st.error("Please enter a query")
        else:
            # Create containers for live updates
            status_container = st.empty()
            progress_container = st.empty()
            time_container = st.empty()
            
            try:
                # Log start
                log_entry = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "query_type": query_choice,
                    "status": "Started",
                    "duration": 0,
                    "error": None,
                    "result_count": 0
                }
                
                # Setup connection
                status_container.info("🔌 Setting up connection...")
                start_time = time.time()
                
                endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
                sparql = SPARQLWrapper2(endpoint)
                sparql.setHTTPAuth(DIGEST)
                sparql.setCredentials('sawgraph-endpoint', 'skailab')
                sparql.setMethod(GET)
                sparql.setReturnFormat(JSON)
                sparql.setTimeout(timeout)
                
                # Set query
                status_container.info("📝 Setting query...")
                sparql.setQuery(query)
                
                # Execute query
                status_container.warning("⏳ Executing query... (this may take a while)")
                progress_container.progress(50)
                
                # Update time every second in a separate thread-like manner
                query_start = time.time()
                
                result = sparql.query()
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Process results
                status_container.success(f"✅ Query completed in {duration:.2f} seconds!")
                progress_container.progress(100)
                
                # Convert results
                results = []
                for binding in result.bindings:
                    row = {}
                    for var in binding:
                        value = binding[var]
                        row[var] = rdflib.term.Literal(value.value, datatype=value.datatype).toPython()
                    results.append(row)
                
                # Update log
                log_entry["status"] = "Success"
                log_entry["duration"] = duration
                log_entry["result_count"] = len(results)
                
                # Display results
                if results:
                    st.subheader(f"Results ({len(results)} rows)")
                    df = pd.DataFrame(results)
                    st.dataframe(df)
                    
                    # Show first few results in detail
                    with st.expander("Detailed Results"):
                        for i, row in enumerate(results[:5]):
                            st.write(f"**Row {i+1}:**")
                            for key, value in row.items():
                                st.write(f"- {key}: {value}")
                else:
                    st.warning("No results returned")
                
            except Exception as e:
                status_container.error(f"❌ Query failed: {str(e)}")
                progress_container.progress(0)
                log_entry["status"] = "Failed"
                log_entry["duration"] = time.time() - start_time
                log_entry["error"] = str(e)
            
            # Add to log
            st.session_state.query_log.insert(0, log_entry)

with col2:
    st.header("Query Log")
    
    if st.session_state.query_log:
        for entry in st.session_state.query_log[:10]:  # Show last 10
            color = "green" if entry["status"] == "Success" else "red"
            st.markdown(
                f"""<div style="border-left: 3px solid {color}; padding-left: 10px; margin-bottom: 10px;">
                <b>{entry['timestamp']}</b> - {entry['query_type']}<br>
                Status: {entry['status']}<br>
                Duration: {entry['duration']:.2f}s<br>
                Results: {entry['result_count']}
                {f"<br>Error: {entry['error']}" if entry['error'] else ""}
                </div>""",
                unsafe_allow_html=True
            )
    else:
        st.info("No queries executed yet")

# Query display
st.header("Current Query")
if query_choice == "5. Custom Query":
    st.code(custom_query if 'custom_query' in locals() else "Enter custom query above", language="sparql")
else:
    st.code(queries[query_choice], language="sparql")

# Tips
with st.expander("💡 Debugging Tips"):
    st.markdown("""
    1. **Start with simple queries** - Test basic SELECT with LIMIT 1
    2. **Check timeouts** - Increase timeout if queries are complex
    3. **Remove GROUP BY** - These operations can be very slow
    4. **Add more LIMIT clauses** - Limit intermediate results
    5. **Test SERVICE calls separately** - Each repository might have different performance
    6. **Check the endpoint status** - The server might be overloaded
    
    If queries consistently timeout:
    - The endpoint might be down
    - Network issues might be blocking the connection
    - The queries might be too complex for the current indexing
    """)
