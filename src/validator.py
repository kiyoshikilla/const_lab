import json
from typing import Any, Dict, List

from .model import (
    BRANCH_OPS,
    MAX_CONST,
    MAX_FLOWCHARTS,
    MAX_NODES,
    MAX_VARIABLES,
    NODE_TYPES,
)


class ValidationError(Exception):
    pass


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def validate_project(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []

    if not isinstance(data, dict):
        return ["Project must be a JSON object"]

    flowcharts = data.get("flowcharts")

    if not isinstance(flowcharts, list):
        errors.append("flowcharts must be a list")
        return errors

    if len(flowcharts) < 1:
        errors.append("at least one flowchart is required")

    if len(flowcharts) > MAX_FLOWCHARTS:
        errors.append("flowcharts count exceeds 100")

    for chart in flowcharts:
        _validate_flowchart(chart, errors)

    return errors


def _validate_flowchart(chart: Dict[str, Any], errors: List[str]) -> None:
    if not isinstance(chart, dict):
        errors.append("flowchart must be an object")
        return

    chart_id = chart.get("id")
    if not isinstance(chart_id, str) or not chart_id:
        errors.append("flowchart id must be a non-empty string")

    variables = chart.get("variables")
    if not isinstance(variables, list):
        errors.append(f"flowchart {chart_id}: variables must be a list")
        variables = []

    if len(variables) > MAX_VARIABLES:
        errors.append(f"flowchart {chart_id}: variables count exceeds 100")

    var_set = set()
    for v in variables:
        if not isinstance(v, str) or not v:
            errors.append(f"flowchart {chart_id}: invalid variable name: {v}")
        elif v in var_set:
            errors.append(f"flowchart {chart_id}: duplicate variable name: {v}")
        var_set.add(v)

    nodes = chart.get("nodes")
    edges = chart.get("edges")

    if not isinstance(nodes, list):
        errors.append(f"flowchart {chart_id}: nodes must be a list")
        return

    if not isinstance(edges, list):
        errors.append(f"flowchart {chart_id}: edges must be a list")
        return

    if len(nodes) > MAX_NODES:
        errors.append(f"flowchart {chart_id}: nodes count exceeds 100")

    node_ids = set()
    start_count = 0
    for node in nodes:
        if not isinstance(node, dict):
            errors.append(f"flowchart {chart_id}: node must be an object")
            continue
        node_id = node.get("id")
        node_type = node.get("type")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"flowchart {chart_id}: node id is invalid")
        elif node_id in node_ids:
            errors.append(f"flowchart {chart_id}: duplicate node id {node_id}")
        node_ids.add(node_id)

        if node_type not in NODE_TYPES:
            errors.append(f"flowchart {chart_id}: invalid node type {node_type}")
            continue
        if node_type == "START":
            start_count += 1

        params = node.get("params") or {}
        if not isinstance(params, dict):
            errors.append(f"flowchart {chart_id}: params must be an object")
            continue
        _validate_node_params(chart_id, node_type, params, var_set, errors)

    if start_count != 1:
        errors.append(f"flowchart {chart_id}: must have exactly one START node")

    for edge in edges:
        if not isinstance(edge, dict):
            errors.append(f"flowchart {chart_id}: edge must be an object")
            continue
        src = edge.get("from")
        dst = edge.get("to")
        if src not in node_ids:
            errors.append(f"flowchart {chart_id}: edge from invalid node {src}")
        if dst not in node_ids:
            errors.append(f"flowchart {chart_id}: edge to invalid node {dst}")

    # Branch nodes must have true/false edges
    branch_ids = [n.get("id") for n in nodes if isinstance(n, dict) and n.get("type") == "BRANCH"]
    edge_labels = {}
    for edge in edges:
        src = edge.get("from")
        label = edge.get("label")
        if src not in edge_labels:
            edge_labels[src] = []
        edge_labels[src].append(label)

    for branch_id in branch_ids:
        labels = edge_labels.get(branch_id, [])
        if sorted(labels) != ["false", "true"]:
            errors.append(
                f"flowchart {chart_id}: BRANCH {branch_id} must have edges labeled true/false"
            )


def _validate_node_params(
    chart_id: str,
    node_type: str,
    params: Dict[str, Any],
    var_set: set,
    errors: List[str],
) -> None:
    if node_type == "ASSIGN_VAR_VAR":
        _require_var(chart_id, params, "dst", var_set, errors)
        _require_var(chart_id, params, "src", var_set, errors)
    elif node_type == "ASSIGN_VAR_CONST":
        _require_var(chart_id, params, "dst", var_set, errors)
        value = params.get("value")
        if not _is_int(value) or not (0 <= value <= MAX_CONST):
            errors.append(f"flowchart {chart_id}: invalid const value {value}")
    elif node_type == "INPUT":
        _require_var(chart_id, params, "dst", var_set, errors)
    elif node_type == "PRINT":
        _require_var(chart_id, params, "src", var_set, errors)
    elif node_type == "BRANCH":
        _require_var(chart_id, params, "left", var_set, errors)
        op = params.get("op")
        if op not in BRANCH_OPS:
            errors.append(f"flowchart {chart_id}: invalid branch op {op}")
        right = params.get("right")
        if not _is_int(right) or not (0 <= right <= MAX_CONST):
            errors.append(f"flowchart {chart_id}: invalid branch const {right}")


def _require_var(
    chart_id: str,
    params: Dict[str, Any],
    key: str,
    var_set: set,
    errors: List[str],
) -> None:
    value = params.get(key)
    if value not in var_set:
        errors.append(f"flowchart {chart_id}: param {key} must be an existing variable")


def load_json_file(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
