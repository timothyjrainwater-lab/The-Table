"""Shared test fixtures and cleanup hooks.

Ensures cross-test cleanup for resources that can leak between test modules
(daemon threads, background managers, etc.).
"""
