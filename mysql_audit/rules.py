"""MYS001-MYS004 rules."""

from __future__ import annotations

from dataclasses import dataclass

from .model import DEFAULT_RETENTION_DAYS


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    target: str
    detail: str


def rule_prod_backups_disabled(systems: tuple) -> list:
    """MYS001 HIGH: prod-labeled DB system with automatic backups disabled."""
    return [
        Finding("MYS001", "HIGH", d.name,
                "prod-labeled DB system records automatic backups disabled; the OCI docs recommend "
                "enabling them - without them only manual backups exist, if any. Review flag")
        for d in systems if d.is_prod() and not d.backups_enabled
    ]


def rule_retention_below_default(systems: tuple) -> list:
    """MYS002 MEDIUM: automatic backup retention below the 7-day documented default."""
    out = []
    for d in systems:
        if d.backups_enabled and d.retention_days < DEFAULT_RETENTION_DAYS:
            out.append(
                Finding("MYS002", "MEDIUM", d.name,
                        f"automatic backup retention is {d.retention_days} day(s), below the 7-day "
                        f"documented default (service allows 1-35); the default is this rule's review "
                        f"floor, not a platform minimum - review flag")
            )
    return out


def rule_prod_not_delete_protected(systems: tuple) -> list:
    """MYS003 MEDIUM: prod-labeled DB system without delete protection."""
    return [
        Finding("MYS003", "MEDIUM", d.name,
                "prod-labeled DB system records delete protection off in its deletion plan; "
                "accidental deletion is not blocked and no final backup is forced. Review flag")
        for d in systems if d.is_prod() and not d.delete_protected
    ]


def rule_no_identifiers(systems: tuple) -> list:
    """MYS004 LOW: no description and no tags recorded."""
    return [
        Finding("MYS004", "LOW", d.name,
                "no description and no tags recorded; hard to trace to an owner or purpose")
        for d in systems if not d.description and not d.tags
    ]


ALL_RULES = (
    rule_prod_backups_disabled,
    rule_retention_below_default,
    rule_prod_not_delete_protected,
    rule_no_identifiers,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(systems: tuple) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(systems))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.target))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
