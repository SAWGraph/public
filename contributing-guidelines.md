# Namespaces and Named Graphs

Each dataset has its own namespace, separate namespaces for TBox and ABox:
- lower case prefixes
- ABox with "_data" attached
   - `@prefix me_egad: <http://w3id.org/sawgraph/v1/me-egad#> .`
   - `@prefix me_egad_data: <http://w3id.org/sawgraph/v1/me-egad-data#> .`
   - `@prefix us_wqp: <http://sawgraph.spatialai.org/v1/us-wqp#> .`
   - `@prefix us_wqp_data: <http://sawgraph.spatialai.org/v1/us-wqp-data#> .`

Each namespace is its own named graph </br>
ABox and TBox are their own named graph
- `http://sawgraph.spatialai.org/v1/namedgraph/me-egad`
- `http://sawgraph.spatialai.org/v1/namedgraph/me-egad-data`
- `http://sawgraph.spatialai.org/v1/namedgraph/me-egad-s2`

# Naming Conventions
Class names
- camel case
- start with upper case
- no special symbols except hyphens

Object and Data properties
- camel case
- start with lower case

Instances
- must start with a lower case
- attach "d." followed by class name that it is instantiated in followed by "." and unique identifier for the instance among all of that class

Examples
- `me_egad_data:d.EGAD-Observation.1234 rdf:type me_egad:EGAD-Observation . `
- `prefix:CLASSNAME_id`
- `egad:Observation/1234`
- `egad:1234`

# Versioning
Integers are used for version numbers. ABox version numbers (for sets of triples) are not tied to TBox version numbers. ABox version numbers increase when new data is involved, which may be additional data or additional attributes for current data, but do not change for minor updates or error corrections.

# Provenance

`dcterms:issued` is used for releases. `dcterms:modified` is used for small updates that do not change the current version number.

## TBox example
This is a minimal example focused on provenance only.

**Ontology**
```
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix me_egad: <http://w3id.org/sawgraph/v1/me-egad#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

<http://w3id.org/sawgraph/v1/me-egad> rdf:type owl:Ontology ;
                                      dcterms:issued "2026-03-11"^^xsd:date ;
                                      prov:wasAttributedTo <https://sawgraph.github.io> .
```
**Classes, Properties, and Named Individuals**
```
me_egad:associatedSite rdf:type owl:ObjectProperty ;
                       rdfs:isDefinedBy <http://w3id.org/sawgraph/v1/me-egad> .
```

## ABox example
**Dataset**

Spatial and temporal coverage are optional but recommended. If the ABox is comprised of multiple files, create a single file that only contains the `owl:Ontology` information and import the data files.
```
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix kwgr: <http://stko-kwg.geog.ucsb.edu/lod/resource/> .
@prefix me_egad_data: <http://w3id.org/sawgraph/v1/me-egad-data#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix stad: <http://purl.org/spatialai/stad/v2/core/> .

<http://w3id.org/sawgraph/v2/me-egad-data> rdf:type owl:Ontology ;
                                           dcterms:issued "2024-07-26" ;   #first triplification release at this version
                                           dcterms:modified "2026-04-17" ; #date of last triplification at this version
                                           prov:wasDerivedFrom me_egad_data:sourceDataset .
me_egad_data:sourceDataset rdf:type stad:Dataset ;
                           dcterms:issued "2026-01-01" ;  #dataset publication date
                           dcterms:source <https://www.maine.gov/dep/maps-data/egad/> ;
                           stad:hasSpatialCoverage kwgr:administrativeRegion.USA.23 ;
                           stad:hasTemporalCoverage me_egad_data:temporalCoverage .
me_egad_data:temporalCoverage a time:ProperInterval ;
                              time:hasBeginning me_egad_data:temporalCoverage.start ;
                              time:hasEnd me_egad_data:temporalCoverage.end ;
                              time:hasDurationDescription me_egad_data:temporalCoverage.duration .
me_egad_data:temporalCoverage.start a time:Instant ;
                                    time:inXSDDateTime "2022-01-01T05:00:00Z"^^xsd:dateTime .
me_egad_data:temporalCoverage.end a time:Instant ;
                                  time:inXSDDateTime "2026-01-01T05:00:00Z"^^xsd:dateTime .
me_egad_data:temporalCoverage.duration a time:DurationDescription ;
                                       time:years "5"^^xsd:decimal .
```
**Instances**
```
me_egad_data:quantityValue.C0591FS.BNO.20230918.375951 a coso:DetectQuantityValue ;
                                                       rdfs:isDefinedBy <http://w3id.org/sawgraph/v2/me-egad-data> .
```

# Annotation Property Conventions
| Property | Use |
| --- | --- |
| `rdfs:label` |  |
| `rdsf:comment` |  |
| `dcterms:description` |  |
| `schema:name` |  |
| `skos:altLabel` |  |

# Data for All Repositories

Recommended additions to most repositories in addition to data:
- [us_admin-region_class-statements.zip](https://drive.google.com/file/d/1xM81w-Pxz8bFFKjpwD_oKzHtS1KqhxST/view?usp=drive_link)
- [us_s2-l13_class-statements.zip](https://drive.google.com/file/d/1vRoccOEJjwoeLYHGeUec86W3VsHp9JG9/view?usp=drive_link)
- [sawgraph-spatial-ontology.ttl](https://github.com/SAWGraph/geospatial-kg/blob/main/ontologies/sawgraph-spatial-ontology.ttl)

# Current Namespaces:
| Prefix | Namespace | Notes |
| --- | --- | --- |
| co_cgs | <http://sawgraph.spatial.org/v1/co-cgs#> |  |
| co_cgs_data | <http://sawgraph.spatial.org/v1/co-cgs-data#> |  |
| coso | <http://w3id.org/coso/v1/contaminoso#> |  |
| dc | <http://purl.org/dc/elements/1.1/> |  |
| dcgeoid | <https://datacommons.org/browser/geoId/> |  |
| dcterms | <http://purl.org/dc/terms/> | sawgraph-spatial-ontology.ttl uses `terms:` |
| epa_frs | <http://w3id.org/fio/v1/epa-frs#> |  |
| epa_frs_data | <http://w3id.org/fio/v1/epa-frs-data#> |  |
| example | <http://example.com/0000003> |  |
| fio-pfas | <http://w3id.org/fio/v1/pfas#> |  |
| fio | <http://w3id.org/fio/v1/fio#> |  |
| gcx | <https://geoconnex.us/> |  |
| gcx_cid | <https://geoconnex.us/nhdplusv2/comid/> | This is temporary and will likely change |
| gcx_ms | <https://geoconnex.us/ref/mainstems/> |  |
| geo | <http://www.opengis.net/ont/geosparql#> |  |
| gsmlb | <http://geosciml.org/def/gsmlb#> |  |
| gwml2 | <http://gwml2.org/def/gwml2#> | This does not dereference; FRINK suggests gwml22: <http://www.opengis.net/gwml-main/2.2/>, which also does not dereference |
| hyf | <https://www.opengis.net/def/schema/hy_features/hyf/> | Per FRINK, there are 3 different prefixes: `hyf:`, `hyfa:`, and `hyfo:` |
| hyfo | <http://hyfo.spatialai.org/v1/hyfo#> | Per FRINK, this prefix is also used for HY_Features(?) |
| il_isgs | <http://sawgraph.spatialai.org/v1/il-isgs#> |  |
| il_isgs_data | <http://sawgraph.spatialai.org/v1/il-isgs-data#> |  |
| kwg-ont | <http://stko-kwg.geog.ucsb.edu/lod/ontology/> |  |
| kwgr | <http://stko-kwg.geog.ucsb.edu/lod/resource/> |  |
| me_egad | <http://w3id.org/sawgraph/v1/me-egad#> | previously `@prefix me_egad: <http://sawgraph.spatialai.org/v1/me-egad#>`  |
| me_egad_data | <http://w3id.org/sawgraph/v1/me-egad-data#> | previously `@prefix me_egad_data: <http://sawgraph.spatialai.org/v1/me-egad-data#>`  |
| me_mgs | <http://sawgraph.spatialai.org/v1/me-mgs#> |  |
| me_mgs_data | <http://sawgraph.spatialai.org/v1/me-mgs-data#> |  |
| naics | <http://w3id.org/fio/v1/naics#> | previously `@prefix naics: <http://sawgraph.spatialai.org/v1/fio/naics#>` |
| obo | <http://purl.obolibrary.org/obo/> |  |
| owl | <http://www.w3.org/2002/07/owl#> |  |
| pfas | <http://sawgraph.spatialai.org/v1/pfas#> |  |
| prov | <http://www.w3.org/ns/prov#> |  |
| psys | <http://proton.semanticweb.org/protonsys#> |  |
| quantitykind | <http://qudt.org/vocab/quantitykind/> |  |
| qudt | <http://qudt.org/schema/qudt/> |  |
| rdf | <http://www.w3.org/1999/02/22-rdf-syntax-ns#> |  |
| rdfs | <http://www.w3.org/2000/01/rdf-schema#> |  |
| saw_geo | <http://sawgraph.spatialai.org/v1/saw_geo#> |  |
| schema | <https://schema.org/> |  |
| sf | <http://www.opengis.net/ont/sf#> |  |
| skos | <http://www.w3.org/2004/02/skos/core#> |  |
| sosa | <http://www.w3.org/ns/sosa/> |  |
| spatial | <http://purl.org/spatialai/spatial/spatial-full#> |  |
| stad | <http://purl.org/spatialai/stad/v2/core/> |  |
| time | <http://www.w3.org/2006/time#> |  |
| unit | <http://qudt.org/vocab/unit/> |  |
| us_nhdplusv2 | <http://nhdplusv2.spatialai.org/v1/nhdplusv2#> |  |
| us_sdwis | <http://sawgraph.spatialai.org/v1/us-sdwis#> |  |
| us_wbd | <http://wbd.spatialai.org/v1/wbd#> |  |
| us_wbd_data | <http://wbd.spatialai.org/v1/wbd-data#> |  |
| usgs | <http://usgs.spatialai.org/v1/usgs#> |  |
| usgs_data | <http://usgs.spatialai.org/v1/usgs-data#> |  |
| usgwd | <http://w3id.org/hyfo/usgwd/v1/usgwd#> |  |
| vann | <http://purl.org/vocab/vann/> |  |
| wdt | <https://www.wikidata.org/prop/direct/> | See FRINK for additional wikidate prefixes/namespaces (18 in total) |
| xml | <http://www.w3.org/XML/1998/namespace> |  |
| xsd | <http://www.w3.org/2001/XMLSchema#> |  |

# Deprecated namespaces
| Prefix | Namespace | Notes |
| --- | --- | ---
| contaminoso | <http://sawgraph.spatialai.org/v1/contaminoso#> | Replaced by coso: |
| me_mgs | <http://sawgraph.spatialai.org/v1/me_mgs#> | This should be replaced wherever it is found (see the version above) |
| saw_water | <http://sawgraph.spatialai.org/v1/saw_water#> | Replaced by nhdplusv2 |
| us_frs | <http://sawgraph.spatialai.org/v1/us-frs#> | Replaced by epa_frs: |
| us_frs_data | <http://sawgraph.spatialai.org/v1/us-frs-data#> | Replaced by epa_frs_data: |
