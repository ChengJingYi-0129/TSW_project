# HL7 FHIR Personal Health Knowledge Graph

A semantic-web prototype that transforms synthetic HL7 FHIR R4 health records into an RDF/OWL knowledge graph, supports SPARQL queries, and applies rule-based inference to identify higher-risk patients.

> The project uses Synthea synthetic data only. No real patient records are included.

## Highlights

- Maps FHIR resources into RDF triples
- Models health concepts with RDF, RDFS, and OWL
- Runs SPARQL queries over an RDFLib graph
- Applies rule-based inference to classify `RiskPatient` individuals
- Includes a GUI demonstration workflow

## Technology

- Python
- RDFLib
- HL7 FHIR R4
- RDF / RDFS / OWL
- SPARQL
- Synthea synthetic EHR data

## Run Locally

```bash
pip install -r requirements.txt
python fhir_kg_system.py
```

To launch the GUI demo:

```bash
python gui_app.py
```

## Outputs

- `output/personal_health_kg.ttl` — generated knowledge graph
- `output/query_results.txt` — SPARQL query results

## FHIR Coverage

The graph maps Patient, Condition, Observation, MedicationRequest, CarePlan, Immunization, and Encounter resources.

## Project Context

An academic Semantic Web project demonstrating how interoperable health-data standards and ontology-based reasoning can support structured analysis without exposing real patient information.