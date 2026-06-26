# Tester Demo Guide

Project:
HL7 FHIR-Based Personal Health Knowledge Graph and Intelligent SPARQL Query System Using OWL Ontologies

This guide explains how a tester can install, run, and verify the project demo.

## 1. Open the Project Folder

Open a terminal or command prompt in:

```powershell
TSW_project\source_code
```

The folder should contain:

```text
fhir_kg_system.py
gui_app.py
test_fhir_kg_system.py
requirements.txt
data\fhir
```

## 2. Install Dependencies

Run:

```powershell
pip install -r requirements.txt
```

The main required library is:

```text
rdflib
```

RDFLib is used to build the RDF graph, define RDFS/OWL statements, serialize Turtle output, and execute SPARQL queries.

## 3. Run the Command-Line Demo

Run:

```powershell
python fhir_kg_system.py
```

Expected behavior:

1. The program loads synthetic HL7 FHIR R4 JSON bundles from `data\fhir`.
2. It converts supported FHIR resources into RDF triples.
3. It creates RDFS/OWL classes and properties.
4. It applies rule-based inference for `RiskPatient`.
5. It runs predefined SPARQL queries.
6. It saves output files in:

```text
..\output
```

Expected output files:

```text
..\output\personal_health_kg.ttl
..\output\query_results.txt
```

`personal_health_kg.ttl` contains the generated RDF/RDFS/OWL Turtle knowledge graph.

`query_results.txt` contains readable SPARQL query results.

## 4. Run the GUI Demo

Run:

```powershell
python gui_app.py
```

Expected behavior:

1. A desktop GUI window opens.
2. The graph summary shows the FHIR folder and total RDF triple count.
3. The tester can choose a predefined question from the dropdown list.
4. Clicking `Run Query` displays the SPARQL result in a table.
5. Clicking `Run All Demo Queries` saves all query results to:

```text
..\output\query_results.txt
```

6. Clicking `Show RDF / Turtle` previews the generated Turtle knowledge graph.

## 5. Suggested Demo Flow for Tester

Use this flow during evaluation:

1. Run `python fhir_kg_system.py`.
2. Confirm that the terminal shows the graph was created and query results were printed.
3. Open `..\output\personal_health_kg.ttl` to confirm RDF triples exist.
4. Open `..\output\query_results.txt` to confirm SPARQL results exist.
5. Run `python gui_app.py`.
6. In the GUI, test these questions:

```text
What conditions does the patient have?
Show observations.
Which patient has risk?
What care recommendation is available?
Show immunization records
Show medication records
```

7. Click `Show RDF / Turtle` to demonstrate that the table results are backed by a generated RDF knowledge graph.

## 6. Run Basic Functional Tests

Run:

```powershell
python test_fhir_kg_system.py
```

Expected result:

```text
All tests passed.
```

The tests verify that:

1. Patient condition queries return results.
2. Observation queries return values.
3. Immunization queries return values.
4. Risk patient inference runs without error.

## 7. What the Demo Proves

This project demonstrates the selected Semantic Web Technology topics:

Category 2: RDF, RDFS, and SPARQL

- FHIR JSON records are transformed into RDF triples.
- RDFS schema statements define labels, domains, ranges, and subclass relationships.
- SPARQL queries retrieve patient conditions, observations, care plans, immunizations, medications, and risk patients.

Category 3: OWL ontology and inference

- OWL classes, object properties, and datatype properties are created.
- A rule-based inference step classifies selected patients as `RiskPatient`.

## 8. Troubleshooting

If this error appears:

```text
ModuleNotFoundError: No module named 'rdflib'
```

Run:

```powershell
pip install -r requirements.txt
```

If the GUI does not open, make sure Python includes Tkinter support. Most standard Windows Python installations include Tkinter by default.

If no output folder exists before running the demo, this is normal. The program creates:

```text
..\output
```

automatically when the command-line demo or GUI runs.
