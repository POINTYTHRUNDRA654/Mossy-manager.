"""
MossyManager GUI entry point.

This script is the executable launched by Mod Organizer 2.
It opens the self-contained desktop window immediately, with no CLI arguments
required.  MO2 simply runs this file and the window appears.

Supported flags (handled BEFORE any GUI imports so they work headlessly in CI):
  --version / -V       Print version and exit (exit code 0)
  --help    / -h       Print usage and exit (exit code 0)
  --mo2-path PATH / -m PATH
                       Path to MO2 installation (auto-detected when omitted)

See UI_MANIFEST (repository root) for the authoritative UI architecture spec.
"""

import sys
import os

# ---------------------------------------------------------------------------
# Early-exit flags: handle BEFORE any GUI or backend imports so these work
# in headless CI environments (no display, no tkinter, no sklearn required).
# ---------------------------------------------------------------------------
_args = sys.argv[1:]

if "--version" in _args or "-V" in _args:
    print("Mossy Manager 1.0.0")
    sys.exit(0)

if "--help" in _args or "-h" in _args:
    print("Mossy Manager - MO2 Load Order Manager & Conflict Resolver")
    print("")
    print("Usage: MossyManager[.exe] [OPTIONS]")
    print("")
    print("  Opens the self-contained desktop UI (MO2-style window).")
    print("  Designed to be added to Mod Organizer 2 via the Executables list.")
    print("")
    print("Options:")
    print("  -m, --mo2-path PATH   Path to MO2 installation (auto-detected if omitted)")
    print("  -V, --version         Print version and exit")
    print("  -h, --help            Print this help and exit")
    print("")
    print("MO2 Setup:")
    print("  Title    : Mossy Manager")
    print("  Binary   : <path to MossyManager.exe>")
    print("  Arguments: (leave blank)")
    print("  Start in : (leave blank)")
    sys.exit(0)

# ---------------------------------------------------------------------------
# Ensure src/ is on the path when running from the repo (dev mode).
# In a PyInstaller bundle _here points inside the temp extraction directory
# and there is no src/ sibling, so this block is a safe no-op when bundled.
# ---------------------------------------------------------------------------
_here = os.path.dirname(os.path.abspath(__file__))
_src  = os.path.join(_here, "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from mossy_manager.gui.app import launch

if __name__ == "__main__":
    # Parse --mo2-path / -m
    mo2_path = None
    for i, arg in enumerate(_args):
        if arg in ("--mo2-path", "-m") and i + 1 < len(_args):
            mo2_path = _args[i + 1]
        elif arg.startswith("--mo2-path="):
            mo2_path = arg.split("=", 1)[1]

    launch(mo2_path=mo2_path)
