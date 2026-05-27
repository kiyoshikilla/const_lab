import unittest

from src.codegen import generate_python


class CodegenTests(unittest.TestCase):
    def test_generate_python(self):
        data = {
            "flowcharts": [
                {
                    "id": "T1",
                    "variables": ["A"],
                    "nodes": [
                        {"id": "n1", "type": "START"},
                        {"id": "n2", "type": "ASSIGN_VAR_CONST", "params": {"dst": "A", "value": 1}},
                        {"id": "n3", "type": "END"},
                    ],
                    "edges": [
                        {"from": "n1", "to": "n2"},
                        {"from": "n2", "to": "n3"},
                    ],
                }
            ],
        }
        code = generate_python(data)
        self.assertIn("class FlowchartRunner", code)
        self.assertIn("def main()", code)


if __name__ == "__main__":
    unittest.main()
