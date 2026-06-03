import json
from typing import Any, Dict

from .validator import ValidationError, validate_project


def generate_python(data: Dict[str, Any]) -> str:
    errors = validate_project(data)
    if errors:
        raise ValidationError("\n".join(errors))

    data_json = json.dumps(data, ensure_ascii=True, indent=2)
    data_literal = repr(data_json)

    return f"""# Auto-generated from flowcharts.json
# 

import json
import threading

MAX_CONST = 2 ** 31 - 1
DATA = json.loads({data_literal})


class SharedState:
    def __init__(self, variables):
        self._lock = threading.Lock()
        self._vars = {{name: 0 for name in variables}}

    def read(self, name):
        with self._lock:
            return int(self._vars[name])

    def write(self, name, value):
        if value < 0 or value > MAX_CONST:
            raise ValueError(f"Value out of range: {{value}}")
        with self._lock:
            self._vars[name] = int(value)


class InputManager:
    def __init__(self):
        self._lock = threading.Lock()

    def read_int(self, thread_id):
        with self._lock:
            while True:
                raw = input(f"[Thread {{thread_id}}] INPUT> ").strip()
                try:
                    value = int(raw)
                except ValueError:
                    print("Enter an integer in range 0..2^31-1")
                    continue
                if 0 <= value <= MAX_CONST:
                    return value
                print("Value out of range 0..2^31-1")


class OutputManager:
    def __init__(self):
        self._lock = threading.Lock()

    def print_value(self, thread_id, value):
        with self._lock:
            print(f"[Thread {{thread_id}}] PRINT: {{value}}")


class FlowchartRunner(threading.Thread):
    def __init__(self, chart, shared, input_mgr, output_mgr, max_steps=None):
        super().__init__(daemon=False)
        self.chart = chart
        self.shared = shared
        self.input_mgr = input_mgr
        self.output_mgr = output_mgr
        self.max_steps = max_steps

        self.nodes = {{n["id"]: n for n in chart["nodes"]}}
        self.edges = chart["edges"]
        self.adj = self._build_adjacency()

    def _build_adjacency(self):
        adj = {{}}
        for edge in self.edges:
            src = edge["from"]
            adj.setdefault(src, []).append(edge)
        return adj

    def run(self):
        start_id = self._find_start_node()
        current = start_id
        steps = 0

        while current is not None:
            if self.max_steps is not None and steps >= self.max_steps:
                raise RuntimeError("Max steps exceeded")

            node = self.nodes[current]
            node_type = node["type"]
            params = node.get("params") or {{}}

            if node_type == "END":
                return
            elif node_type == "START":
                current = self._next_single(current)
            elif node_type == "ASSIGN_VAR_VAR":
                value = self.shared.read(params["src"])
                self.shared.write(params["dst"], value)
                current = self._next_single(current)
            elif node_type == "ASSIGN_VAR_CONST":
                self.shared.write(params["dst"], params["value"])
                current = self._next_single(current)
            elif node_type == "INPUT":
                value = self.input_mgr.read_int(self.chart["id"])
                self.shared.write(params["dst"], value)
                current = self._next_single(current)
            elif node_type == "PRINT":
                value = self.shared.read(params["src"])
                self.output_mgr.print_value(self.chart["id"], value)
                current = self._next_single(current)
            elif node_type == "BRANCH":
                left = self.shared.read(params["left"])
                op = params["op"]
                right = params["right"]
                result = (left == right) if op == "==" else (left < right)
                current = self._next_branch(current, result)
            else:
                raise RuntimeError(f"Unknown node type: {{node_type}}")

            steps += 1

    def _find_start_node(self):
        for node in self.chart["nodes"]:
            if node.get("type") == "START":
                return node["id"]
        raise RuntimeError("START node not found")

    def _next_single(self, node_id):
        edges = self.adj.get(node_id, [])
        if len(edges) != 1:
            raise RuntimeError(f"Node {{node_id}} must have exactly one outgoing edge")
        return edges[0]["to"]

    def _next_branch(self, node_id, predicate):
        edges = self.adj.get(node_id, [])
        label = "true" if predicate else "false"
        for edge in edges:
            if edge.get("label") == label:
                return edge["to"]
        raise RuntimeError(f"BRANCH {{node_id}} missing {{label}} edge")


def main():
    all_vars = []
    seen = set()
    for chart in DATA["flowcharts"]:
        for name in chart.get("variables", []):
            if name not in seen:
                seen.add(name)
                all_vars.append(name)

    shared = SharedState(all_vars)
    input_mgr = InputManager()
    output_mgr = OutputManager()

    threads = [
        FlowchartRunner(chart, shared, input_mgr, output_mgr)
        for chart in DATA["flowcharts"]
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
"""


def emit_python(path: str, data: Dict[str, Any]) -> None:
    code = generate_python(data)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
