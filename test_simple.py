#!/usr/bin/env python3
"""
Test with the absolute simplest possible query
"""

from SPARQLWrapper import SPARQLWrapper, JSON, GET, DIGEST
import time

print("Testing simplest possible SPARQL query...")
print("-" * 50)

# Use SPARQLWrapper (not SPARQLWrapper2) for more control
endpoint = 'https://gdb.acg.maine.edu:7201/repositories/PFAS'
sparql = SPARQLWrapper(endpoint)
sparql.setHTTPAuth(DIGEST)
sparql.setCredentials('sawgraph-endpoint', 'skailab')
sparql.setMethod(GET)
sparql.setReturnFormat(JSON)

# Set a longer timeout
sparql.setTimeout(60)  # 60 seconds

# The absolute simplest query - just ask for 1 triple
query = """
SELECT * WHERE {
    ?s ?p ?o .
} LIMIT 1
"""

print(f"Query to execute:\n{query}")
print("\nExecuting query (timeout: 60 seconds)...")

try:
    start_time = time.time()
    sparql.setQuery(query)
    
    # Execute and get raw results
    results = sparql.query().convert()
    
    end_time = time.time()
    print(f"\n✅ SUCCESS! Query completed in {end_time - start_time:.2f} seconds")
    
    # Print raw results
    print("\nRaw results:")
    print(results)
    
    # Parse results
    if "results" in results and "bindings" in results["results"]:
        bindings = results["results"]["bindings"]
        print(f"\nFound {len(bindings)} results")
        
        if bindings:
            print("\nFirst result:")
            for var, value in bindings[0].items():
                print(f"  ?{var} = {value['value']}")
    
except Exception as e:
    end_time = time.time()
    print(f"\n❌ FAILED after {end_time - start_time:.2f} seconds")
    print(f"Error: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Try to get more error details
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print("\n" + "-" * 50)
print("\nPossible issues if this failed:")
print("1. Network/firewall blocking the connection")
print("2. Endpoint is down or overloaded")
print("3. Authentication credentials are incorrect")
print("4. SSL/TLS certificate issues")
print("5. The endpoint URL might have changed")

# Also test the endpoint status URL
print("\n" + "-" * 50)
print("Testing endpoint status page...")
try:
    import requests
    from requests.auth import HTTPDigestAuth
    
    status_url = "https://gdb.acg.maine.edu:7201/repositories/PFAS/size"
    response = requests.get(
        status_url, 
        auth=HTTPDigestAuth('sawgraph-endpoint', 'skailab'),
        timeout=10,
        verify=True  # Change to False if SSL issues
    )
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print(f"Repository size: {response.text}")
except Exception as e:
    print(f"Status check failed: {e}")
