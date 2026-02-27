import sys, os
# ensure package path is available
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
import tempfile
from pathlib import Path
from mossy_manager.integrations.mo2 import MO2Integration
from mossy_manager.games.fallout4 import Fallout4Rules

# prepare fake mo2
fake = Path(tempfile.mkdtemp()) / 'MO2'
(fake / 'profiles' / 'Default').mkdir(parents=True)
(fake / 'profiles' / 'Default' / 'plugins.txt').write_text('*Fallout4.esm\n')
(fake / 'profiles' / 'Default' / 'loadorder.txt').write_text('Fallout4.esm\n')
(fake / 'profiles' / '_active_profile.txt').write_text('Default')

# patch detection manually
MO2Integration.detect_mo2_installation = lambda: fake

# run CLI
from mossy_manager.cli.main import main
import sys
sys.argv = ['mossy-manager', 'loadorder', 'auto-fo4']
try:
    rc = main()
except SystemExit as e:
    rc = e.code
print('return code:', rc)
