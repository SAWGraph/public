#!/usr/bin/env python3
"""
Test SPARQL endpoint connectivity and basic queries
"""

from SPARQLWrapper import SPARQLWrapper2, JSON, GET, DIGEST
import time
import sys

print("Testing SPARQL Endpoint Connection...")
print("=" * 50)

# Test 1: Basic connection
print("\n1. Testing endpoint connection...")
try:
    endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
    sparql = SPARQLWrapper2(endpoint)
    sparql.setHTTPAuth(DIGEST)
    sparql.setCredentials('sawgraph-endpoint', 'skailab')
    sparql.setMethod(GET)
    sparql.setReturnFormat(JSON)
    print("✅ Connection setup successful")
except Exception as e:
    print(f"❌ Connection setup failed: {e}")
    sys.exit(1)

# Test 2: Simple COUNT query
print("\n2. Testing simple COUNT query...")
simple_query = """
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
SELECT (COUNT(?s) as ?count) WHERE {
    ?s a coso:SamplePoint .
} LIMIT 1
"""

try:
    start_time = time.time()
    sparql.setQuery(simple_query)
    print("   Query set, executing...")
    result = sparql.query()
    end_time = time.time()
    
    print(f"✅ Query executed in {end_time - start_time:.2f} seconds")
    
    # Print results
    for binding in result.bindings:
        count = binding['count'].value
        print(f"   Found {count} sample points in the database")
except Exception as e:
    print(f"❌ Query failed: {e}")

# Test 3: Simple facility query with LIMIT
print("\n3. Testing facility query with LIMIT 5...")
facility_query = """
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>

SELECT ?facility ?facilityName WHERE {
    SERVICE <repository:FIO> {
        ?facility fio:ofIndustry naics:NAICS-562212 ;
                  rdfs:label ?facilityName .
    }
} LIMIT 5
"""

try:
    start_time = time.time()
    sparql.setQuery(facility_query)
    print("   Query set, executing...")
    result = sparql.query()
    end_time = time.time()
    
    print(f"✅ Query executed in {end_time - start_time:.2f} seconds")
    
    # Print results
    count = 0
    for binding in result.bindings:
        count += 1
        print(f"   Facility {count}: {binding['facilityName'].value}")
except Exception as e:
    print(f"❌ Query failed: {e}")

# Test 4: Test a simple version of Q1 with heavy limits
print("\n4. Testing simplified Q1 query with LIMIT 5...")
test_q1 = """
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT ?samplePoint ?spWKT ?sampleId WHERE {
    ?samplePoint rdf:type coso:SamplePoint;
                 geo:hasGeometry/geo:asWKT ?spWKT .
    ?sample coso:fromSamplePoint ?samplePoint;
            dcterms:identifier ?sampleId .
} LIMIT 5
"""

try:
    start_time = time.time()
    sparql.setQuery(test_q1)
    print("   Query set, executing...")
    result = sparql.query()
    end_time = time.time()
    
    print(f"✅ Query executed in {end_time - start_time:.2f} seconds")
    
    # Print results
    count = 0
    for binding in result.bindings:
        count += 1
        print(f"   Sample {count}: {binding['sampleId'].value}")
except Exception as e:
    print(f"❌ Query failed: {e}")

# Test 5: Test the complex join but with minimal data
print("\n5. Testing complex join with LIMIT 2...")
complex_query = """
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX coso: <http://w3id.org/coso/v1/contaminoso#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX fio: <http://w3id.org/fio/v1/fio#>

SELECT ?samplePoint ?facility WHERE {
    SERVICE <repository:FIO> {
        ?facility fio:ofIndustry naics:NAICS-562212 .
    }
    SERVICE <repository:Spatial> {
        ?s2 kwg-ont:sfContains ?facility ;
            rdf:type kwg-ont:S2Cell_Level13 .
    }
    ?samplePoint kwg-ont:sfWithin ?s2 ;
                 rdf:type coso:SamplePoint .
} LIMIT 2
"""

try:
    start_time = time.time()
    sparql.setQuery(complex_query)
    print("   Query set, executing...")
    result = sparql.query()
    end_time = time.time()
    
    print(f"✅ Query executed in {end_time - start_time:.2f} seconds")
    
    # Print results
    count = 0
    for binding in result.bindings:
        count += 1
        print(f"   Result {count} found")
except Exception as e:
    print(f"❌ Query failed: {e}")

print("\n" + "=" * 50)
print("Testing complete!")
print("\nIf queries are timing out, the issue might be:")
print("1. The endpoint is overloaded")
print("2. The queries are too complex without proper indexing")
print("3. Network issues or firewall blocking")
print("4. The GROUP_CONCAT operations are too expensive")
