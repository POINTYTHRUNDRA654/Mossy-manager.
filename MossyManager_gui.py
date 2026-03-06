"""
MossyManager GUI entry point.

This script is the executable launched by Mod Organizer 2.
It opens the self-contained desktop window immediately, with no CLI arguments
required.  MO2 simply runs this file and the window appears.

See UI_MANIFEST (repository root) for the authoritative UI architecture spec.
"""

import sys
import os

# Ensure src/ is on the path when running from the repo (dev mode)
_here = os.path.dirname(os.path.abspath(__file__))
_src  = os.path.join(_here, "src")
if os.path.isdir(_src) and _src not in sys.path:
    sys.path.insert(0, _src)

from mossy_manager.gui.app import launch

if __name__ == "__main__":
    # Accept an optional --mo2-path argument so MO2 can pass its own directory
    mo2_path = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg in ("--mo2-path", "-m") and i + 1 < len(args):
            mo2_path = args[i + 1]
        elif arg.startswith("--mo2-path="):
            mo2_path = arg.split("=", 1)[1]

    launch(mo2_path=mo2_path)
