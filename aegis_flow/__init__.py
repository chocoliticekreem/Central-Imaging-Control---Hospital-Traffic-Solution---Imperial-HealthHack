"""
Aegis Flow - shim package
=========================

This file is a small compatibility shim so existing imports like
`import aegis_flow.api` keep working after the real backend package was
moved into `backend/aegis_flow` during a reorganization.

The shim prepends `backend/aegis_flow` to the package `__path__` when it
exists, allowing Python to find submodules there transparently.
"""

import os

# Path to the moved backend package (relative to this file)
_backend_candidate = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "backend", "aegis_flow")
)

if os.path.isdir(_backend_candidate):
    __path__.insert(0, _backend_candidate)

# Keep a simple version fallback
__version__ = "0.1.0"
