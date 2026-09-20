"""Phase 5: every retirement/staleness condition has ONE owner (smith_core.RETIREMENT_OWNERS).
cmd_proposals may auto-retire only on mechanical ticker-level facts; smith_validity only gives a
verdict (the user clicks); reconcile-proposals only marks a real fill executed."""
import os
import re

import smith_core as core
import smith_validity as sv

SCRIPTS = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")


def _src(name):
    return open(os.path.join(SCRIPTS, name)).read()


def _codes_in(src):
    return set(re.findall(r'\bcond(?:ition)?\s*=\s*"([a-z0-9_]+)"', src)) | \
        set(re.findall(r'"condition":\s*"([a-z0-9_]+)"', src)) | \
        set(re.findall(r'(?:cond_retire|cond_weak)\.append\("([a-z0-9_]+)"\)', src)) | \
        set(re.findall(r'retired_condition"\]\s*=\s*"([a-z0-9_]+)"', src)) | \
        set(re.findall(r'"(?:ticket_expired|ticket_invalidation_met)"', src) and
            re.findall(r'"(ticket_expired|ticket_invalidation_met)"', src))


def test_table_shape_and_owners_are_known():
    owners = {o for o, _ in core.RETIREMENT_OWNERS.values()}
    assert owners == {core.OWNER_LIFECYCLE, core.OWNER_VALIDITY, core.OWNER_RECONCILE}
    assert all(desc for _, desc in core.RETIREMENT_OWNERS.values())


def test_no_condition_is_owned_by_both_modules():
    life = core.retirement_conditions(core.OWNER_LIFECYCLE)
    assert not (life & sv.VERDICT_CONDITIONS)
    assert life | sv.VERDICT_CONDITIONS | core.retirement_conditions(core.OWNER_RECONCILE) == set(core.RETIREMENT_OWNERS)


def test_lifecycle_source_emits_only_lifecycle_codes():
    used = _codes_in(_src("smith_lifecycle.py"))
    assert used, "no condition codes found -- the tagging regex is stale"
    assert used <= core.retirement_conditions(core.OWNER_LIFECYCLE), used - core.retirement_conditions(core.OWNER_LIFECYCLE)


def test_validity_source_emits_only_validity_codes_and_no_lifecycle_code():
    used = _codes_in(_src("smith_validity.py"))
    assert used and used <= sv.VERDICT_CONDITIONS
    assert not (used & core.retirement_conditions(core.OWNER_LIFECYCLE))


def test_validity_never_writes_a_status():
    src = _src("smith_validity.py")
    assert not re.search(r'\["status"\]\s*=', src) and "safe_write" not in src


def test_every_lifecycle_retirement_carries_a_condition():
    """A retired row with no condition code would be an unowned retirement."""
    src = _src("smith_lifecycle.py")
    for m in re.finditer(r'\["status"\] = "auto_retired"', src):
        assert "condition" in src[m.start():m.start() + 700]


def test_validity_trigger_gone_alone_is_not_a_verdict_condition():
    assert "trigger_no_longer_fires" not in sv.VERDICT_CONDITIONS
