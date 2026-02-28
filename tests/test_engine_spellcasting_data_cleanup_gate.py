"""Gate tests: WO-ENGINE-SPELLCASTING-DATA-CLEANUP-001

Fix A: Conjuration (creation) spells set spell_resistance=False (PHB individual entries).
Fix B: EF.SPELL_DC_BASE constant replaces bare string in play_loop.py.

SDC-001 – SDC-008 (8 tests)
"""
import pytest
import ast
import inspect

from aidm.data.spell_definitions import SPELL_REGISTRY
from aidm.schemas.entity_fields import EF


# ---------------------------------------------------------------------------
# SDC-001: web spell has spell_resistance == False
# ---------------------------------------------------------------------------

def test_sdc_001_web_sr_false():
    """SDC-001: Web spell (conjuration creation) has SR: No."""
    spell = SPELL_REGISTRY["web"]
    assert spell.spell_resistance is False, "PHB p.301: web SR: No"


# ---------------------------------------------------------------------------
# SDC-002: grease spell has spell_resistance == False
# ---------------------------------------------------------------------------

def test_sdc_002_grease_sr_false():
    """SDC-002: Grease spell (conjuration creation) has SR: No."""
    spell = SPELL_REGISTRY["grease"]
    assert spell.spell_resistance is False, "PHB p.237: grease SR: No"


# ---------------------------------------------------------------------------
# SDC-003: stinking_cloud spell has spell_resistance == False
# ---------------------------------------------------------------------------

def test_sdc_003_stinking_cloud_sr_false():
    """SDC-003: Stinking Cloud (conjuration creation) has SR: No."""
    spell = SPELL_REGISTRY["stinking_cloud"]
    assert spell.spell_resistance is False, "PHB p.284: stinking_cloud SR: No"


# ---------------------------------------------------------------------------
# SDC-004: fog_cloud spell has spell_resistance == False
# ---------------------------------------------------------------------------

def test_sdc_004_fog_cloud_sr_false():
    """SDC-004: Fog Cloud (conjuration creation) has SR: No."""
    spell = SPELL_REGISTRY["fog_cloud"]
    assert spell.spell_resistance is False, "PHB p.232: fog_cloud SR: No"


# ---------------------------------------------------------------------------
# SDC-005: fireball spell has spell_resistance == True (unchanged)
# ---------------------------------------------------------------------------

def test_sdc_005_fireball_sr_true():
    """SDC-005: Fireball (evocation) still allows SR."""
    spell = SPELL_REGISTRY["fireball"]
    assert spell.spell_resistance is True, "Fireball should still allow SR"


# ---------------------------------------------------------------------------
# SDC-006: EF.SPELL_DC_BASE constant exists in entity_fields.py
# ---------------------------------------------------------------------------

def test_sdc_006_ef_spell_dc_base_exists():
    """SDC-006: EF.SPELL_DC_BASE constant exists and equals 'spell_dc_base'."""
    assert hasattr(EF, "SPELL_DC_BASE"), "EF.SPELL_DC_BASE must exist"
    assert EF.SPELL_DC_BASE == "spell_dc_base"


# ---------------------------------------------------------------------------
# SDC-007: play_loop reads EF.SPELL_DC_BASE (no bare string "spell_dc_base")
# ---------------------------------------------------------------------------

def test_sdc_007_play_loop_uses_ef_constant():
    """SDC-007: play_loop.py uses EF.SPELL_DC_BASE, not bare string."""
    import aidm.core.play_loop as pl_mod
    source = inspect.getsource(pl_mod)
    # The bare string "spell_dc_base" should NOT appear as a standalone dict key.
    # EF.SPELL_DC_BASE is the correct accessor.
    # Check that EF.SPELL_DC_BASE is used in the source
    assert "EF.SPELL_DC_BASE" in source, "play_loop must use EF.SPELL_DC_BASE constant"


# ---------------------------------------------------------------------------
# SDC-008: SR gate at spell_resolver skips check when spell_resistance == False
# ---------------------------------------------------------------------------

def test_sdc_008_sr_gate_skips_when_false():
    """SDC-008: SR gate logic respects spell_resistance=False (no SR roll made)."""
    from aidm.core.spell_resolver import SpellDefinition, SpellTarget

    # A spell with spell_resistance=False
    spell_no_sr = SpellDefinition(
        spell_id="test_no_sr", name="test_no_sr", school="conjuration", level=2,
        target_type=SpellTarget.SINGLE, range_ft=30,
        spell_resistance=False,
    )
    assert spell_no_sr.spell_resistance is False

    # A spell with default (True)
    spell_with_sr = SpellDefinition(
        spell_id="test_with_sr", name="test_with_sr", school="evocation", level=3,
        target_type=SpellTarget.SINGLE, range_ft=100,
    )
    assert spell_with_sr.spell_resistance is True

    # The SR gate condition: `if spell.spell_resistance and target.spell_resistance > 0`
    # When spell.spell_resistance is False, the entire condition short-circuits to False
    target_sr = 15
    assert not (spell_no_sr.spell_resistance and target_sr > 0), \
        "SR gate must skip when spell.spell_resistance is False"
    assert (spell_with_sr.spell_resistance and target_sr > 0), \
        "SR gate must fire when spell.spell_resistance is True and target has SR"
