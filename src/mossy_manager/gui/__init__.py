"""
Mossy Manager – standalone desktop GUI (tkinter).

This package provides a self-contained MO2-style window that runs without
a browser or web server.  It is the primary user interface for the tool.

See UI_MANIFEST at the repository root for the authoritative UI architecture
specification.  DO NOT convert this package to a web-based UI.
"""

from mossy_manager.gui.app import DesktopApp, launch

__all__ = ["DesktopApp", "launch"]
