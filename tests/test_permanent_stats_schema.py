import pytest

from aidm.schemas.permanent_stats import (
    Ability,
    PermanentModifierTotals,
    PermanentModifierType,
    PermanentStatModifiedEvent,
    PermanentStatRestoredEvent,
    DerivedStatsRecalculatedEvent,
    AbilityScoreDeathEvent,
    PermanentStatModifiers,
)
from aidm.schemas.entity_state import EntityState


def test_permanent_modifier_totals_validation_signs():
    # drain must be <= 0
    with pytest.raises(ValueError):
        PermanentModifierTotals(drain=+1, inherent=0)

    # inherent must be >= 0
    with pytest.raises(ValueError):
        PermanentModifierTotals(drain=0, inherent=-1)

    # both ok
    x = PermanentModifierTotals(drain=-2, inherent=+3)
    assert x.drain == -2
    assert x.inherent == 3


def test_permanent_stat_modifiers_roundtrip_defaults_and_order():
    mods = PermanentStatModifiers()
    d = mods.to_dict()
    assert list(d.keys()) == ["str", "dex", "con", "int", "wis", "cha"]

    mods2 = PermanentStatModifiers.from_dict(d)
    assert mods2.to_dict() == d


def test_event_permanent_stat_modified_validation():
    # drain must be negative
    with pytest.raises(ValueError):
        PermanentStatModifiedEvent(
            event_type="permanent_stat_modified",
            entity_id="e1",
            ability=Ability.STR,
            modifier_type=PermanentModifierType.DRAIN,
            amount=+1,
            source="shadow_strength_drain",
            reversible=True,
        )

    # inherent must be positive
    with pytest.raises(ValueError):
        PermanentStatModifiedEvent(
            event_type="permanent_stat_modified",
            entity_id="e1",
            ability=Ability.INT,
            modifier_type=PermanentModifierType.INHERENT,
            amount=-1,
            source="wish",
            reversible=False,
        )

    # amount cannot be zero
    with pytest.raises(ValueError):
        PermanentStatModifiedEvent(
            event_type="permanent_stat_modified",
            entity_id="e1",
            ability=Ability.INT,
            modifier_type=PermanentModifierType.INHERENT,
            amount=0,
            source="wish",
            reversible=False,
        )

    ev = PermanentStatModifiedEvent(
        event_type="permanent_stat_modified",
        entity_id="e1",
        ability=Ability.CON,
        modifier_type=PermanentModifierType.DRAIN,
        amount=-4,
        source="vampire_con_drain",
        reversible=True,
    )
    d = ev.to_dict()
    assert list(d.keys()) == [
        "event_type",
        "entity_id",
        "ability",
        "modifier_type",
        "amount",
        "source",
        "reversible",
    ]
    assert PermanentStatModifiedEvent.from_dict(d) == ev


def test_event_permanent_stat_restored_validation():
    # amount_removed must be positive
    with pytest.raises(ValueError):
        PermanentStatRestoredEvent(
            event_type="permanent_stat_restored",
            entity_id="e1",
            ability=Ability.STR,
            modifier_type=PermanentModifierType.DRAIN,
            amount_removed=0,
            source="restoration_spell",
        )

    # must be drain
    with pytest.raises(ValueError):
        PermanentStatRestoredEvent(
            event_type="permanent_stat_restored",
            entity_id="e1",
            ability=Ability.STR,
            modifier_type=PermanentModifierType.INHERENT,
            amount_removed=1,
            source="restoration_spell",
        )

    ev = PermanentStatRestoredEvent(
        event_type="permanent_stat_restored",
        entity_id="e1",
        ability=Ability.STR,
        modifier_type=PermanentModifierType.DRAIN,
        amount_removed=2,
        source="restoration_spell",
    )
    assert PermanentStatRestoredEvent.from_dict(ev.to_dict()) == ev


def test_event_derived_stats_recalculated_validation_roundtrip():
    ev = DerivedStatsRecalculatedEvent(
        event_type="derived_stats_recalculated",
        entity_id="e1",
        ability_affected=Ability.CON,
        old_effective_score=14,
        new_effective_score=10,
        hp_max_old=45,
        hp_max_new=35,
        recalculated_stats=["hp_max", "fortitude_save"],
    )
    d = ev.to_dict()
    assert list(d.keys()) == [
        "event_type",
        "entity_id",
        "ability_affected",
        "old_effective_score",
        "new_effective_score",
        "hp_max_old",
        "hp_max_new",
        "recalculated_stats",
    ]
    assert DerivedStatsRecalculatedEvent.from_dict(d) == ev

    # scores must be >= 0 (floor enforced later, but schema blocks negatives)
    with pytest.raises(ValueError):
        DerivedStatsRecalculatedEvent(
            event_type="derived_stats_recalculated",
            entity_id="e1",
            ability_affected=Ability.CON,
            old_effective_score=14,
            new_effective_score=-1,
            hp_max_old=45,
            hp_max_new=35,
            recalculated_stats=["hp_max"],
        )


def test_event_ability_score_death_validation_roundtrip():
    ev = AbilityScoreDeathEvent(
        event_type="ability_score_death",
        entity_id="e1",
        ability=Ability.STR,
        final_score=0,
        cause="shadow_strength_drain",
    )
    assert AbilityScoreDeathEvent.from_dict(ev.to_dict()) == ev

    with pytest.raises(ValueError):
        AbilityScoreDeathEvent(
            event_type="ability_score_death",
            entity_id="e1",
            ability=Ability.STR,
            final_score=1,
            cause="shadow_strength_drain",
        )


def test_entity_state_integration_roundtrip_and_separation():
    ent = EntityState(entity_id="e1", base_stats={"str": 16, "con": 14})
    d = ent.to_dict()
    assert "permanent_stat_modifiers" in d
    assert "temporary_modifiers" in d

    ent2 = EntityState.from_dict(d)
    assert ent2.to_dict() == d

    # Ensure permanent and temporary are distinct objects/fields.
    assert "drain" in ent2.permanent_stat_modifiers.to_dict()["str"]
    assert isinstance(ent2.temporary_modifiers, dict)
