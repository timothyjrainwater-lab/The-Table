"""Gate: Rulebook Navigation (3 tests — regression guard)."""
import pytest


KNOWN_REFS = [
    {'ref': 'combat.attack_roll', 'aliases': ['attack', 'attack roll', 'to hit']},
    {'ref': 'combat.basics',      'aliases': ['combat', 'basic combat', 'fighting']},
    {'ref': 'combat.actions',     'aliases': ['actions', 'action types', 'standard action', 'move action']},
    {'ref': 'combat.action_types','aliases': ['full round', 'full-round', 'swift', 'immediate', 'free action']},
    {'ref': 'conditions',         'aliases': ['conditions', 'status', 'blinded', 'fatigued', 'prone', 'stunned']},
    {'ref': 'conditions.list',    'aliases': ['condition list', 'all conditions']},
]
DEFAULT_REF = 'combat.basics'


def search_rule_ref(query):
    q = query.lower().strip()
    if not q:
        return DEFAULT_REF
    for entry in KNOWN_REFS:
        if q in entry['ref']:
            return entry['ref']
        if any(q in a or a in q for a in entry['aliases']):
            return entry['ref']
    return DEFAULT_REF


class RulebookSim:
    def __init__(self):
        self.current_ref = None
        self.opens = []

    def open_to_ref(self, ref):
        self.current_ref = ref
        self.opens.append(ref)

    def handle_rulebook_open(self, rule_ref):
        self.open_to_ref(rule_ref)

    def handle_rulebook_search(self, query):
        ref = search_rule_ref(query)
        self.open_to_ref(ref)


def test_rulebook01_direct_open():
    rb = RulebookSim()
    rb.handle_rulebook_open('conditions')
    assert rb.current_ref == 'conditions'

def test_rulebook02_search_finds_match():
    rb = RulebookSim()
    rb.handle_rulebook_search('grappling')  # no match → default
    assert rb.current_ref == DEFAULT_REF
    rb.handle_rulebook_search('attack')
    assert rb.current_ref == 'combat.attack_roll'

def test_rulebook03_search_fallback():
    rb = RulebookSim()
    rb.handle_rulebook_search('')  # empty → default
    assert rb.current_ref == DEFAULT_REF
    rb.handle_rulebook_search('zzz_nonexistent')
    assert rb.current_ref == DEFAULT_REF
