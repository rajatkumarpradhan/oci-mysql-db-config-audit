import unittest

from mysql_audit.model import DbSystem
from mysql_audit.rules import (
    exit_code,
    rule_no_identifiers,
    rule_prod_backups_disabled,
    rule_prod_not_delete_protected,
    rule_retention_below_default,
    run_all,
)


def db(name="d", labels=("prod",), backups_enabled=True, retention_days=7,
       delete_protected=True, description="x", tags=("team:a",)):
    return DbSystem(name=name, labels=tuple(labels), backups_enabled=backups_enabled,
                    retention_days=retention_days, delete_protected=delete_protected,
                    description=description, tags=tuple(tags))


class TestMys001(unittest.TestCase):
    def test_fires_prod_backups_off(self):
        out = rule_prod_backups_disabled((db(backups_enabled=False),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_quiet_dev_backups_off(self):
        self.assertEqual(rule_prod_backups_disabled((db(labels=("dev",), backups_enabled=False),)), [])

    def test_quiet_prod_backups_on(self):
        self.assertEqual(rule_prod_backups_disabled((db(),)), [])


class TestMys002(unittest.TestCase):
    def test_fires_below_default(self):
        out = rule_retention_below_default((db(retention_days=2),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_quiet_at_default(self):
        self.assertEqual(rule_retention_below_default((db(retention_days=7),)), [])

    def test_quiet_backups_disabled(self):
        # disabled backups are MYS001's job, not a retention misconfiguration
        self.assertEqual(rule_retention_below_default((db(backups_enabled=False, retention_days=1),)), [])


class TestMys003(unittest.TestCase):
    def test_fires_prod_unprotected(self):
        out = rule_prod_not_delete_protected((db(delete_protected=False),))
        self.assertEqual(len(out), 1)

    def test_quiet_dev_unprotected(self):
        self.assertEqual(rule_prod_not_delete_protected((db(labels=("dev",), delete_protected=False),)), [])


class TestMys004(unittest.TestCase):
    def test_fires_no_identifiers(self):
        out = rule_no_identifiers((db(description="", tags=()),))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_quiet_with_tags_only(self):
        self.assertEqual(rule_no_identifiers((db(description="", tags=("team:a",)),)), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((db(backups_enabled=False),))), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((db(retention_days=3),))), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((db(),))), 0)

    def test_sorted_high_first(self):
        out = run_all((db(description="", tags=(), delete_protected=False, backups_enabled=False),))
        self.assertEqual(out[0].severity, "HIGH")
        self.assertEqual(out[-1].severity, "LOW")


if __name__ == "__main__":
    unittest.main()
