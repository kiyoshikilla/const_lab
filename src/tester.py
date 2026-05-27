from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .model import MAX_CONST
from .validator import ValidationError, validate_project


@dataclass
class ThreadState:
    chart_id: str
    current: Optional[str]


@dataclass
class ExecResult:
    output_lines: List[str]
    steps: int


def _find_start_node(chart: Dict[str, Any]) -> str:
    for node in chart["nodes"]:
        if node.get("type") == "START":
            return node["id"]
    raise RuntimeError("START node not found")


def _build_adjacency(edges: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    adj: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        src = edge["from"]
        adj.setdefault(src, []).append(edge)
    return adj


def _step_thread(
    chart: Dict[str, Any],
    thread: ThreadState,
    shared: Dict[str, int],
    input_values: List[int],
    input_index: int,
    output_lines: List[str],
) -> Tuple[Optional[str], int]:
    nodes = {n["id"]: n for n in chart["nodes"]}
    adj = _build_adjacency(chart["edges"])

    node = nodes[thread.current]
    node_type = node["type"]
    params = node.get("params") or {}

    def next_single(node_id: str) -> str:
        edges = adj.get(node_id, [])
        if len(edges) != 1:
            raise RuntimeError(f"Node {node_id} must have exactly one outgoing edge")
        return edges[0]["to"]

    def next_branch(node_id: str, predicate: bool) -> str:
        edges = adj.get(node_id, [])
        label = "true" if predicate else "false"
        for edge in edges:
            if edge.get("label") == label:
                return edge["to"]
        raise RuntimeError(f"BRANCH {node_id} missing {label} edge")

    if node_type == "END":
        return None, input_index
    if node_type == "START":
        return next_single(thread.current), input_index
    if node_type == "ASSIGN_VAR_VAR":
        shared[params["dst"]] = int(shared[params["src"]])
        return next_single(thread.current), input_index
    if node_type == "ASSIGN_VAR_CONST":
        value = int(params["value"])
        if value < 0 or value > MAX_CONST:
            raise ValidationError(f"Value out of range: {value}")
        shared[params["dst"]] = value
        return next_single(thread.current), input_index
    if node_type == "INPUT":
        if input_index >= len(input_values):
            raise ValidationError("Not enough input values for INPUT operation")
        value = int(input_values[input_index])
        if value < 0 or value > MAX_CONST:
            raise ValidationError(f"Value out of range: {value}")
        shared[params["dst"]] = value
        return next_single(thread.current), input_index + 1
    if node_type == "PRINT":
        value = int(shared[params["src"]])
        output_lines.append(f"[Thread {thread.chart_id}] PRINT: {value}")
        return next_single(thread.current), input_index
    if node_type == "BRANCH":
        left = int(shared[params["left"]])
        op = params["op"]
        right = int(params["right"])
        result = (left == right) if op == "==" else (left < right)
        return next_branch(thread.current, result), input_index

    raise RuntimeError(f"Unknown node type: {node_type}")


def _init_shared_vars(data: Dict[str, Any]) -> Dict[str, int]:
    all_vars: Dict[str, int] = {}
    for chart in data["flowcharts"]:
        for name in chart.get("variables", []):
            all_vars.setdefault(name, 0)
    return all_vars


def iterate_executions(
    data: Dict[str, Any],
    input_values: List[int],
    max_steps: int,
    max_schedules: Optional[int] = None,
) -> Iterable[ExecResult]:
    errors = validate_project(data)
    if errors:
        raise ValidationError("\n".join(errors))

    charts = data["flowcharts"]
    threads = [ThreadState(chart_id=c["id"], current=_find_start_node(c)) for c in charts]
    shared = _init_shared_vars(data)

    seen = set()
    schedule_count = 0

    def make_state_key(
        threads_state: List[ThreadState],
        shared_state: Dict[str, int],
        input_index: int,
        output_lines: List[str],
    ) -> Tuple:
        return (
            tuple(t.current for t in threads_state),
            tuple(sorted(shared_state.items())),
            input_index,
            tuple(output_lines),
        )

    def dfs(
        threads_state: List[ThreadState],
        shared_state: Dict[str, int],
        input_index: int,
        output_lines: List[str],
        steps: int,
    ) -> Iterable[ExecResult]:
        nonlocal schedule_count
        if max_schedules is not None and schedule_count >= max_schedules:
            return

        state_key = make_state_key(threads_state, shared_state, input_index, output_lines)
        if state_key in seen:
            return
        seen.add(state_key)

        if all(t.current is None for t in threads_state):
            schedule_count += 1
            yield ExecResult(output_lines=list(output_lines), steps=steps)
            return
        if steps >= max_steps:
            return

        for idx, t in enumerate(threads_state):
            if t.current is None:
                continue
            new_threads = [ThreadState(chart_id=tt.chart_id, current=tt.current) for tt in threads_state]
            new_shared = dict(shared_state)
            new_output = list(output_lines)
            chart = charts[idx]
            try:
                new_current, new_input_index = _step_thread(
                    chart,
                    new_threads[idx],
                    new_shared,
                    input_values,
                    input_index,
                    new_output,
                )
            except ValidationError:
                continue
            new_threads[idx].current = new_current
            yield from dfs(new_threads, new_shared, new_input_index, new_output, steps + 1)

    yield from dfs(threads, shared, 0, [], 0)


def enumerate_executions(
    data: Dict[str, Any],
    input_values: List[int],
    max_steps: int,
    max_schedules: Optional[int] = None,
) -> Tuple[List[ExecResult], int]:
    results = list(iterate_executions(data, input_values, max_steps, max_schedules))
    return results, len(results)


def count_executions(
    data: Dict[str, Any],
    input_values: List[int],
    max_steps: int,
) -> int:
    count = 0
    for _ in iterate_executions(data, input_values, max_steps=max_steps, max_schedules=None):
        count += 1
    return count


def parse_input_values(raw: str) -> List[int]:
    raw = raw.strip()
    if not raw:
        return []
    return [int(x) for x in raw.split()]


def normalize_expected(expected: Any) -> List[str]:
    if isinstance(expected, list):
        return [str(x) for x in expected]
    return [str(expected)]


def run_testset(
    data: Dict[str, Any],
    testset: Dict[str, Any],
    max_steps: int,
    max_schedules: Optional[int],
    k_limit: Optional[int],
) -> int:
    tests = testset.get("tests", [])
    if not isinstance(tests, list):
        raise ValidationError("testset must contain a list of tests")

    passed = 0
    for test in tests:
        test_id = test.get("id", "(no id)")
        raw_input = test.get("input", "")
        expected = normalize_expected(test.get("expected", ""))
        input_values = parse_input_values(raw_input)

        unexpected = 0
        checked = 0
        checked_steps: List[int] = []

        try:
            for res in iterate_executions(
                data,
                input_values,
                max_steps=max_steps,
                max_schedules=max_schedules,
            ):
                checked += 1
                checked_steps.append(res.steps)
                output_text = "\n".join(res.output_lines)
                if output_text not in expected:
                    unexpected += 1
        except KeyboardInterrupt:
            print("\nTest interrupted by user.")
            k = _prompt_k()
            _print_k_progress(data, input_values, checked_steps, k)
            return 0

        if checked == 0:
            print(f"Test {test_id}: no completed executions within max_steps")
            continue

        if unexpected:
            print(f"Test {test_id}: FAIL ({unexpected} unexpected outputs)")
        else:
            print(f"Test {test_id}: OK ({checked} executions)")
            passed += 1

        if k_limit is not None:
            _print_k_progress(data, input_values, checked_steps, k_limit)

    return 0 if passed == len(tests) else 1


def _prompt_k() -> int:
    while True:
        raw = input("Enter K (1..20): ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Enter an integer.")
            continue
        if 1 <= value <= 20:
            return value
        print("K must be in range 1..20")


def _print_k_progress(
    data: Dict[str, Any],
    input_values: List[int],
    checked_steps: List[int],
    k: int,
) -> None:
    if k < 1 or k > 20:
        print("K must be in range 1..20")
        return
    total_k = count_executions(data, input_values, max_steps=k)
    checked_k = sum(1 for s in checked_steps if s <= k)
    if total_k == 0:
        print(f"No executions complete within <= {k} steps.")
        return
    percent = (checked_k / total_k) * 100
    print(
        f"Checked {checked_k}/{total_k} executions with <= {k} steps "
        f"({percent:.2f}%)."
    )
