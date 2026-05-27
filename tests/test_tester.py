import unittest

from src.tester import enumerate_executions


class TesterTests(unittest.TestCase):
    def test_enumerate_executions(self):
        data = {
            "flowcharts": [
                {
                    "id": "T1",
                    "variables": ["A"],
                    "nodes": [
                        {"id": "n1", "type": "START"},
                        {"id": "n2", "type": "ASSIGN_VAR_CONST", "params": {"dst": "A", "value": 1}},
                        {"id": "n3", "type": "PRINT", "params": {"src": "A"}},
                        {"id": "n4", "type": "END"},
                    ],
                    "edges": [
                        {"from": "n1", "to": "n2"},
                        {"from": "n2", "to": "n3"},
                        {"from": "n3", "to": "n4"},
                    ],
                }
            ]
        }
        results, checked = enumerate_executions(data, [], max_steps=10)
        self.assertEqual(checked, 1)
        self.assertEqual(results[0].output_lines, ["[Thread T1] PRINT: 1"])


if __name__ == "__main__":
    unittest.main()
