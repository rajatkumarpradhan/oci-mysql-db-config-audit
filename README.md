# oci-mysql-db-config-audit

**Category: custom portfolio tool.** The OOTB built-in-services project in this pair is
`oci-ootb-goldengate-deployment-check`.

## The problem

A MySQL HeatWave DB system's backup plan and deletion plan are configured per system, and
the platform does not force them: automatic backups are optional (though the OCI docs
recommend enabling them), retention can be set below the 7-day default, and delete
protection is off unless someone selects it. For a production database each of these is a
review-worthy gap. This tool audits an offline JSON export of DB systems and flags them.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| MYS001 | HIGH | A **prod-labeled** DB system records automatic backups **disabled** - the docs recommend enabling them; without them only manual backups exist, if any. |
| MYS002 | MEDIUM | Automatic backup retention is set **below the 7-day default** (the service allows 1-35 days; this rule uses the documented default as the review floor, not a platform minimum). |
| MYS003 | MEDIUM | A **prod-labeled** DB system records **delete protection off** in its deletion plan - accidental deletion is not blocked and no final backup is forced. |
| MYS004 | LOW | No description and no tags recorded - the system is hard to trace to an owner or purpose. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m mysql_audit.cli samples/mysql_messy.json   # exits 2, all 4 rules fire
python -m mysql_audit.cli samples/mysql_clean.json   # exits 0
python -m unittest discover -s tests -v              # 23 tests, stdlib only
```

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCI API.
- Findings are review prompts describing what the export records. Disabled automatic
  backups can be deliberate when backups are managed another way, and a short retention
  can match a documented recovery-point requirement.
- Always Free DB systems have a fixed 1-day retention; exports for them should be
  labelled so MYS002 does not misread the platform default as a misconfiguration.
- Backup and deletion-plan semantics are from the MySQL HeatWave docs as of Nov 2026
  (automatic backups recommended, default retention 7 days, configurable 1-35 days).
  Verify current behavior before acting.
- "prod" labeling is read from the export; an unlabeled production system is invisible
  to MYS001 and MYS003.
- No live tenancy was touched.

## Implementation and sources

Custom Python code audits supplied records; it does not configure a native OCI workflow.
Only the offline tests and synthetic demos ran, locally and in GitHub Actions.

- https://docs.oracle.com/en-us/iaas/mysql-database/doc/overview-backups.html
- https://docs.oracle.com/en-us/iaas/mysql-database/doc/creating-db-system.html
- https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/mysql_mysql_db_system

## Project status

Built as a daily portfolio project. 23 unit tests, green locally and in CI. Free tier
only; no live cloud calls, no spend.
