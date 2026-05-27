import unittest

from src.validator import validate_project


class ValidatorTests(unittest.TestCase):
    def test_valid_project(self):
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
        errors = validate_project(data)
        self.assertEqual(errors, [])

    def test_missing_start(self):
        data = {
            "flowcharts": [
                {
                    "id": "T1",
                    "variables": ["A"],
                    "nodes": [
                        {"id": "n2", "type": "ASSIGN_VAR_CONST", "params": {"dst": "A", "value": 1}},
                        {"id": "n3", "type": "END"},
                    ],
                    "edges": [
                        {"from": "n2", "to": "n3"},
                    ],
                }
            ],
        }
        errors = validate_project(data)
        self.assertTrue(any("START" in e for e in errors))

    def test_invalid_const(self):
        data = {
            "flowcharts": [
                {
                    "id": "T1",
                    "variables": ["A"],
                    "nodes": [
                        {"id": "n1", "type": "START"},
                        {"id": "n2", "type": "ASSIGN_VAR_CONST", "params": {"dst": "A", "value": -1}},
                        {"id": "n3", "type": "END"},
                    ],
                    "edges": [
                        {"from": "n1", "to": "n2"},
                        {"from": "n2", "to": "n3"},
                    ],
                }
            ],
        }
        errors = validate_project(data)
        self.assertTrue(any("const value" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
