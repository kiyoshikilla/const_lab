import tkinter as tk
from typing import Dict, Optional, Tuple
from tkinter import filedialog, messagebox, ttk

from .validator import load_json_file, save_json_file, validate_project
from .model import BRANCH_OPS, MAX_CONST, MAX_FLOWCHARTS, MAX_NODES, MAX_VARIABLES, NODE_TYPES


class FlowchartEditor(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Flowchart Threads Editor")
        self.geometry("1100x650")

        self.data = {
            "flowcharts": [],
        }

        self._canvas_nodes: Dict[str, Tuple[int, int]] = {}
        self._canvas_edges = []
        self._drag_node_id: Optional[str] = None
        self._drag_offset = (0, 0)
        self._selected_flowchart_idx: Optional[int] = None
        self._selected_node_id: Optional[str] = None

        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="New flowchart", command=self._new_flowchart).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Open", command=self._open_project).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Save", command=self._save_project).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Validate", command=self._validate_project).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Auto layout", command=self._auto_layout).pack(side=tk.LEFT)

        main = ttk.Frame(self)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Flowcharts").pack(anchor=tk.W)
        self.flowcharts_list = tk.Listbox(left, width=22)
        self.flowcharts_list.pack(fill=tk.Y, expand=True)
        self.flowcharts_list.bind("<<ListboxSelect>>", self._on_select_flowchart)

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X)
        ttk.Button(btns, text="Remove", command=self._remove_flowchart).pack(side=tk.LEFT)

        center = ttk.Frame(main)
        center.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vars_box = ttk.LabelFrame(center, text="Variables for selected flowchart")
        vars_box.pack(fill=tk.X)
        self.vars_entry = ttk.Entry(vars_box)
        self.vars_entry.pack(fill=tk.X, padx=4, pady=4)

        nodes_box = ttk.LabelFrame(center, text="Nodes")
        nodes_box.pack(fill=tk.BOTH, expand=True)
        self.nodes_list = tk.Listbox(nodes_box)
        self.nodes_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.nodes_list.bind("<<ListboxSelect>>", self._on_select_node)

        node_form = ttk.Frame(nodes_box)
        node_form.pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Label(node_form, text="Node ID").pack(anchor=tk.W)
        self.node_id_entry = ttk.Entry(node_form)
        self.node_id_entry.pack(fill=tk.X)

        ttk.Label(node_form, text="Type").pack(anchor=tk.W)
        self.node_type_var = tk.StringVar()
        self.node_type_combo = ttk.Combobox(
            node_form, textvariable=self.node_type_var, values=sorted(NODE_TYPES), state="readonly"
        )
        self.node_type_combo.pack(fill=tk.X)
        self.node_type_combo.bind("<<ComboboxSelected>>", self._on_node_type_change)

        params_box = ttk.LabelFrame(node_form, text="Parameters")
        params_box.pack(fill=tk.X, pady=6)

        self.param_dst_label = ttk.Label(params_box, text="dst")
        self.param_dst_label.grid(row=0, column=0, sticky=tk.W)
        self.param_dst_var = tk.StringVar()
        self.param_dst_combo = ttk.Combobox(params_box, textvariable=self.param_dst_var, values=[])
        self.param_dst_combo.grid(row=0, column=1, sticky=tk.EW, padx=4, pady=2)

        self.param_src_label = ttk.Label(params_box, text="src")
        self.param_src_label.grid(row=1, column=0, sticky=tk.W)
        self.param_src_var = tk.StringVar()
        self.param_src_combo = ttk.Combobox(params_box, textvariable=self.param_src_var, values=[])
        self.param_src_combo.grid(row=1, column=1, sticky=tk.EW, padx=4, pady=2)

        self.param_const_label = ttk.Label(params_box, text="const")
        self.param_const_label.grid(row=2, column=0, sticky=tk.W)
        self.param_const_var = tk.StringVar()
        self.param_const_entry = ttk.Entry(params_box, textvariable=self.param_const_var)
        self.param_const_entry.grid(row=2, column=1, sticky=tk.EW, padx=4, pady=2)

        self.param_op_label = ttk.Label(params_box, text="op")
        self.param_op_label.grid(row=3, column=0, sticky=tk.W)
        self.param_op_var = tk.StringVar()
        self.param_op_combo = ttk.Combobox(
            params_box, textvariable=self.param_op_var, values=sorted(BRANCH_OPS), state="readonly"
        )
        self.param_op_combo.grid(row=3, column=1, sticky=tk.EW, padx=4, pady=2)

        self.param_left_label = ttk.Label(params_box, text="left")
        self.param_left_label.grid(row=4, column=0, sticky=tk.W)
        self.param_left_var = tk.StringVar()
        self.param_left_combo = ttk.Combobox(params_box, textvariable=self.param_left_var, values=[])
        self.param_left_combo.grid(row=4, column=1, sticky=tk.EW, padx=4, pady=2)

        self.param_right_label = ttk.Label(params_box, text="right")
        self.param_right_label.grid(row=5, column=0, sticky=tk.W)
        self.param_right_var = tk.StringVar()
        self.param_right_entry = ttk.Entry(params_box, textvariable=self.param_right_var)
        self.param_right_entry.grid(row=5, column=1, sticky=tk.EW, padx=4, pady=2)

        params_box.columnconfigure(1, weight=1)

        ttk.Button(node_form, text="Add/Update", command=self._add_update_node).pack(
            fill=tk.X, pady=4
        )
        ttk.Button(node_form, text="Remove", command=self._remove_node).pack(fill=tk.X)

        edges_box = ttk.LabelFrame(center, text="Edges")
        edges_box.pack(fill=tk.BOTH, expand=True)
        self.edges_list = tk.Listbox(edges_box)
        self.edges_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        edge_form = ttk.Frame(edges_box)
        edge_form.pack(side=tk.LEFT, fill=tk.Y, padx=8)
        ttk.Label(edge_form, text="From").pack(anchor=tk.W)
        self.edge_from_var = tk.StringVar()
        self.edge_from_combo = ttk.Combobox(edge_form, textvariable=self.edge_from_var, values=[], state="readonly")
        self.edge_from_combo.pack(fill=tk.X)

        ttk.Label(edge_form, text="To").pack(anchor=tk.W)
        self.edge_to_var = tk.StringVar()
        self.edge_to_combo = ttk.Combobox(edge_form, textvariable=self.edge_to_var, values=[], state="readonly")
        self.edge_to_combo.pack(fill=tk.X)

        ttk.Label(edge_form, text="Label").pack(anchor=tk.W)
        self.edge_label_var = tk.StringVar()
        self.edge_label_combo = ttk.Combobox(
            edge_form,
            textvariable=self.edge_label_var,
            values=("empty", "true", "false"),
            state="readonly",
        )
        self.edge_label_combo.pack(fill=tk.X)

        ttk.Button(edge_form, text="Add", command=self._add_edge).pack(fill=tk.X, pady=4)
        ttk.Button(edge_form, text="Remove", command=self._remove_edge).pack(fill=tk.X)

        right = ttk.Frame(main)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas_box = ttk.LabelFrame(right, text="Diagram (drag nodes)")
        canvas_box.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        self.canvas = tk.Canvas(canvas_box, background="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self._on_canvas_press)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)

    def _current_flowchart(self):
        index = self.flowcharts_list.curselection()
        if index:
            self._selected_flowchart_idx = index[0]
        if self._selected_flowchart_idx is None:
            return None
        if self._selected_flowchart_idx >= len(self.data["flowcharts"]):
            return None
        return self.data["flowcharts"][self._selected_flowchart_idx]

    def _select_flowchart_index(self, index: int) -> None:
        if index < 0 or index >= len(self.data["flowcharts"]):
            return
        self.flowcharts_list.selection_clear(0, tk.END)
        self.flowcharts_list.selection_set(index)
        self.flowcharts_list.see(index)
        self._selected_flowchart_idx = index

    def _refresh_flowcharts(self) -> None:
        self.flowcharts_list.delete(0, tk.END)
        for chart in self.data["flowcharts"]:
            self.flowcharts_list.insert(tk.END, chart["id"])

    def _refresh_nodes(self) -> None:
        self.nodes_list.delete(0, tk.END)
        chart = self._current_flowchart()
        if not chart:
            return
        self._sync_var_options(chart)
        self._sync_edge_options(chart)
        self._ensure_node_positions(chart)
        for node in chart["nodes"]:
            self.nodes_list.insert(tk.END, f"{node['id']} ({node['type']})")
        self._render_canvas()
        self._reselect_node()

    def _refresh_edges(self) -> None:
        self.edges_list.delete(0, tk.END)
        chart = self._current_flowchart()
        if not chart:
            return
        for edge in chart["edges"]:
            label = edge.get("label")
            label_str = f" [{label}]" if label else ""
            self.edges_list.insert(tk.END, f"{edge['from']} -> {edge['to']}{label_str}")
        self._render_canvas()

    def _new_project(self) -> None:
        self.data = {"flowcharts": []}
        self._selected_flowchart_idx = None
        self._selected_node_id = None
        self.vars_entry.delete(0, tk.END)
        self.edge_from_var.set("")
        self.edge_to_var.set("")
        self.edge_label_var.set("")
        self._refresh_flowcharts()
        self.nodes_list.delete(0, tk.END)
        self.edges_list.delete(0, tk.END)
        self._render_canvas()
        self._clear_node_form()
        self._sync_edge_options({"nodes": []})

    def _open_project(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            self.data = load_json_file(path)
        except Exception as exc:
            messagebox.showerror("Open", f"Failed to load file: {exc}")
            return
        self._refresh_flowcharts()
        self.nodes_list.delete(0, tk.END)
        self.edges_list.delete(0, tk.END)
        if self.data["flowcharts"]:
            self._select_flowchart_index(0)
            self._sync_vars_from_chart(self.data["flowcharts"][0])
            self._refresh_nodes()
            self._refresh_edges()
        else:
            self._selected_flowchart_idx = None
            self._sync_edge_options({"nodes": []})
        self._render_canvas()

    def _save_project(self) -> None:
        self._sync_vars_to_chart()
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        save_json_file(path, self.data)

    def _validate_project(self) -> None:
        self._sync_vars_to_chart()
        errors = validate_project(self.data)
        if errors:
            messagebox.showerror("Validate", "\n".join(errors))
        else:
            messagebox.showinfo("Validate", "OK")

    def _sync_vars_to_chart(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            return
        raw = self.vars_entry.get().strip()
        if raw:
            vars_list = [v.strip() for v in raw.split(",") if v.strip()]
            if len(vars_list) > MAX_VARIABLES:
                messagebox.showerror("Variables", "Maximum 100 variables per flowchart")
                vars_list = vars_list[:MAX_VARIABLES]
            chart["variables"] = vars_list
        else:
            chart["variables"] = []
        self._sync_var_options(chart)

    def _sync_vars_from_chart(self, chart: Dict) -> None:
        self.vars_entry.delete(0, tk.END)
        self.vars_entry.insert(0, ", ".join(chart.get("variables", [])))
        self._sync_var_options(chart)

    def _add_flowchart(self) -> None:
        if len(self.data["flowcharts"]) >= MAX_FLOWCHARTS:
            messagebox.showerror("Flowcharts", "Maximum 100 flowcharts allowed")
            return
        name = f"T{len(self.data['flowcharts']) + 1}"
        chart = {"id": name, "variables": [], "nodes": [], "edges": []}
        self.data["flowcharts"].append(chart)
        self._refresh_flowcharts()
        self._select_flowchart_index(len(self.data["flowcharts"]) - 1)
        self._sync_vars_from_chart(chart)
        self._refresh_nodes()
        self._refresh_edges()
        self._render_canvas()

    def _new_flowchart(self) -> None:
        self._add_flowchart()

    def _remove_flowchart(self) -> None:
        index = self.flowcharts_list.curselection()
        if not index:
            return
        del self.data["flowcharts"][index[0]]
        self._refresh_flowcharts()
        if self.data["flowcharts"]:
            self._select_flowchart_index(0)
            self._sync_vars_from_chart(self.data["flowcharts"][0])
            self._refresh_nodes()
            self._refresh_edges()
        else:
            self.vars_entry.delete(0, tk.END)
            self._selected_flowchart_idx = None
            self._clear_node_form()
            self._sync_edge_options({"nodes": []})
        self.nodes_list.delete(0, tk.END)
        self.edges_list.delete(0, tk.END)
        self._render_canvas()

    def _on_select_flowchart(self, _event=None) -> None:
        self._sync_vars_to_chart()
        chart = self._current_flowchart()
        if chart:
            self._sync_vars_from_chart(chart)
        self._refresh_nodes()
        self._refresh_edges()
        self._render_canvas()

    def _add_update_node(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            messagebox.showerror("Node", "Select a flowchart first")
            return
        if len(chart["nodes"]) >= MAX_NODES:
            messagebox.showerror("Node", "Maximum 100 nodes per flowchart")
            return
        node_id = self.node_id_entry.get().strip()
        node_type = self.node_type_var.get().strip()

        if not node_id or not node_type:
            messagebox.showerror("Node", "Node ID and type are required")
            return

        try:
            params = self._params_from_form(node_type)
        except ValueError as exc:
            messagebox.showerror("Node", str(exc))
            return

        self._sync_vars_to_chart()
        errors = self._validate_node_params(node_type, params, chart.get("variables", []))
        if errors:
            messagebox.showerror("Node", "\n".join(errors))
            return

        for node in chart["nodes"]:
            if node["id"] == node_id:
                node["type"] = node_type
                node["params"] = params
                self._selected_node_id = node_id
                self._refresh_nodes()
                return

        node = {"id": node_id, "type": node_type, "params": params}
        self._assign_node_position(node, chart)
        chart["nodes"].append(node)
        self._selected_node_id = node_id
        self._refresh_nodes()

    def _remove_node(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            messagebox.showerror("Node", "Select a flowchart first")
            return
        selection = self.nodes_list.curselection()
        if not selection:
            return
        index = selection[0]
        node_id = chart["nodes"][index]["id"]
        chart["nodes"] = [n for n in chart["nodes"] if n["id"] != node_id]
        chart["edges"] = [e for e in chart["edges"] if e["from"] != node_id and e["to"] != node_id]
        self._selected_node_id = None
        self._refresh_nodes()
        self._refresh_edges()
        self._render_canvas()
        self._clear_node_form()

    def _add_edge(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            messagebox.showerror("Edge", "Select a flowchart first")
            return
        self._sync_vars_to_chart()
        src = self.edge_from_var.get().strip()
        dst = self.edge_to_var.get().strip()
        label_raw = self.edge_label_var.get().strip()
        label = None if label_raw in {"", "empty"} else label_raw

        if not src or not dst:
            messagebox.showerror("Edge", "From and To are required")
            return

        edge = {"from": src, "to": dst}
        if label:
            edge["label"] = label
        chart["edges"].append(edge)
        self._refresh_edges()
        self._render_canvas()

    def _remove_edge(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            messagebox.showerror("Edge", "Select a flowchart first")
            return
        selection = self.edges_list.curselection()
        if not selection:
            return
        index = selection[0]
        del chart["edges"][index]
        self._refresh_edges()
        self._render_canvas()

    def _validate_node_params(self, node_type: str, params: Dict, variables: list) -> list:
        errors = []
        var_set = set(variables)

        def require_var(key: str) -> None:
            value = params.get(key)
            if value not in var_set:
                errors.append(f"param {key} must be an existing variable")

        def require_const(key: str) -> None:
            value = params.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= MAX_CONST):
                errors.append(f"param {key} must be int 0..2^31-1")

        if node_type == "ASSIGN_VAR_VAR":
            require_var("dst")
            require_var("src")
        elif node_type == "ASSIGN_VAR_CONST":
            require_var("dst")
            require_const("value")
        elif node_type == "INPUT":
            require_var("dst")
        elif node_type == "PRINT":
            require_var("src")
        elif node_type == "BRANCH":
            require_var("left")
            op = params.get("op")
            if op not in BRANCH_OPS:
                errors.append("param op must be '==' or '<'")
            require_const("right")

        return errors

    def _assign_node_position(self, node: Dict, chart: Dict) -> None:
        if "pos" in node:
            return
        index = len(chart["nodes"])
        x = 80 + (index % 4) * 180
        y = 60 + (index // 4) * 120
        node["pos"] = {"x": x, "y": y}

    def _auto_layout(self) -> None:
        chart = self._current_flowchart()
        if not chart:
            messagebox.showerror("Layout", "Select a flowchart first")
            return
        for node in chart["nodes"]:
            node.pop("pos", None)
        for index, node in enumerate(chart["nodes"]):
            x = 80 + (index % 4) * 180
            y = 60 + (index // 4) * 120
            node["pos"] = {"x": x, "y": y}
        self._render_canvas()

    def _ensure_node_positions(self, chart: Dict) -> None:
        for node in chart["nodes"]:
            self._assign_node_position(node, chart)

    def _render_canvas(self) -> None:
        self.canvas.delete("all")
        self._canvas_nodes.clear()
        self._canvas_edges = []

        chart = self._current_flowchart()
        if not chart:
            return

        self._ensure_node_positions(chart)

        for edge in chart["edges"]:
            src = edge.get("from")
            dst = edge.get("to")
            src_node = self._find_node(chart, src)
            dst_node = self._find_node(chart, dst)
            if not src_node or not dst_node:
                continue
            x1, y1 = self._node_center(src_node)
            x2, y2 = self._node_center(dst_node)
            line_id = self.canvas.create_line(x1, y1, x2, y2, arrow=tk.LAST)
            label = edge.get("label")
            if label:
                lx = (x1 + x2) / 2
                ly = (y1 + y2) / 2
                self.canvas.create_text(lx, ly - 8, text=label, fill="#555")
            self._canvas_edges.append(line_id)

        for node in chart["nodes"]:
            x, y = self._node_center(node)
            w = 120
            h = 50
            rect = self.canvas.create_rectangle(
                x - w / 2, y - h / 2, x + w / 2, y + h / 2, fill="#f2f2f2"
            )
            text = self.canvas.create_text(x, y, text=f"{node['id']}\n{node['type']}")
            self._canvas_nodes[node["id"]] = (rect, text)

    def _find_node(self, chart: Dict, node_id: str) -> Optional[Dict]:
        for node in chart["nodes"]:
            if node.get("id") == node_id:
                return node
        return None

    def _node_center(self, node: Dict) -> Tuple[float, float]:
        pos = node.get("pos") or {"x": 0, "y": 0}
        return float(pos.get("x", 0)), float(pos.get("y", 0))

    def _on_canvas_press(self, event) -> None:
        chart = self._current_flowchart()
        if not chart:
            return
        item = self.canvas.find_closest(event.x, event.y)
        if not item:
            return
        node_id = self._node_id_for_item(item[0])
        if not node_id:
            return
        node = self._find_node(chart, node_id)
        if not node:
            return
        x, y = self._node_center(node)
        self._drag_node_id = node_id
        self._drag_offset = (x - event.x, y - event.y)
        self._select_node_in_list(node_id)

    def _on_canvas_drag(self, event) -> None:
        if not self._drag_node_id:
            return
        chart = self._current_flowchart()
        if not chart:
            return
        node = self._find_node(chart, self._drag_node_id)
        if not node:
            return
        dx, dy = self._drag_offset
        node["pos"] = {"x": event.x + dx, "y": event.y + dy}
        self._render_canvas()

    def _on_canvas_release(self, _event) -> None:
        self._drag_node_id = None

    def _node_id_for_item(self, item_id: int) -> Optional[str]:
        for node_id, (rect_id, text_id) in self._canvas_nodes.items():
            if item_id in (rect_id, text_id):
                return node_id
        return None

    def _select_node_in_list(self, node_id: str) -> None:
        chart = self._current_flowchart()
        if not chart:
            return
        for idx, node in enumerate(chart["nodes"]):
            if node.get("id") == node_id:
                self.nodes_list.selection_clear(0, tk.END)
                self.nodes_list.selection_set(idx)
                self.nodes_list.see(idx)
                self._on_select_node()
                return

    def _reselect_node(self) -> None:
        if not self._selected_node_id:
            return
        self._select_node_in_list(self._selected_node_id)

    def _on_select_node(self, _event=None) -> None:
        chart = self._current_flowchart()
        if not chart:
            return
        selection = self.nodes_list.curselection()
        if not selection:
            return
        node = chart["nodes"][selection[0]]
        self._selected_node_id = node.get("id")
        self.node_id_entry.delete(0, tk.END)
        self.node_id_entry.insert(0, node.get("id", ""))
        self.node_type_var.set(node.get("type", ""))
        self._sync_var_options(chart)
        self._fill_form_from_params(node.get("type", ""), node.get("params") or {})

    def _sync_var_options(self, chart: Dict) -> None:
        variables = chart.get("variables", [])
        for combo in (
            self.param_dst_combo,
            self.param_src_combo,
            self.param_left_combo,
        ):
            combo["values"] = variables

    def _sync_edge_options(self, chart: Dict) -> None:
        node_ids = [node.get("id", "") for node in chart.get("nodes", []) if node.get("id")]
        self.edge_from_combo["values"] = node_ids
        self.edge_to_combo["values"] = node_ids
        if self.edge_from_var.get() not in node_ids:
            self.edge_from_var.set("")
        if self.edge_to_var.get() not in node_ids:
            self.edge_to_var.set("")
        if self.edge_label_var.get() not in {"", "empty", "true", "false"}:
            self.edge_label_var.set("")

    def _clear_node_form(self) -> None:
        self.node_id_entry.delete(0, tk.END)
        self.node_type_var.set("")
        self.param_dst_var.set("")
        self.param_src_var.set("")
        self.param_const_var.set("")
        self.param_op_var.set("")
        self.param_left_var.set("")
        self.param_right_var.set("")
        self._update_param_form("")

    def _params_from_form(self, node_type: str) -> Dict:
        if node_type == "ASSIGN_VAR_VAR":
            return {"dst": self.param_dst_var.get(), "src": self.param_src_var.get()}
        if node_type == "ASSIGN_VAR_CONST":
            value = self._parse_required_int(self.param_const_var.get(), "const")
            return {"dst": self.param_dst_var.get(), "value": value}
        if node_type == "INPUT":
            return {"dst": self.param_dst_var.get()}
        if node_type == "PRINT":
            return {"src": self.param_src_var.get()}
        if node_type == "BRANCH":
            value = self._parse_required_int(self.param_right_var.get(), "right")
            return {
                "left": self.param_left_var.get(),
                "op": self.param_op_var.get(),
                "right": value,
            }
        return {}

    def _fill_form_from_params(self, node_type: str, params: Dict) -> None:
        self._update_param_form(node_type)
        if node_type == "ASSIGN_VAR_VAR":
            self.param_dst_var.set(params.get("dst", ""))
            self.param_src_var.set(params.get("src", ""))
        elif node_type == "ASSIGN_VAR_CONST":
            self.param_dst_var.set(params.get("dst", ""))
            self.param_const_var.set(str(params.get("value", "")))
        elif node_type == "INPUT":
            self.param_dst_var.set(params.get("dst", ""))
        elif node_type == "PRINT":
            self.param_src_var.set(params.get("src", ""))
        elif node_type == "BRANCH":
            self.param_left_var.set(params.get("left", ""))
            self.param_op_var.set(params.get("op", ""))
            self.param_right_var.set(str(params.get("right", "")))

    def _on_node_type_change(self, _event=None) -> None:
        self._update_param_form(self.node_type_var.get())

    def _update_param_form(self, node_type: str) -> None:
        def set_visible(label, widget, visible: bool) -> None:
            if visible:
                label.grid()
                widget.grid()
                widget.configure(state="normal")
            else:
                label.grid_remove()
                widget.grid_remove()
                widget.configure(state="disabled")

        set_visible(
            self.param_dst_label,
            self.param_dst_combo,
            node_type in {"ASSIGN_VAR_VAR", "ASSIGN_VAR_CONST", "INPUT"},
        )
        set_visible(
            self.param_src_label,
            self.param_src_combo,
            node_type in {"ASSIGN_VAR_VAR", "PRINT"},
        )
        set_visible(
            self.param_const_label,
            self.param_const_entry,
            node_type == "ASSIGN_VAR_CONST",
        )
        set_visible(
            self.param_op_label,
            self.param_op_combo,
            node_type == "BRANCH",
        )
        set_visible(
            self.param_left_label,
            self.param_left_combo,
            node_type == "BRANCH",
        )
        set_visible(
            self.param_right_label,
            self.param_right_entry,
            node_type == "BRANCH",
        )

    def _parse_required_int(self, raw: str, field: str) -> int:
        raw = raw.strip()
        if raw == "":
            raise ValueError(f"Field {field} must be an integer")
        try:
            return int(raw)
        except ValueError as exc:
            raise ValueError(f"Field {field} must be an integer") from exc


def run_gui() -> None:
    app = FlowchartEditor()
    app.mainloop()
