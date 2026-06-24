# HL7 FHIR Personal Health Knowledge Graph Demo

Project title:
Development of a HL7 FHIR-Based Personal Health Knowledge Graph and Intelligent SPARQL Query System Using OWL Ontologies

Selected Semantic Web topics:
- Category 2: RDF, RDFS, and SPARQL
- Category 3: OWL ontology and inference

## Dataset

The demo uses Synthea FHIR R4 synthetic EHR records stored in:

```powershell
data\fhir
```

Synthetic data is used because real EHR records contain sensitive patient information.

## Setup

Install dependencies:

```powershell
pip install -r requirements.txt
```

## How to Run

From this folder:

```powershell
python fhir_kg_system.py
```

For the GUI demo:

```powershell
python gui_app.py
```

Expected outputs:
- `..\output\personal_health_kg.ttl` - RDF/RDFS/OWL Turtle knowledge graph
- `..\output\query_results.txt` - SPARQL query result tables

The program demonstrates:
- Loading Synthea FHIR JSON patient bundles.
- Mapping Patient, Condition, Observation, MedicationRequest, CarePlan, Immunization, and Encounter resources into RDF triples.
- Defining OWL classes, object properties, and datatype properties.
- Defining RDFS subclass, domain, range, and label statements.
- Running real SPARQL queries over the RDFLib graph.
- Applying rule-based inference to classify RiskPatient individuals.
