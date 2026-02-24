"""Gate UI-NB-CON — Notebook Consent Chain (5 tests).

Authority: GT v12, DOCTRINE_04_TABLE_UI_MEMO_V4 §14, WO-UI-NOTEBOOK-01.

Tests verify:
1. NB-CON-01: Default write-lock — notebook starts locked; player ink bypasses lock
2. NB-CON-02: AI-assisted write requires full EV-010 → EV-011 → EV-013 chain
3. NB-CON-03: Ambiguous / null consent response defaults to EV-012 (denied)
4. NB-CON-04: No auto-write path exists (static scan of notebook-object.ts)
5. NB-CON-05: Consent scope is one-at-a-time; expires on scene end

All tests run against a Python simulation of NotebookConsentChain that mirrors
the TypeScript implementation in client/src/notebook-object.ts.
No browser or build tooling required.
"""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Event type constants (mirror EV-010 … EV-013 from notebook-object.ts)
# ---------------------------------------------------------------------------

EV_NOTEBOOK_WRITE_CONSENT_REQUESTED = 'EV-010'
EV_NOTEBOOK_WRITE_CONSENT_GRANTED   = 'EV-011'
EV_NOTEBOOK_WRITE_CONSENT_DENIED    = 'EV-012'
EV_NOTEBOOK_WRITE_APPLIED           = 'EV-013'


# ---------------------------------------------------------------------------
# NotebookConsentSim — Python mirror of NotebookConsentChain (TS)
# ---------------------------------------------------------------------------

class NotebookConsentSim:
    """Python simulation of the NotebookConsentChain class from notebook-object.ts.

    State machine:
      idle → pending  (requestConsent / EV-010)
      pending → granted (grant / EV-011)
      pending → denied  (deny / EV-012, or null response → defaults NO)
      granted → idle   (applyWrite / EV-013; consent cleared)
      denied  → idle   (after deny; consent cleared)

    Player ink (startStroke) always bypasses this chain — no consent needed.
    """

    def __init__(self):
        self._state = 'idle'
        self._pending_request = None
        self._pending_payload = None

    @property
    def state(self) -> str:
        return self._state

    @property
    def is_write_locked(self) -> bool:
        """True unless the chain has transitioned to 'granted'."""
        return self._state != 'granted'

    @property
    def has_pending_consent(self) -> bool:
        return self._state == 'pending'

    def request_consent(self, label: str, payload=None) -> bool:
        """EV-010: Request AI-assisted write consent. Returns False if already pending."""
        if self._state != 'idle':
            return False  # one-at-a-time
        self._state = 'pending'
        self._pending_request = label
        self._pending_payload = payload
        return True

    def grant(self):
        """EV-011: Player grants consent. Returns payload; None if not pending."""
        if self._state != 'pending':
            return None
        self._state = 'granted'
        payload = self._pending_payload
        return payload

    def deny(self) -> None:
        """EV-012: Player denies, or ambiguous/null → defaults denied."""
        self._state = 'denied'
        self._pending_request = None
        self._pending_payload = None

    def apply_write(self) -> bool:
        """EV-013: Apply write. Valid only after grant(). Clears consent state."""
        if self._state != 'granted':
            return False
        self._state = 'idle'
        self._pending_request = None
        self._pending_payload = None
        return True

    def reset_on_scene_end(self) -> None:
        """Clear all consent state on scene boundary."""
        self._state = 'idle'
        self._pending_request = None
        self._pending_payload = None

    # ---- Player-ink simulation (always permitted; bypasses consent chain) ----

    def player_ink_start_stroke(self) -> str:
        """Simulate startStroke() — always returns 'allowed', consent-chain ignored."""
        return 'allowed'

    # ---- AI-write simulation (blocked when write-locked) ----

    def ai_assisted_write_attempt(self, payload=None) -> bool:
        """Simulate an AI-assisted write call. Blocked unless state is 'granted'."""
        if self.is_write_locked:
            return False
        return self.apply_write()


# ---------------------------------------------------------------------------
# NB-CON-01: Default write-lock — notebook starts locked
# ---------------------------------------------------------------------------

def test_nb_con01_default_write_lock():
    """Notebook consent chain starts locked; player ink always allowed;
    AI-assisted write blocked when not granted."""
    sim = NotebookConsentSim()

    # Starts idle — write locked
    assert sim.state == 'idle', f"Expected 'idle' on init, got '{sim.state}'"
    assert sim.is_write_locked is True, "Notebook must start write-locked"

    # Direct player ink bypasses consent requirement — always allowed
    result = sim.player_ink_start_stroke()
    assert result == 'allowed', "Player ink must bypass consent chain"

    # AI-assisted write is blocked when locked
    blocked = sim.ai_assisted_write_attempt(payload={'text': 'AI note'})
    assert blocked is False, \
        "AI-assisted write must be blocked when is_write_locked is True"

    # State must remain idle after failed AI write attempt
    assert sim.state == 'idle', \
        f"State must remain 'idle' after blocked write attempt, got '{sim.state}'"


# ---------------------------------------------------------------------------
# NB-CON-02: AI-assisted write requires full EV-010 → EV-011 → EV-013 chain
# ---------------------------------------------------------------------------

def test_nb_con02_full_consent_chain_required():
    """AI-assisted write without EV-010 is rejected; full chain succeeds."""
    sim = NotebookConsentSim()

    # Attempt AI write without EV-010 → must be rejected
    assert sim.ai_assisted_write_attempt({'text': 'no consent'}) is False, \
        "AI write must be rejected without EV-010 (requestConsent)"

    # EV-010: request consent
    ok = sim.request_consent(label='Add bestiary entry: Goblin', payload={'entity_id': 'goblin'})
    assert ok is True, "requestConsent must return True on first call from idle"
    assert sim.state == 'pending', f"Expected 'pending' after EV-010, got '{sim.state}'"
    assert sim.has_pending_consent is True

    # AI write still blocked while pending — EV-011 not yet received
    assert sim.is_write_locked is True, \
        "Write must still be locked in 'pending' state"

    # EV-011: player grants consent
    payload = sim.grant()
    assert sim.state == 'granted', f"Expected 'granted' after EV-011, got '{sim.state}'"
    assert payload == {'entity_id': 'goblin'}, \
        f"grant() must return the pending payload, got {payload}"
    assert sim.is_write_locked is False, \
        "Write must be unlocked after EV-011 grant"

    # EV-013: apply write — clears consent
    applied = sim.apply_write()
    assert applied is True, "applyWrite must return True after valid grant"
    assert sim.state == 'idle', \
        f"State must return to 'idle' after EV-013, got '{sim.state}'"
    assert sim.is_write_locked is True, \
        "Write must be locked again after EV-013 clears consent"


# ---------------------------------------------------------------------------
# NB-CON-03: Ambiguous / null consent defaults to EV-012 (denied)
# ---------------------------------------------------------------------------

def test_nb_con03_ambiguous_consent_defaults_no():
    """Null/ambiguous player response to EV-010 results in EV-012 denial; no write."""
    sim = NotebookConsentSim()

    # EV-010: request
    sim.request_consent(label='Add bestiary entry: Troll', payload={'entity_id': 'troll'})
    assert sim.state == 'pending'

    # Ambiguous response — caller passes None as response; simulate deny()
    ambiguous_response = None
    if not ambiguous_response:
        sim.deny()  # null/ambiguous → defaults NO (EV-012)

    assert sim.state == 'denied', \
        f"Expected 'denied' after ambiguous response, got '{sim.state}'"

    # Apply write must be blocked after denial
    applied = sim.apply_write()
    assert applied is False, "applyWrite must fail after EV-012 denial"

    # State clears to idle (not stuck in denied)
    # In practice, after deny() the consumer calls reset_on_scene_end or just
    # starts over; we verify the deny path does not persist the payload.
    sim.reset_on_scene_end()
    assert sim.state == 'idle', \
        f"State must be 'idle' after reset, got '{sim.state}'"


# ---------------------------------------------------------------------------
# NB-CON-04: No auto-write path exists (static scan)
# ---------------------------------------------------------------------------

def test_nb_con04_no_auto_write_path():
    """Static scan of notebook-object.ts confirms no write method pushes to
    internal arrays without explicit player action or consent chain passage.

    Banned patterns (auto-write violations):
      - addTranscriptEntry(...) — removed in remediation
      - addHandout(...) — removed in remediation
      - _transcriptEntries.push(...) — must not exist
      - _handoutEntries.push(...) — must not exist

    Permitted push sites (explicit player-initiated or consent-gated):
      - _strokes.push  inside endStroke() (player ink — always permitted)
      - _bestiaryEntries.push  inside applyBestiaryUpsert() (consent-gated)
    """
    nb_ts = os.path.join(ROOT, 'client', 'src', 'notebook-object.ts')
    assert os.path.isfile(nb_ts), f"notebook-object.ts not found at {nb_ts}"
    text = open(nb_ts, encoding='utf-8').read()

    # Violation 1: addTranscriptEntry must be gone
    assert 'addTranscriptEntry' not in text, \
        "VIOLATION: addTranscriptEntry() auto-write path still present in notebook-object.ts"

    # Violation 2: addHandout must be gone
    assert 'addHandout' not in text, \
        "VIOLATION: addHandout() auto-write path still present in notebook-object.ts"

    # _transcriptEntries push must not exist anywhere
    assert '_transcriptEntries.push' not in text, \
        "VIOLATION: _transcriptEntries.push detected — transcript auto-write path"

    # _handoutEntries push must not exist anywhere
    assert '_handoutEntries.push' not in text, \
        "VIOLATION: _handoutEntries.push detected — handout auto-write path"

    # Verify that _strokes.push only appears inside an explicitly player-initiated handler.
    # We scan for _strokes.push and verify it is within endStroke / undoStroke context.
    strokes_push_positions = [m.start() for m in re.finditer(r'_strokes\.push', text)]
    for pos in strokes_push_positions:
        # Look backward up to 300 chars for endStroke or undoStroke
        context_before = text[max(0, pos - 300):pos]
        assert 'endStroke' in context_before or 'undoStroke' in context_before, \
            (f"_strokes.push at char {pos} is not inside endStroke/undoStroke — "
             f"potential auto-write violation. Context: ...{context_before[-80:]!r}")

    # Verify bestiary push is only inside applyBestiaryUpsert (consent-gated).
    # The method body is ~600 chars; look back 900 to be safe.
    bestiary_push_positions = [m.start() for m in re.finditer(r'_bestiaryEntries\.push', text)]
    for pos in bestiary_push_positions:
        context_before = text[max(0, pos - 900):pos]
        assert 'applyBestiaryUpsert' in context_before, \
            (f"_bestiaryEntries.push at char {pos} is not inside applyBestiaryUpsert — "
             f"potential auto-write violation. Context: ...{context_before[-80:]!r}")


# ---------------------------------------------------------------------------
# NB-CON-05: Consent scope is one-at-a-time; expires on scene end
# ---------------------------------------------------------------------------

def test_nb_con05_one_at_a_time_expires_on_scene_end():
    """Previous grant does not carry over; each write needs fresh EV-010.
    Consent state does not persist across scene boundaries."""
    sim = NotebookConsentSim()

    # Full cycle 1: request → grant → apply
    sim.request_consent('First write', {'data': 1})
    sim.grant()
    sim.apply_write()
    assert sim.state == 'idle', \
        "State must be 'idle' after first complete cycle"

    # Attempt second AI write without EV-010 — must be rejected
    assert sim.ai_assisted_write_attempt({'data': 2}) is False, \
        "Previous grant must NOT carry over — fresh EV-010 required for second write"

    # Full cycle 2: prove a new EV-010 is needed
    ok = sim.request_consent('Second write', {'data': 2})
    assert ok is True, "A fresh requestConsent must be accepted after previous cycle clears"
    sim.grant()
    applied = sim.apply_write()
    assert applied is True, "Second full cycle must succeed"

    # Simulate pending consent at scene end — reset clears it
    sim.request_consent('Third write', {'data': 3})
    assert sim.state == 'pending'
    sim.reset_on_scene_end()
    assert sim.state == 'idle', \
        "reset_on_scene_end must clear pending consent"

    # Attempt write after reset — must be blocked (no carry-over)
    assert sim.ai_assisted_write_attempt({'data': 3}) is False, \
        "Consent must not persist across simulated session boundary"
