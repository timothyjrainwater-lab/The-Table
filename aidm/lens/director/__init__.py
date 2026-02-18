"""Director — small deterministic beat selector inside Lens.

Director chooses "what happens next" from existing Oracle content using
a deterministic priority cascade.  It emits BeatIntent + NudgeDirective.
It never invents canon, writes stores, or overrides Box outcomes.

Authority: Director Spec v0, GT v12 DIR-001..DIR-005, Lens Spec v0.
"""
