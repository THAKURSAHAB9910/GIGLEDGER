"""GIGLEDGER REST API Package.
Provides production endpoints for decoupled backend hosting (Render, Railway, Fly.io, AWS).
"""
from src.api.main import app

__all__ = ["app"]
