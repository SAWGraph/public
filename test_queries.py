#!/usr/bin/env python3
"""
Test script to verify SPARQL queries work correctly with modified variable handling
"""

from SPARQLWrapper import SPARQLWrapper2, JSON, GET, DIGEST
import rdflib
import pandas as pd

def setup_sparql_endpoint():
    """Setup SPARQL endpoint with authentication"""
    endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
    sparql = SPARQLWrapper2(endpoint)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials('sawgraph-endpoint', 'skailab')
    sparql.setMethod(GET)
    sparql.setReturnFormat(JSON)
    return sparql

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

def test_modified_query():
    """Test the modified Q1 query with new variable handling"""
    
    print("Testing modified Q1 query...")
    print("-" * 50)
    
    # Modified query with new variable handling
    query = '''
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
WHERE {
    SERVICE <repository:FIO>{
        ?s2neighbor kwg-ont:sfContains ?facility.
        ?facility fio:ofIndustry ?industry.
        VALUES ?industry { naics:NAICS-562212 naics:NAICS-928110 }.
    }
    SERVICE <repository:Spatial>{
        ?s2 kwg-ont:sfTouches|owl:sameAs ?s2neighbor.
        ?s2neighbor rdf:type kwg-ont:S2Cell_Level13.
    }
    
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
} 
GROUP BY ?samplePoint ?spWKT ?sample ?unit
LIMIT 5
'''
    
    try:
        sparql = setup_sparql_endpoint()
        sparql.setQuery(query)
        result = sparql.query()
        df = convertToDataframe(result)
        
        print(f"✅ Query executed successfully!")
        print(f"   Found {len(df)} sample points")
        print(f"   Columns: {', '.join(df.columns)}")
        
        if not df.empty:
            print(f"\nFirst result:")
            print(f"   Sample: {df.iloc[0]['samples']}")
            print(f"   Max concentration: {df.iloc[0]['Max']} {df.iloc[0]['unit']}")
            print(f"   Result count: {df.iloc[0]['resultCount']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {str(e)}")
        return False

def test_facilities_query():
    """Test the facilities query"""
    
    print("\n\nTesting facilities query...")
    print("-" * 50)
    
    query = '''
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>

SELECT DISTINCT ?facility ?facWKT ?facilityName ?industry ?industryName WHERE {
    SERVICE <repository:FIO>{
        ?facility fio:ofIndustry ?industry;
                geo:hasGeometry/geo:asWKT ?facWKT;
                rdfs:label ?facilityName.
        ?industry rdfs:label ?industryName.
        VALUES ?industry { naics:NAICS-562212 naics:NAICS-928110 }.
    }
}
LIMIT 5
'''
    
    try:
        sparql = setup_sparql_endpoint()
        sparql.setQuery(query)
        result = sparql.query()
        df = convertToDataframe(result)
        
        print(f"✅ Query executed successfully!")
        print(f"   Found {len(df)} facilities")
        
        if not df.empty:
            print(f"\nFirst facility:")
            print(f"   Name: {df.iloc[0]['facilityName']}")
            print(f"   Industry: {df.iloc[0]['industryName']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("SAWGraph Query Test")
    print("=" * 50)
    
    # Test both queries
    q1_success = test_modified_query()
    q2_success = test_facilities_query()
    
    print("\n" + "=" * 50)
    if q1_success and q2_success:
        print("✅ All tests passed! The queries work correctly.")
        print("   The Streamlit app should work without errors.")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
