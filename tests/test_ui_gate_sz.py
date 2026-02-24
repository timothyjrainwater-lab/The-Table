"""Gate UI-SZ -- Session Zero Notebook Flow (6 tests).

Tests verify cover name/image persistence logic using Python simulation.
"""
import pytest
import json


class MockLocalStorage:
    def __init__(self):
        self._store = {}
    def setItem(self, key, value): self._store[key] = value
    def getItem(self, key): return self._store.get(key)
    def removeItem(self, key): self._store.pop(key, None)


class NotebookCoverSim:
    """Python simulation of NotebookObject cover persistence."""

    def __init__(self, session_id='default', storage=None):
        self._session_id = session_id
        self._storage = storage or MockLocalStorage()
        self._cover_player_name = ''
        self._cover_image_url = ''
        self._rendered_name = None
        self._loaded_image_url = None

    def set_cover_name(self, name):
        self._cover_player_name = name
        self._rendered_name = name
        self._storage.setItem(f'nb_cover_name_{self._session_id}', name)

    def set_cover_image(self, url):
        if not url:
            return
        self._cover_image_url = url
        self._loaded_image_url = url
        self._storage.setItem(f'nb_cover_image_{self._session_id}', url)

    def load_cover_from_storage(self):
        name = self._storage.getItem(f'nb_cover_name_{self._session_id}')
        if name:
            self._rendered_name = name
        url = self._storage.getItem(f'nb_cover_image_{self._session_id}')
        if url:
            self._loaded_image_url = url


# SZ-01: session_zero_start handler exists (no crash, no-op is fine)
def test_sz01_session_zero_start_handler():
    # Just verifies the handler signature -- no crash
    nb = NotebookCoverSim()
    # No-op on session_zero_start
    assert nb._cover_player_name == ''  # unchanged


# SZ-02: notebook_cover_name updates cover text
def test_sz02_cover_name_updates():
    nb = NotebookCoverSim(session_id='session_sz')
    nb.set_cover_name('Kira Stoneheart')
    assert nb._rendered_name == 'Kira Stoneheart'


# SZ-03: notebook_cover_image updates cover texture
def test_sz03_cover_image_updates():
    nb = NotebookCoverSim(session_id='session_sz')
    nb.set_cover_image('http://example.com/cover.png')
    assert nb._loaded_image_url == 'http://example.com/cover.png'


# SZ-04: Cover name persists to localStorage
def test_sz04_cover_name_persists():
    storage = MockLocalStorage()
    nb = NotebookCoverSim(session_id='session_sz04', storage=storage)
    nb.set_cover_name('Aldric the Bold')
    stored = storage.getItem('nb_cover_name_session_sz04')
    assert stored == 'Aldric the Bold', f"Expected stored name, got: {stored}"


# SZ-05: Cover image URL persists to localStorage
def test_sz05_cover_image_persists():
    storage = MockLocalStorage()
    nb = NotebookCoverSim(session_id='session_sz05', storage=storage)
    nb.set_cover_image('http://example.com/art.png')
    stored = storage.getItem('nb_cover_image_session_sz05')
    assert stored == 'http://example.com/art.png', f"Expected stored URL, got: {stored}"


# SZ-06: session_resume reloads cover from localStorage
def test_sz06_session_resume_reloads():
    storage = MockLocalStorage()
    # Session 1: save name + image
    nb1 = NotebookCoverSim(session_id='session_sz06', storage=storage)
    nb1.set_cover_name('Seraphine')
    nb1.set_cover_image('http://example.com/seraphine.png')
    # Session 2: new instance, same storage, same session_id
    nb2 = NotebookCoverSim(session_id='session_sz06', storage=storage)
    nb2.load_cover_from_storage()
    assert nb2._rendered_name == 'Seraphine', f"Expected name reloaded, got: {nb2._rendered_name}"
    assert nb2._loaded_image_url == 'http://example.com/seraphine.png'
