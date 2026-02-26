"""
Web UI module for Mossy Manager.
Provides FastAPI application and builder functions for the web interface.
"""

from mossy_manager.webui.app import app, build_app

__all__ = ['app', 'build_app']
