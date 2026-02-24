"""Gate: Bestiary Image Binding (4 tests — regression guard)."""
import pytest


REVEAL_LEVELS = {'heard': 0.15, 'seen': 0.45, 'fought': 0.70, 'studied': 1.0}


class BestiaryBindSim:
    def __init__(self):
        self._current = None
        self._updates = []

    def handle_reveal(self, creature_id, knowledge_state, image_url=None, name=None, traits=None):
        entry = {
            'creature_id': creature_id,
            'knowledge_state': knowledge_state,
            'image_url': image_url,
            'name': name,
            'traits': traits or [],
        }
        self._current = entry
        opacity = REVEAL_LEVELS.get(knowledge_state, 0)
        self._updates.append({'entry': entry, 'opacity': opacity})

    @property
    def current(self): return self._current


def test_bestiary01_heard_dim():
    b = BestiaryBindSim()
    b.handle_reveal('goblin', 'heard')
    assert b._updates[-1]['opacity'] == 0.15

def test_bestiary02_studied_full():
    b = BestiaryBindSim()
    b.handle_reveal('dragon', 'studied', image_url='http://example.com/dragon.png')
    assert b._updates[-1]['opacity'] == 1.0
    assert b.current['image_url'] == 'http://example.com/dragon.png'

def test_bestiary03_progressive_reveal():
    b = BestiaryBindSim()
    states = ['heard', 'seen', 'fought', 'studied']
    for s in states:
        b.handle_reveal('orc', s)
    opacities = [u['opacity'] for u in b._updates]
    assert opacities == [0.15, 0.45, 0.70, 1.0]

def test_bestiary04_current_updates():
    b = BestiaryBindSim()
    b.handle_reveal('troll', 'seen', name='Cave Troll')
    assert b.current['creature_id'] == 'troll'
    assert b.current['knowledge_state'] == 'seen'
    assert b.current['name'] == 'Cave Troll'
