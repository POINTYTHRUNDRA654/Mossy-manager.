# Tool Discovery (MO2 Bundles)

Mossy Manager auto-detects bundled tools inside Mod Organizer 2. If you place the external executables under `MO2/tools`, the manager will find them without extra configuration.

## Drop-in Locations
- `MO2/tools/bsarch/bsarch.exe` (or directly `MO2/tools/bsarch.exe`)
- `MO2/tools/FO4Edit/FO4Edit.exe` (any xEdit variant is also picked up: `xEdit.exe`, `SSEEdit.exe`, `TES5Edit.exe`)

## Behavior
- Merge (BA2) uses `bsarch`: the CLI and Python paths will resolve via `BSARCH_PATH`, then PATH, then MO2/tools.
- Conflict/XEdit flows use `FO4Edit.exe` (or other xEdit names): they check `--xedit-path`, then PATH, then MO2/tools.

## CLI Examples
- Merge with auto tool discovery:
  - `dist\MossyManager.exe merge "<modsDir>" --output merged`
- Conflict export with FO4Edit from MO2/tools:
  - `.venv312\Scripts\python.exe -m mossy_manager conflicts resolve-xedit --mods-dir "<MO2 mods>" --game fallout4`

## If Not Found
- Set env vars: `BSARCH_PATH` for bsarch; pass `--xedit-path` for xEdit.
- Place the executables under `MO2/tools/` as above and re-run.
