# Flowchart Threads (Python + Tkinter)

A minimal editor and runtime for multi-threaded flowchart programs.

## Features
- Create/edit flowcharts (nodes + edges) in a Tkinter GUI
- Canvas diagram view with draggable nodes (positions saved in JSON)
- Save/load a JSON project file
- Validate structure and constraints
- Run N flowcharts as N threads with shared variables

## Quick Start

Run the GUI:

```powershell
python -m src.main
```

Run the runtime on a JSON file:

```powershell
python -m src.main --run examples/flowcharts.json
```

Generate Python source code from a JSON file:

```powershell
python -m src.main --run examples/flowcharts.json --emit generated_program.py
```

Run test set on a flowcharts JSON:

```powershell
python -m src.main --run examples/flowcharts.json --test examples/testset.json --max-steps 100
```

Report progress for executions with <= K steps:

```powershell
python -m src.main --run examples/flowcharts.json --test examples/testset.json --max-steps 100 --k 10
```

Stop test enumeration with Ctrl+C to enter K (1..20) and get progress for executions
with <= K operations.

## JSON Format (flowcharts.json)

Top-level shape:

```json
{
  "flowcharts": [
    {
      "id": "T1",
      "variables": ["X", "Y"],
      "nodes": [
        {"id": "n1", "type": "START"},
        {"id": "n2", "type": "INPUT", "params": {"dst": "X"}},
        {"id": "n3", "type": "END"}
      ],
      "edges": [
        {"from": "n1", "to": "n2"},
        {"from": "n2", "to": "n3"}
      ]
    }
  ]
}
```

Node types and params:
- START, END (no params)
- ASSIGN_VAR_VAR: {"dst": "V1", "src": "V2"}
- ASSIGN_VAR_CONST: {"dst": "V", "value": 123}
- INPUT: {"dst": "V"}
- PRINT: {"src": "V"}
- BRANCH: {"op": "=="|"<", "left": "V", "right": 123}
  - Requires two outgoing edges with labels "true" and "false"

Optional node layout fields:
- Each node may include a "pos" object: {"x": 100, "y": 80}

Constraints:
- 1 <= number of flowcharts <= 100
- Each flowchart has up to 100 nodes
- Up to 100 shared variables per flowchart
- Constants: 0..2^31-1

## Notes
- Shared variables are 32-bit integers; updates are synchronized with a lock.
- INPUT is blocking per thread and uses a global input lock to avoid interleaved prompts.

## Test Set Format (testset.json)

```json
{
  "tests": [
    {
      "id": "basic",
      "input": "5",
      "expected": "[Thread T2] PRINT: 1\n[Thread T1] PRINT: 5"
    }
  ]
}
```

Notes:
- `input` is whitespace-separated integers for INPUT operations.
- `expected` can be a string or a list of strings for nondeterministic outputs.

