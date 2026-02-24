"""Gate: Cup Holder Soft Delete (3 tests — regression guard)."""
import pytest


MAX_STACK = 5


class SoftDeleteSim:
    def __init__(self):
        self._stack = []
        self.change_count = 0

    def push(self, id_, visible=True):
        if len(self._stack) >= MAX_STACK:
            return False
        self._stack.append({'id': id_, 'visible': True, 'dimmed': True})
        self.change_count += 1
        return True

    def pop(self):
        if not self._stack:
            return None
        item = self._stack.pop()
        item['dimmed'] = False
        self.change_count += 1
        return item

    @property
    def count(self): return len(self._stack)
    @property
    def is_full(self): return len(self._stack) >= MAX_STACK
    @property
    def is_empty(self): return len(self._stack) == 0


def test_cup01_push_dims_item():
    s = SoftDeleteSim()
    s.push('obj_1')
    assert s.count == 1
    assert s._stack[0]['dimmed'] is True

def test_cup02_pop_retrieves():
    s = SoftDeleteSim()
    s.push('obj_1')
    s.push('obj_2')
    item = s.pop()
    assert item['id'] == 'obj_2'  # LIFO
    assert s.count == 1

def test_cup03_max_5_items():
    s = SoftDeleteSim()
    for i in range(5):
        assert s.push(f'obj_{i}') is True
    assert s.is_full is True
    assert s.push('obj_overflow') is False
    assert s.count == 5
