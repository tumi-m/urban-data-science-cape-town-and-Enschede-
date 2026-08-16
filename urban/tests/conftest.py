"""Pytest configuration: ensure the project root is on sys.path.

This lets tests import the `urban` package directly.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
