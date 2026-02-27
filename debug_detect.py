import sys
import os
# ensure project root is on path
# ensure the src folder is on path so mossy_manager package can be imported
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
from mossy_manager.main import main
from unittest.mock import patch
from io import StringIO
from pathlib import Path
import tempfile

# helper run_main

def run_main(*args):
    with patch("sys.argv", ["mossy-manager"] + list(args)):
        captured_out = StringIO()
        captured_err = StringIO()
        with patch("sys.stdout", captured_out), patch("sys.stderr", captured_err):
            try:
                rc = main()
            except SystemExit as e:
                rc = e.code
        return rc, captured_out.getvalue(), captured_err.getvalue()

# patch detect_mo2_installation to None
import mossy_manager.integrations.mo2 as mo2mod
mo2mod.MO2Integration.detect_mo2_installation = lambda: None

rc, out, err = run_main('detect')
print('rc', rc)
print('out>', out)
print('err>', err)

# test with mo2 path
fake_dir = Path(tempfile.mkdtemp()) / 'MO2'
(fake_dir / 'tools' / 'MossyManager').mkdir(parents=True)
(fake_dir / 'tools' / 'MossyManager' / 'MossyManager.exe').write_text('')
mo2mod.MO2Integration.detect_mo2_installation = lambda: fake_dir

import mossy_manager.utils.xedit_integration as xi
xi.XEditIntegration.detect_xedit = lambda game, search_roots=None: None

cfg_path = Path(tempfile.mkdtemp()) / 'config.ini'
rc, out, err = run_main('detect', '--mo2-config', str(cfg_path))
print('rc', rc)
print('out>', out)
print('err>', err)

