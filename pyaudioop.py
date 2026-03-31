"""Compatibility shim for Python 3.14 where stdlib audioop is removed.

This module exposes the bundled fallback implementation shipped with pydub
under the top-level name expected by pydub.utils and ShazamAPI.
"""

from importlib import import_module


_pyaudioop = import_module("pydub.pyaudioop")


for _name in dir(_pyaudioop):
    if _name.startswith("__"):
        continue
    globals()[_name] = getattr(_pyaudioop, _name)
