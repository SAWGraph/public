from branca.element import Figure                                  # For controlling the size of the final map
import folium                                                      # For map layer control
import geopandas as gpd                                            # For geospatial dataframes
import pandas as pd                                                # For dataframes
from shapely import wkt                                            # For working with WKT coordinates in a GeoDataFrame
from SPARQLWrapper import SPARQLWrapper, JSON, GET, POST, DIGEST   # For querying SPARQL endpoints
import sparql_dataframe                                            # For converting SPARQL query results to Pandas dataframes
# from tabulate import tabulate                                      # For pretty printing dataframes
# import webbrowser
import streamlit as st
from streamlit_folium import st_folium


pd.options.display.width = 240

endpointFIO = 'https://gdb.acg.maine.edu:7201/repositories/FIO'
sparqlFIO = SPARQLWrapper(endpointFIO)
sparqlFIO.setHTTPAuth(DIGEST)
sparqlFIO.setCredentials('sawgraph-endpoint', 'skailab')
sparqlFIO.setMethod(GET)
sparqlFIO.setReturnFormat(JSON)

endpointSpatial = 'https://gdb.acg.maine.edu:7201/repositories/Spatial'
sparqlSpatial = SPARQLWrapper(endpointSpatial)
sparqlSpatial.setHTTPAuth(DIGEST)
sparqlSpatial.setCredentials('sawgraph-endpoint', 'skailab')
sparqlSpatial.setMethod(GET)
sparqlSpatial.setReturnFormat(JSON)

endpointHydrology = 'https://gdb.acg.maine.edu:7201/repositories/Hydrology'
sparqlHydrology = SPARQLWrapper(endpointHydrology)
sparqlHydrology.setHTTPAuth(DIGEST)
sparqlHydrology.setCredentials('sawgraph-endpoint', 'skailab')
sparqlHydrology.setMethod(GET)
sparqlHydrology.setReturnFormat(JSON)


query = """
PREFIX fio: <http://w3id.org/fio/v1/fio#>
PREFIX geo: <http://www.opengis.net/ont/geosparql#>
PREFIX hyf: <https://www.opengis.net/def/schema/hy_features/hyf/>
PREFIX kwg-ont: <http://stko-kwg.geog.ucsb.edu/lod/ontology/>
PREFIX kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/>
PREFIX naics: <http://w3id.org/fio/v1/naics#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>
PREFIX spatial: <http://purl.org/spatialai/spatial/spatial-full#>

SELECT * WHERE {
    ?fac rdf:type fio:Facility ;
            fio:ofIndustry ?code ;
            kwg-ont:sfWithin ?fac_s2 .
    ?fac_s2 rdf:type kwg-ont:S2Cell_Level13 .
    OPTIONAL { ?fac rdfs:label ?faclabel . }
    OPTIONAL { ?code rdfs:label ?ind . }
    VALUES ?code { naics:NAICS-562212 naics:NAICS-92811 naics:NAICS-928110 }

    SERVICE <repository:Spatial> {
        SELECT * WHERE {
            ?nbr_s2 kwg-ont:sfTouches | owl:sameAs ?fac_s2 ;
                    rdf:type kwg-ont:S2Cell_Level13 ;
                    spatial:connectedTo kwgr:administrativeRegion.USA.23 .
        }
    }

    SERVICE <repository:Hydrology> {
        SELECT * WHERE {
            ?wb rdf:type hyf:HY_WaterBody ;
                spatial:connectedTo ?nbr_s2 .
            OPTIONAL { ?wb schema:name ?wblabel . }
        }
    }
}
"""
df = sparql_dataframe.get(endpointFIO, query)


def geo_query(data):
    instances = ''
    for d in data:
        instances += '<' + d + '>, '
    instances = instances[:-2]
    query = """
    PREFIX geo: <http://www.opengis.net/ont/geosparql#>

    SELECT * WHERE {
        ?x geo:hasGeometry/geo:asWKT ?wkt .
        FILTER (?x IN (""" + instances + """))
    }
    """
    return query


def retrieve_geometries(instances, repo):
    max_length = 50
    if len(instances) < max_length + 1:
        query = geo_query(instances)
        return sparql_dataframe.get(repo, query)
    else:
        data_dict = {}
        for i in range(len(instances) // max_length + 1):
            data_dict[i] = instances[i * max_length:(i + 1) * max_length]
        df_dict = {}
        for k, v in data_dict.items():
            query = geo_query(v)
            df_temp = sparql_dataframe.get(repo, query)
            if k == 0:
                df_dict[k] = [df_temp.columns.values.tolist()] + df_temp.values.tolist()
            else:
                df_dict[k] = df_temp.values.tolist()
        data_list = []
        for k, v in df_dict.items():
            for item in v:
                data_list.append(item)
        df_geo = pd.DataFrame(data_list[1:], columns=data_list[0])
        df_geo.drop_duplicates(inplace=True)
        return df_geo


fac = []
fac_s2 = []
nbr_s2 = []
wb = []
for row in df.itertuples():
    if row.fac not in fac:
        fac.append(row.fac)
    if row.fac_s2 not in fac_s2:
        fac_s2.append(row.fac_s2)
    if row.nbr_s2 not in nbr_s2:
        nbr_s2.append(row.nbr_s2)
    if row.wb not in wb:
        wb.append(row.wb)


df_fac_geo = retrieve_geometries(fac, endpointFIO)
df_fac_s2_geo = retrieve_geometries(fac_s2, endpointSpatial)
df_nbr_s2_geo = retrieve_geometries(nbr_s2, endpointSpatial)
df_wb_geo = retrieve_geometries(wb, endpointHydrology)


def new_column(df_in, df_wkt, col_item, col_wkt):
    df_out = df_in.copy()
    df_out[col_wkt] = df_out[col_item]
    for row in df_wkt.itertuples():
        df_out.loc[df_out[col_wkt] == row.x, col_wkt] = row.wkt
    df_out = df_out[df_out[col_item] != df_out[col_wkt]]
    return df_out


df = new_column(df, df_fac_geo, 'fac', 'fac_wkt')
df = new_column(df, df_fac_s2_geo, 'fac_s2', 'fac_s2_wkt')
df = new_column(df, df_nbr_s2_geo, 'nbr_s2', 'nbr_s2_wkt')
df = new_column(df, df_wb_geo, 'wb', 'wb_wkt')


df_fac = df[['fac', 'faclabel', 'fac_wkt']].copy()
df_fac.drop_duplicates(inplace=True)
df_fac['fac_wkt'] = df_fac['fac_wkt'].apply(wkt.loads)

df_fac_s2 = df[['fac_s2', 'fac_s2_wkt']].copy()
df_fac_s2.drop_duplicates(inplace=True)
df_fac_s2['fac_s2_wkt'] = df_fac_s2['fac_s2_wkt'].apply(wkt.loads)

df_nbr_s2 = df[['nbr_s2', 'nbr_s2_wkt']].copy()
df_nbr_s2.drop_duplicates(inplace=True)
df_nbr_s2['nbr_s2_wkt'] = df_nbr_s2['nbr_s2_wkt'].apply(wkt.loads)

df_wb = df[['wb', 'wblabel', 'wb_wkt']].copy()
df_wb.drop_duplicates(inplace=True)
df_wb['wb_wkt'] = df_wb['wb_wkt'].apply(wkt.loads)


gdf_fac = gpd.GeoDataFrame(df_fac, geometry='fac_wkt')
gdf_fac.set_crs(epsg=4326, inplace=True, allow_override=True)

gdf_fac_s2 = gpd.GeoDataFrame(df_fac_s2, geometry='fac_s2_wkt')
gdf_fac_s2.set_crs(epsg=4326, inplace=True, allow_override=True)

gdf_nbr_s2 = gpd.GeoDataFrame(df_nbr_s2, geometry='nbr_s2_wkt')
gdf_nbr_s2.set_crs(epsg=4326, inplace=True, allow_override=True)

gdf_wb = gpd.GeoDataFrame(df_wb, geometry='wb_wkt')
gdf_wb.set_crs(epsg=4326, inplace=True, allow_override=True)


fac_color = 'red'
fac_s2_color = 'darkred'
s2_color = 'black'
wb_color = 'blue'
boundweight = 5

map = gdf_fac.explore(color=fac_color,
                      style_kwds=dict(weight=boundweight),
                      tooltip=True,
                      name='<span style="color: red;">Facilities</span>',
                      show=True)
gdf_fac_s2.explore(m=map,
                   color=fac_s2_color,
                   style_kwds=dict(weight=boundweight),
                   tooltip=True,
                   name='<span style="color: darkred;">Facilities S2 Cells</span>',
                   show=False)
gdf_nbr_s2.explore(m=map,
                   color=s2_color,
                   style_kwds=dict(weight=boundweight),
                   tooltip=True,
                   name='S2 Cell Neighbors',
                   show=False)
gdf_wb.explore(m=map,
               color=wb_color,
               style_kwds=dict(weight=boundweight),
               tooltip=True,
               highlight=False,
               name='<span style="color: blue;">Water Bodies</span>',
               show=True)

# folium.TileLayer("stamenterrain", show=False).add_to(map)
# folium.TileLayer("MapQuest Open Aerial", show=False).add_to(map)
folium.LayerControl(collapsed=False).add_to(map)


map.save('SAWGraph_UC1_CQ2_map.html')

def auto_open(path):
    html_page = f'{path}'
    # f_map.save(html_page)
    new = 2
    webbrowser.open(html_page, new=new)

# auto_open('SAWGraph_UC1_CQ2_map.html')
#
# fig = Figure(width=800, height=600)
# fig.add_child(map)

st.set_page_config(layout='wide')
st.title('SAWGraph Use Case 1 (PFAS Testing) Competency Question 2')
st.header('What surface water bodies are near landfills or Department of Defense sites in Maine?', divider=True)
col1, col2 = st.columns(2)
with col1:
    st_data_map = st_folium(map, width=800, height=600, returned_objects=[])
with col2:
    st.markdown('The first stage of testing prioritization for many states involves identifying facilities that are likely to be utilizing PFAs chemicals. This competency question addresses features of enivronmental concern (surface water bodies) that are near potential contamination sources.')
    st.markdown('- Landfills are sites of PFAS contamination resulting from both industrial usage and prevalence in consumer products that accumulate in landfills.')
    st.markdown('- Department of Defense sites are frequently on the list PFAs contamination primarily because of the usage of Fire Fighiting Foam (AFFF).')
    st.markdown('The query could easily be modified to identify other features of concern (water supply wells, streams, etc.) or other potential contamination sources. This query would inform testing prioritization as it would help identify surface water bodies that may be at risk of contamination.')
    st.markdown('The map was generated by querying the SAWGraph for facilities of the specified type in the state of Maine (that are suspected pfas sources), and then finding the nearby surface water bodies based on the S2 Cell spatial indexing.')

# Also st.subheader, st.sidebar, variables