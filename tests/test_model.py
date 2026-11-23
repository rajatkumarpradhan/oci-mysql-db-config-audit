import json
import os
import tempfile
import unittest

from mysql_audit.model import DEFAULT_RETENTION_DAYS, ExportError, load_export


def write(payload):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as fh:
        json.dump(payload, fh)
    return path


class TestLoad(unittest.TestCase):
    def test_load_ok(self):
        path = write({"db_systems": [{"name": "a", "labels": ["prod"], "retention_days": 14}]})
        (systems,) = load_export(path)
        self.assertEqual(systems.name, "a")
        self.assertTrue(systems.is_prod())
        self.assertEqual(systems.retention_days, 14)

    def test_defaults(self):
        path = write({"db_systems": [{"name": "a"}]})
        (s,) = load_export(path)
        self.assertTrue(s.backups_enabled)
        self.assertEqual(s.retention_days, DEFAULT_RETENTION_DAYS)
        self.assertFalse(s.delete_protected)

    def test_rejects_missing_name(self):
        with self.assertRaises(ExportError):
            load_export(write({"db_systems": [{}]}))

    def test_rejects_bad_json(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as fh:
            fh.write("{not json")
        with self.assertRaises(ExportError):
            load_export(path)

    def test_rejects_zero_retention(self):
        with self.assertRaises(ExportError):
            load_export(write({"db_systems": [{"name": "a", "retention_days": 0}]}))

    def test_rejects_bool_retention(self):
        with self.assertRaises(ExportError):
            load_export(write({"db_systems": [{"name": "a", "retention_days": True}]}))


if __name__ == "__main__":
    unittest.main()
