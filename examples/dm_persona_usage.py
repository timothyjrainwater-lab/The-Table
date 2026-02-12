"""Example: Using DMPersona with NarrativeBrief and ContextAssembler

Demonstrates how to use the DM Personality Layer (WO-041) to build
consistent system prompts for Spark narration generation.
"""

from aidm.spark import DMPersona, ToneConfig, create_theatrical_dm
from aidm.lens import NarrativeBrief, ContextAssembler


def example_basic_usage():
    """Basic DMPersona usage with default tone."""
    # Create default DM persona
    dm = DMPersona()

    # Create narrative brief
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric the Bold",
        target_name="Goblin Chieftain",
        outcome_summary="Aldric strikes Goblin Chieftain with longsword",
        severity="devastating",
        weapon_name="longsword",
        damage_type="slashing",
        scene_description="A torch-lit dungeon corridor",
    )

    # Build system prompt
    system_prompt = dm.build_system_prompt(brief)

    print("=== Basic System Prompt ===")
    print(system_prompt)
    print()


def example_custom_tone():
    """DMPersona with custom tone configuration."""
    # Create theatrical DM (high drama, high verbosity)
    tone = ToneConfig(gravity=0.8, verbosity=0.9, drama=0.9)
    dm = DMPersona(tone=tone)

    # Create narrative brief
    brief = NarrativeBrief(
        action_type="spell_damage",
        actor_name="Malakar the Dark",
        target_name="Aldric the Bold",
        outcome_summary="Malakar casts fireball",
        severity="devastating",
        target_defeated=False,
        scene_description="The throne room erupts in flames",
    )

    # Build system prompt with theatrical tone
    system_prompt = dm.build_system_prompt(brief)

    print("=== Theatrical System Prompt ===")
    print(system_prompt)
    print()


def example_with_session_context():
    """DMPersona with session context from ContextAssembler."""
    # Create context assembler
    assembler = ContextAssembler(token_budget=800)

    # Create narrative brief with previous narrations
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric the Bold",
        target_name="Goblin Chieftain",
        outcome_summary="Aldric strikes",
        severity="severe",
        weapon_name="longsword",
        previous_narrations=[
            "The goblin chieftain roars in fury!",
            "Aldric circles to the side, blade ready.",
            "The two warriors clash in the narrow passage.",
        ],
    )

    # Assemble context
    context = assembler.assemble(brief)

    # Create DM persona and build prompt with context
    dm = DMPersona()
    system_prompt = dm.build_system_prompt(brief, session_context=context)

    print("=== System Prompt with Session Context ===")
    print(system_prompt)
    print()


def example_npc_characterization():
    """DMPersona with NPC voice mapping and characterization."""
    # Create DM persona
    dm = DMPersona()

    # Register recurring NPC with voice and personality
    dm.register_npc(
        npc_name="Malakar the Dark",
        voice_id="en_us_male_villain_deep",
        personality_traits=["arrogant", "theatrical", "power-hungry", "cunning"],
    )

    # Create brief featuring the NPC
    brief = NarrativeBrief(
        action_type="spell_damage",
        actor_name="Malakar the Dark",
        target_name="Party",
        outcome_summary="Malakar unleashes dark magic",
        severity="devastating",
        scene_description="The lich's tower trembles with arcane power",
    )

    # Build system prompt (includes NPC characterization)
    system_prompt = dm.build_system_prompt(brief)

    # Get NPC voice for TTS
    voice_id = dm.get_npc_voice("Malakar the Dark")

    print("=== System Prompt with NPC Characterization ===")
    print(system_prompt)
    print(f"\nNPC Voice ID: {voice_id}")
    print()


def example_preset_personas():
    """Using preset DM persona factories."""
    # Create brief
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Fighter",
        target_name="Dragon",
        outcome_summary="Fighter strikes Dragon",
        severity="moderate",
    )

    # Gritty DM (serious, understated)
    gritty_dm = create_theatrical_dm()
    gritty_prompt = gritty_dm.build_system_prompt(brief)

    print("=== Gritty DM Prompt ===")
    print(gritty_prompt[:200] + "...")
    print()


def example_full_pipeline():
    """Full pipeline: NarrativeBrief → ContextAssembler → DMPersona → Spark."""
    # Step 1: Create narrative brief (from Box STP events)
    brief = NarrativeBrief(
        action_type="attack_hit",
        actor_name="Aldric the Bold",
        target_name="Goblin Chieftain",
        outcome_summary="Aldric strikes Goblin Chieftain with longsword",
        severity="devastating",
        weapon_name="longsword",
        damage_type="slashing",
        scene_description="A narrow dungeon corridor",
        previous_narrations=[
            "The goblin chieftain raises its crude axe!",
            "Aldric advances cautiously through the shadows.",
        ],
    )

    # Step 2: Assemble context within token budget
    assembler = ContextAssembler(token_budget=800)
    context = assembler.assemble(brief)

    # Step 3: Build DM system prompt with tone
    dm = DMPersona(tone=ToneConfig(gravity=0.7, verbosity=0.6, drama=0.7))
    system_prompt = dm.build_system_prompt(brief, session_context=context)

    # Step 4: Send to Spark (example - actual integration happens in GuardedNarrationService)
    # spark_request = SparkRequest(
    #     prompt=system_prompt,
    #     temperature=0.8,
    #     max_tokens=150,
    # )
    # response = spark_adapter.generate(spark_request)

    print("=== Full Pipeline: System Prompt ===")
    print(system_prompt)
    print()

    print("=== Context Budget ===")
    print(f"Token estimate: {assembler._estimate_tokens(context)} / {assembler.token_budget}")
    print()


if __name__ == "__main__":
    print("DMPersona Examples\n" + "=" * 60 + "\n")

    example_basic_usage()
    example_custom_tone()
    example_with_session_context()
    example_npc_characterization()
    example_preset_personas()
    example_full_pipeline()
