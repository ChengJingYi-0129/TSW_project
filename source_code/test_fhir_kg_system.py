from pathlib import Path

from fhir_kg_system import (
    apply_simple_inference,
    create_graph_from_folder,
    query_conditions,
    query_immunizations,
    query_observations,
    query_risk_patients,
)


BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data" / "fhir"


def build_graph():
    graph = create_graph_from_folder(DATA_FOLDER)
    apply_simple_inference(graph)
    return graph


def test_graph_has_patient_conditions() -> None:
    graph = build_graph()
    rows = query_conditions(graph)
    assert rows


def test_observation_query_returns_values() -> None:
    graph = build_graph()
    rows = query_observations(graph)
    assert rows


def test_immunization_query_returns_values() -> None:
    graph = build_graph()
    rows = query_immunizations(graph)
    assert rows


def test_inference_runs() -> None:
    graph = build_graph()
    risk_patients = query_risk_patients(graph)
    assert isinstance(risk_patients, list)


if __name__ == "__main__":
    test_graph_has_patient_conditions()
    test_observation_query_returns_values()
    test_immunization_query_returns_values()
    test_inference_runs()
    print("All tests passed.")
