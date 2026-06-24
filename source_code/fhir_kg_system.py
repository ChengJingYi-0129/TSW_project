import json
import re
from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import RDF, RDFS, OWL, XSD


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_FOLDER = BASE_DIR / "data" / "fhir"
DEFAULT_OUTPUT_FOLDER = BASE_DIR.parent / "output"

EX = Namespace("http://example.org/healthkg/")
FHIR = Namespace("http://hl7.org/fhir/")
SNOMED = Namespace("http://snomed.info/id/")
LOINC = Namespace("http://loinc.org/rdf/")

PREFIXES = """
PREFIX ex: <http://example.org/healthkg/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""


def safe_id(value):
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(value))


def resource_uri(resource_type, resource_id):
    return EX[f"{resource_type}_{safe_id(resource_id)}"]


def patient_uri(patient_id):
    return resource_uri("Patient", patient_id)


def bind_namespaces(graph):
    graph.bind("ex", EX)
    graph.bind("fhir", FHIR)
    graph.bind("snomed", SNOMED)
    graph.bind("loinc", LOINC)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("owl", OWL)
    graph.bind("xsd", XSD)


def create_ontology(graph):
    classes = {
        EX.Patient: "Patient",
        EX.Condition: "Condition",
        EX.ChronicCondition: "Chronic Condition",
        EX.Observation: "Observation",
        EX.CarePlan: "Care Plan",
        EX.Immunization: "Immunization",
        EX.Medication: "Medication",
        EX.Encounter: "Encounter",
        EX.RiskPatient: "Risk Patient",
        EX.MedicalCode: "Medical Code",
    }

    for cls, label in classes.items():
        graph.add((cls, RDF.type, OWL.Class))
        graph.add((cls, RDF.type, RDFS.Class))
        graph.add((cls, RDFS.label, Literal(label)))

    graph.add((EX.ChronicCondition, RDFS.subClassOf, EX.Condition))
    graph.add((EX.RiskPatient, RDFS.subClassOf, EX.Patient))

    object_properties = {
        EX.hasCondition: (EX.Patient, EX.Condition, "has condition"),
        EX.hasObservation: (EX.Patient, EX.Observation, "has observation"),
        EX.hasCarePlan: (EX.Patient, EX.CarePlan, "has care plan"),
        EX.hasImmunization: (EX.Patient, EX.Immunization, "has immunization"),
        EX.hasMedication: (EX.Patient, EX.Medication, "has medication"),
        EX.hasEncounter: (EX.Patient, EX.Encounter, "has encounter"),
        EX.hasCode: (OWL.Thing, EX.MedicalCode, "has medical code"),
    }

    for prop, (domain, range_, label) in object_properties.items():
        graph.add((prop, RDF.type, OWL.ObjectProperty))
        graph.add((prop, RDFS.domain, domain))
        graph.add((prop, RDFS.range, range_))
        graph.add((prop, RDFS.label, Literal(label)))

    data_properties = {
        EX.name: (EX.Patient, XSD.string, "name"),
        EX.gender: (EX.Patient, XSD.string, "gender"),
        EX.birthDate: (EX.Patient, XSD.date, "birth date"),
        EX.status: (OWL.Thing, XSD.string, "status"),
        EX.label: (OWL.Thing, XSD.string, "label"),
        EX.value: (EX.Observation, XSD.string, "value"),
        EX.unit: (EX.Observation, XSD.string, "unit"),
        EX.date: (OWL.Thing, XSD.string, "date"),
        EX.recommendation: (EX.CarePlan, XSD.string, "recommendation"),
        EX.codeSystem: (EX.MedicalCode, XSD.anyURI, "code system"),
        EX.codeValue: (EX.MedicalCode, XSD.string, "code value"),
    }

    for prop, (domain, range_, label) in data_properties.items():
        graph.add((prop, RDF.type, OWL.DatatypeProperty))
        graph.add((prop, RDFS.domain, domain))
        graph.add((prop, RDFS.range, range_))
        graph.add((prop, RDFS.label, Literal(label)))


def load_bundles_from_folder(data_folder):
    folder = Path(data_folder)
    bundles = []
    for json_file in sorted(folder.glob("*.json")):
        bundles.append(json.loads(json_file.read_text(encoding="utf-8")))
    return bundles


def build_reference_map(bundles):
    reference_map = {}
    for bundle in bundles:
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            if not resource_type or not resource_id:
                continue

            uri = resource_uri(resource_type, resource_id)
            reference_map[f"{resource_type}/{resource_id}"] = uri
            if entry.get("fullUrl"):
                reference_map[entry["fullUrl"]] = uri

    return reference_map


def fhir_reference_to_uri(reference, reference_map=None):
    if not reference:
        return None
    if reference_map and reference in reference_map:
        return reference_map[reference]
    if "/" in reference:
        resource_type, resource_id = reference.split("/", 1)
        return resource_uri(resource_type, resource_id)
    if reference.startswith("urn:uuid:"):
        return EX[f"Resource_{safe_id(reference.replace('urn:uuid:', ''))}"]
    return EX[f"Resource_{safe_id(reference)}"]


def full_patient_name(patient):
    name = patient.get("name", [{}])[0]
    given = " ".join(name.get("given", []))
    family = name.get("family", "")
    return f"{given} {family}".strip() or patient.get("id", "Unknown patient")


def first_coding(resource):
    code_block = resource.get("code", {})
    coding = code_block.get("coding", [])
    if coding:
        return coding[0]
    return {"system": "", "code": "unknown", "display": code_block.get("text", "Unknown code")}


def code_text(resource):
    code_block = resource.get("code", {})
    return code_block.get("text") or first_coding(resource).get("display") or "Unknown"


def coding_uri(coding):
    system = coding.get("system", "")
    code = safe_id(coding.get("code", "unknown"))
    if "snomed" in system.lower():
        return SNOMED[code]
    if "loinc" in system.lower():
        return LOINC[code]
    return EX[f"Code_{code}"]


def add_code(graph, subject, coding, fallback_label):
    code_node = coding_uri(coding)
    graph.add((code_node, RDF.type, EX.MedicalCode))
    graph.add((code_node, RDFS.label, Literal(coding.get("display") or fallback_label)))
    graph.add((code_node, EX.codeSystem, Literal(coding.get("system", ""), datatype=XSD.anyURI)))
    graph.add((code_node, EX.codeValue, Literal(coding.get("code", ""))))
    graph.add((subject, EX.hasCode, code_node))
    return code_node


def status_text(resource):
    if isinstance(resource.get("clinicalStatus"), dict):
        clinical_status = resource["clinicalStatus"]
        if clinical_status.get("text"):
            return clinical_status["text"]
        return " ".join(coding.get("code", "") for coding in clinical_status.get("coding", []))
    return resource.get("status", "")


def add_if_not_none(graph, triple):
    if all(value is not None for value in triple):
        graph.add(triple)


def clean_html_label(value, fallback):
    label = str(value or fallback)
    label = label.replace('<div xmlns="http://www.w3.org/1999/xhtml">', "")
    label = label.replace("</div>", "")
    return label.split("<br/>")[0].strip() or fallback


def process_bundle(graph, bundle, reference_map=None):
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            continue

        try:
            if resource_type == "Patient":
                patient = patient_uri(resource_id)
                graph.add((patient, RDF.type, EX.Patient))
                graph.add((patient, RDFS.label, Literal(full_patient_name(resource))))
                graph.add((patient, EX.name, Literal(full_patient_name(resource))))
                graph.add((patient, EX.gender, Literal(resource.get("gender", ""))))
                graph.add((patient, EX.birthDate, Literal(resource.get("birthDate", ""))))

            elif resource_type == "Condition":
                patient = fhir_reference_to_uri(resource.get("subject", {}).get("reference"), reference_map)
                condition = resource_uri("Condition", resource_id)
                label = code_text(resource)

                graph.add((condition, RDF.type, EX.Condition))
                if any(term in label.lower() for term in ["diabetes", "hypertension", "asthma", "obesity", "prediabetes"]):
                    graph.add((condition, RDF.type, EX.ChronicCondition))
                graph.add((condition, RDFS.label, Literal(label)))
                graph.add((condition, EX.label, Literal(label)))
                graph.add((condition, EX.status, Literal(status_text(resource))))
                add_if_not_none(graph, (patient, EX.hasCondition, condition))
                add_code(graph, condition, first_coding(resource), label)

            elif resource_type == "Observation":
                patient = fhir_reference_to_uri(resource.get("subject", {}).get("reference"), reference_map)
                observation = resource_uri("Observation", resource_id)
                label = code_text(resource)

                graph.add((observation, RDF.type, EX.Observation))
                graph.add((observation, RDFS.label, Literal(label)))
                graph.add((observation, EX.label, Literal(label)))

                value_quantity = resource.get("valueQuantity")
                if value_quantity:
                    graph.add((observation, EX.value, Literal(value_quantity.get("value", ""))))
                    graph.add((observation, EX.unit, Literal(value_quantity.get("unit", ""))))
                elif "valueString" in resource:
                    graph.add((observation, EX.value, Literal(resource.get("valueString", ""))))
                    graph.add((observation, EX.unit, Literal("")))
                elif "valueCodeableConcept" in resource:
                    graph.add((observation, EX.value, Literal(resource["valueCodeableConcept"].get("text", ""))))
                    graph.add((observation, EX.unit, Literal("")))
                elif "component" in resource:
                    values = []
                    for component in resource["component"]:
                        quantity = component.get("valueQuantity", {})
                        value = quantity.get("value")
                        unit = quantity.get("unit", "")
                        if value is not None:
                            values.append(f"{value} {unit}".strip())
                    graph.add((observation, EX.value, Literal(" / ".join(values))))
                    graph.add((observation, EX.unit, Literal("")))
                else:
                    graph.add((observation, EX.value, Literal("")))
                    graph.add((observation, EX.unit, Literal("")))

                graph.add((observation, EX.date, Literal(resource.get("effectiveDateTime", ""))))
                add_if_not_none(graph, (patient, EX.hasObservation, observation))
                add_code(graph, observation, first_coding(resource), label)

            elif resource_type == "MedicationRequest":
                patient = fhir_reference_to_uri(resource.get("subject", {}).get("reference"), reference_map)
                medication = resource_uri("Medication", resource_id)
                label = resource.get("medicationCodeableConcept", {}).get("text", "Medication")

                graph.add((medication, RDF.type, EX.Medication))
                graph.add((medication, RDFS.label, Literal(label)))
                graph.add((medication, EX.label, Literal(label)))
                graph.add((medication, EX.status, Literal(resource.get("status", ""))))
                add_if_not_none(graph, (patient, EX.hasMedication, medication))

            elif resource_type == "CarePlan":
                patient = fhir_reference_to_uri(resource.get("subject", {}).get("reference"), reference_map)
                careplan = resource_uri("CarePlan", resource_id)
                label = resource.get("title") or resource.get("description")
                if not label and resource.get("category"):
                    label = resource["category"][0].get("text")
                if not label:
                    label = resource.get("text", {}).get("div", "CarePlan")
                label = clean_html_label(label, "CarePlan")

                graph.add((careplan, RDF.type, EX.CarePlan))
                graph.add((careplan, RDFS.label, Literal(label)))
                graph.add((careplan, EX.label, Literal(label)))
                graph.add((careplan, EX.status, Literal(resource.get("status", ""))))

                activities = []
                for activity in resource.get("activity", []):
                    text = activity.get("detail", {}).get("code", {}).get("text")
                    if text:
                        activities.append(text)
                graph.add((careplan, EX.recommendation, Literal(" | ".join(activities) if activities else label)))
                add_if_not_none(graph, (patient, EX.hasCarePlan, careplan))

            elif resource_type == "Immunization":
                patient = fhir_reference_to_uri(resource.get("patient", {}).get("reference"), reference_map)
                immunization = resource_uri("Immunization", resource_id)
                vaccine = resource.get("vaccineCode", {}).get("text", "Unknown Vaccine")

                graph.add((immunization, RDF.type, EX.Immunization))
                graph.add((immunization, RDFS.label, Literal(vaccine)))
                graph.add((immunization, EX.label, Literal(vaccine)))
                graph.add((immunization, EX.date, Literal(resource.get("occurrenceDateTime", ""))))
                add_if_not_none(graph, (patient, EX.hasImmunization, immunization))

            elif resource_type == "Encounter":
                patient = fhir_reference_to_uri(resource.get("subject", {}).get("reference"), reference_map)
                encounter = resource_uri("Encounter", resource_id)
                label = "Encounter"
                if resource.get("type"):
                    label = resource["type"][0].get("text", label)

                graph.add((encounter, RDF.type, EX.Encounter))
                graph.add((encounter, RDFS.label, Literal(label)))
                graph.add((encounter, EX.label, Literal(label)))
                graph.add((encounter, EX.status, Literal(resource.get("status", ""))))
                add_if_not_none(graph, (patient, EX.hasEncounter, encounter))

        except (KeyError, TypeError, ValueError):
            continue


def create_graph_from_folder(data_folder=DEFAULT_DATA_FOLDER):
    graph = Graph()
    bind_namespaces(graph)
    create_ontology(graph)

    bundles = load_bundles_from_folder(data_folder)
    reference_map = build_reference_map(bundles)
    for bundle in bundles:
        process_bundle(graph, bundle, reference_map)
    return graph


def create_graph_from_fhir(fhir_file):
    graph = Graph()
    bind_namespaces(graph)
    create_ontology(graph)

    bundle = json.loads(Path(fhir_file).read_text(encoding="utf-8"))
    reference_map = build_reference_map([bundle])
    process_bundle(graph, bundle, reference_map)
    return graph


def run_query(graph, query):
    return graph.query(PREFIXES + query)


def glucose_is_high(value, unit):
    try:
        number = float(str(value).split()[0])
    except (TypeError, ValueError):
        return False
    unit_text = str(unit).lower()
    if "mmol" in unit_text:
        return number >= 7.0
    return number >= 126


def apply_simple_inference(graph):
    patient_query = """
    SELECT ?patient WHERE {
        ?patient rdf:type ex:Patient .
    }
    """

    for row in run_query(graph, patient_query):
        patient = row.patient

        condition_query = f"""
        SELECT ?label WHERE {{
            <{patient}> ex:hasCondition ?condition .
            ?condition ex:label ?label .
        }}
        """
        condition_labels = [str(item.label).lower() for item in run_query(graph, condition_query)]
        has_diabetes = any("diabetes" in label for label in condition_labels)
        has_hypertension = any("hypertension" in label for label in condition_labels)

        glucose_query = f"""
        SELECT ?value ?unit WHERE {{
            <{patient}> ex:hasObservation ?observation .
            ?observation ex:label ?label .
            ?observation ex:value ?value .
            OPTIONAL {{ ?observation ex:unit ?unit . }}
            FILTER(CONTAINS(LCASE(STR(?label)), "glucose"))
        }}
        """
        has_high_glucose = any(glucose_is_high(item.value, item.unit) for item in run_query(graph, glucose_query))

        if (has_diabetes and has_hypertension) or has_high_glucose:
            graph.add((patient, RDF.type, EX.RiskPatient))


def format_result(value):
    if value is None:
        return ""
    return str(value).replace(str(EX), "ex:")


def rows_from_query(graph, query, fields):
    return [[format_result(getattr(row, field)) for field in fields] for row in run_query(graph, query)]


def query_conditions(graph, limit=300):
    query = f"""
    SELECT ?patientName ?conditionLabel WHERE {{
        ?patient rdf:type ex:Patient .
        ?patient ex:name ?patientName .
        ?patient ex:hasCondition ?condition .
        ?condition ex:label ?conditionLabel .
    }}
    ORDER BY ?patientName ?conditionLabel
    LIMIT {limit}
    """
    return rows_from_query(graph, query, ["patientName", "conditionLabel"])


def query_observations(graph, limit=300):
    query = f"""
    SELECT ?patientName ?label ?value ?unit ?date WHERE {{
        ?patient ex:name ?patientName .
        ?patient ex:hasObservation ?observation .
        ?observation ex:label ?label .
        OPTIONAL {{ ?observation ex:value ?value . }}
        OPTIONAL {{ ?observation ex:unit ?unit . }}
        OPTIONAL {{ ?observation ex:date ?date . }}
    }}
    ORDER BY ?patientName ?label
    LIMIT {limit}
    """
    return rows_from_query(graph, query, ["patientName", "label", "value", "unit", "date"])


def query_risk_patients(graph):
    query = """
    SELECT ?patientName WHERE {
        ?patient rdf:type ex:RiskPatient .
        ?patient ex:name ?patientName .
    }
    ORDER BY ?patientName
    """
    return rows_from_query(graph, query, ["patientName"])


def query_careplan(graph, limit=300):
    query = f"""
    SELECT ?patientName ?label ?recommendation WHERE {{
        ?patient ex:name ?patientName .
        ?patient ex:hasCarePlan ?careplan .
        ?careplan ex:label ?label .
        OPTIONAL {{ ?careplan ex:recommendation ?recommendation . }}
    }}
    ORDER BY ?patientName
    LIMIT {limit}
    """
    return rows_from_query(graph, query, ["patientName", "label", "recommendation"])


def query_immunizations(graph, limit=300):
    query = f"""
    SELECT ?patientName ?vaccine ?date WHERE {{
        ?patient ex:name ?patientName .
        ?patient ex:hasImmunization ?immunization .
        ?immunization ex:label ?vaccine .
        OPTIONAL {{ ?immunization ex:date ?date . }}
    }}
    ORDER BY ?patientName ?date
    LIMIT {limit}
    """
    return rows_from_query(graph, query, ["patientName", "vaccine", "date"])


def query_medications(graph, limit=300):
    query = f"""
    SELECT ?patientName ?medication ?status WHERE {{
        ?patient ex:name ?patientName .
        ?patient ex:hasMedication ?medicationNode .
        ?medicationNode ex:label ?medication .
        OPTIONAL {{ ?medicationNode ex:status ?status . }}
    }}
    ORDER BY ?patientName ?medication
    LIMIT {limit}
    """
    return rows_from_query(graph, query, ["patientName", "medication", "status"])


def ask_question(graph, question):
    question = question.lower()
    if "condition" in question or "disease" in question:
        return "Conditions", ["Patient", "Condition"], query_conditions(graph)
    if "observation" in question or "glucose" in question or "steps" in question:
        return "Observations", ["Patient", "Observation", "Value", "Unit", "Date"], query_observations(graph)
    if "risk" in question:
        return "Risk Patients", ["Patient"], query_risk_patients(graph)
    if "care" in question or "recommend" in question:
        return "Care Plan", ["Patient", "Care Plan", "Recommendation"], query_careplan(graph)
    if "immunization" in question or "vaccine" in question or "immune" in question:
        return "Immunizations", ["Patient", "Vaccine", "Date"], query_immunizations(graph)
    if "medication" in question or "medicine" in question or "drug" in question:
        return "Medications", ["Patient", "Medication", "Status"], query_medications(graph)
    return "Conditions", ["Patient", "Condition"], query_conditions(graph)


def print_table(headers, rows):
    if not rows:
        print("No results found.")
        return

    widths = []
    for index, header in enumerate(headers):
        values = [str(row[index]) for row in rows]
        widths.append(max([len(header)] + [len(value) for value in values]))

    line = "-+-".join("-" * width for width in widths)
    print(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print(line)
    for row in rows:
        print(" | ".join(str(row[i]).ljust(widths[i]) for i in range(len(headers))))


def run_demo():
    DEFAULT_OUTPUT_FOLDER.mkdir(exist_ok=True, parents=True)

    print(f"Loading data from folder: {DEFAULT_DATA_FOLDER}")
    graph = create_graph_from_folder(DEFAULT_DATA_FOLDER)

    print("Applying inference...")
    apply_simple_inference(graph)

    graph.serialize(destination=DEFAULT_OUTPUT_FOLDER / "personal_health_kg.ttl", format="turtle")
    print(f"Graph saved. Total triples: {len(graph)}")

    questions = [
        "What conditions does the patient have?",
        "Show observations.",
        "Which patient has risk?",
        "What care recommendation is available?",
        "Show immunization records",
        "Show medication records",
    ]

    result_text = [
        "HL7 FHIR Personal Health Knowledge Graph Demo",
        f"FHIR input folder: {DEFAULT_DATA_FOLDER}",
        f"Total RDF triples: {len(graph)}",
        "",
    ]

    for question in questions:
        title, headers, rows = ask_question(graph, question)
        print("\nQuestion:", question)
        print("Query selected:", title)
        print_table(headers, rows)

        result_text.append("Question: " + question)
        result_text.append("Query selected: " + title)
        result_text.append("Headers: " + ", ".join(headers))
        for row in rows:
            result_text.append(" - " + " | ".join(row))
        result_text.append("")

    (DEFAULT_OUTPUT_FOLDER / "query_results.txt").write_text("\n".join(result_text), encoding="utf-8")


if __name__ == "__main__":
    run_demo()
