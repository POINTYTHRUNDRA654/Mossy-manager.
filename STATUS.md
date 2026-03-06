# Mossy Manager — Project Status & Session Log

> **Purpose:** This file is the single source of truth for every session.
> Before making any changes, read this file top-to-bottom. After a session,
> update the relevant sections so the next session starts from a known-good
> state.

---

## ✅ What The Application Is

**Mossy Manager** is a fully self-contained desktop mod-management tool for
**Fallout 4 / Mod Organizer 2**.  It runs 100% locally — no internet
connection is required.  Users interact via:

1. A **local web UI** (`mossy ui`) — MO2-inspired dark charcoal interface
   served on `http://127.0.0.1:8732` by a FastAPI/uvicorn server.
2. A **CLI** (`mossy <command>`) — 35 working leaf commands.

---

## ✅ 35 Working Applications (CLI Commands)

| # | Command | Description |
|---|---------|-------------|
| 1 | `mossy auto` | Full workflow: optimize + conflict detect + report |
| 2 | `mossy detect` | Auto-detect MO2 / xEdit installations |
| 3 | `mossy info` | Show version, feature list, quick-start guide |
| 4 | `mossy status` | Scored health report (0–100) for a profile |
| 5 | `mossy ui` | Launch local web UI in browser |
| 6 | `mossy loadorder auto-fo4` | Auto-optimize FO4 load order for an MO2 profile |
| 7 | `mossy loadorder esl-candidates` | List `.esp` plugins eligible for ESL-flagging |
| 8 | `mossy loadorder list` | Display current load order with stats |
| 9 | `mossy loadorder optimize` | Optimize load order from a plugins.txt |
| 10 | `mossy loadorder validate` | Validate load order for rule violations |
| 11 | `mossy conflicts resolve-xedit` | Export conflicts to xEdit + generate helper script |
| 12 | `mossy conflicts scan` | Scan mods directory for file conflicts |
| 13 | `mossy conflicts xedit-help` | Print xEdit integration help |
| 14 | `mossy patch apply` | Apply a `.json` patch to a mod directory |
| 15 | `mossy patch create` | Create a new Mossy Manager patch file |
| 16 | `mossy patch create-xedit` | Create a patch and generate xEdit Pascal script |
| 17 | `mossy patch export-xedit` | Export existing patch to xEdit format |
| 18 | `mossy patch list` | List all saved patches |
| 19 | `mossy fallout4 optimize` | FO4-specific load order optimization |
| 20 | `mossy ai analyze` | Full ML-based load order analysis |
| 21 | `mossy ai fix` | Generate ready-to-run fix scripts (Python/Pascal/INI/Batch) |
| 22 | `mossy ai learn` | Teach the AI a mod's actual conflict severity |
| 23 | `mossy ai reason` | Chain-of-thought reasoning about load order / problems |
| 24 | `mossy ai risk` | Predict conflict-risk severity for a single plugin |
| 25 | `mossy ai score` | Score compatibility between two plugins |
| 26 | `mossy ai script` | Generate xEdit/INI/batch scripts (8 types + auto) |
| 27 | `mossy backup cleanup` | Delete old profile backups (keep N most recent) |
| 28 | `mossy backup create` | Create timestamped backup of an MO2 profile |
| 29 | `mossy backup list` | List all available backups with metadata |
| 30 | `mossy backup restore` | Restore a backup to a profile directory |
| 31 | `mossy mods list` | List all installed mods with enabled/disabled status |
| 32 | `mossy mods enable` | Enable a mod in a profile's modlist.txt |
| 33 | `mossy mods disable` | Disable a mod in a profile's modlist.txt |
| 34 | `mossy ini apply` | Apply a named INI preset to Fallout4Custom.ini |
| 35 | `mossy ini diff` | Diff two Fallout 4 INI files side-by-side |

---

## ✅ Web UI Tabs & Features

The UI (`src/mossy_manager/webui/static/index.html`) has an MO2-inspired layout:

| Area | Feature |
|------|---------|
| **Title bar** | App name, version, MO2 status pill, xEdit status pill |
| **Toolbar** | Profile selector, Refresh, Optimize, Scan Conflicts, Merge Wizard |
| **Left panel** | Plugin table with Priority / Enabled / Name / Type columns |
| **Right panel — Load Order tab** | Optimization results, moved-plugin list, validation errors |
| **Right panel — Conflicts tab** | Conflict stats (critical/high/medium/low), full report |
| **Right panel — Settings tab (panel 1)** | Apply, Backup, Scan, xEdit-resolve toggles + inputs |
| **Right panel — Settings tab (panel 2 mirror)** | Duplicate controls that sync bidirectionally |
| **Right panel — AI tab** | AI analysis results, anomalies, risk summary |
| **Merge Wizard** | 3-step modal for selecting and merging mods |
| **Status bar** | Live status dot + message |
| **Toast notifications** | Non-blocking error/success feedback |
| **SSE stream** | `/api/stream` — real-time progress updates |

### Web API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/mo2` | GET | Detect MO2 installation |
| `/api/loadorder` | GET | Read current load order |
| `/api/loadorder/optimize` | POST | Optimize + optionally apply |
| `/api/conflicts/scan` | POST | Scan mods for conflicts |
| `/api/stream` | GET | SSE real-time progress stream |
| `/api/tools` | GET | Detect xEdit/F4SE tools |
| `/api/version` | GET | Local version info (no internet) |
| `/api/mods` | GET | List installed mods |
| `/api/mods/merge` | POST | Merge selected mods |
| `/api/webhook/mo2` | POST | MO2 webhook integration |
| `/health` | GET | Health ping |
| `/api/health` | GET | Detailed health report (JSON) |
| `/api/ai/analyze` | POST | AI load-order analysis |
| `/api/ai/risk/{plugin}` | GET | Plugin conflict-risk prediction |
| `/api/ai/compatibility` | GET | Plugin compatibility score |
| `/api/ai/fix` | POST | Generate fix scripts |
| `/` | GET | Serve the web UI |

---

## ✅ Source Modules & Status

| Module | File | Status |
|--------|------|--------|
| Load order management | `core/load_order.py` | ✅ Complete, tested |
| Conflict resolver | `core/conflict_resolver.py` | ✅ Complete, tested |
| Patcher | `core/patcher.py` | ✅ Complete, tested |
| Dependency graph | `core/dependency_graph.py` | ✅ Complete, tested |
| Fallout 4 rules | `games/fallout4.py` | ✅ Complete, tested |
| MO2 integration | `integrations/mo2.py` | ✅ Complete, tested |
| xEdit integration | `utils/xedit_integration.py` | ✅ Complete, tested |
| INI patcher | `utils/ini_patcher.py` | ✅ Complete, tested |
| Backup manager | `utils/backup_manager.py` | ✅ Complete, tested |
| Health checker | `utils/health_checker.py` | ✅ Complete, tested |
| AI brain (ML) | `ai/brain.py` | ✅ Complete, tested |
| AI reasoner | `ai/reasoner.py` | ✅ Complete, tested |
| AI script writer | `ai/script_writer.py` | ✅ Complete, tested |
| AI fix generator | `ai/fix_generator.py` | ✅ Complete, tested |
| Config manager | `config_manager.py` | ✅ Complete, tested |
| Mod manager | `mod_manager.py` | ✅ Complete, tested |
| Profile manager | `profile_manager.py` | ✅ Complete, tested |
| CLI (35 commands) | `cli/main.py` | ✅ Complete, tested |
| Web UI app | `webui/app.py` | ✅ Complete, tested |
| Web UI HTML | `webui/static/index.html` | ✅ Complete — MO2 look |

---

## ✅ Tests

**444 tests — 0 failures — 0 CodeQL alerts**

| Test file | Tests | Covers |
|-----------|-------|--------|
| `test_config_manager.py` | — | ConfigManager |
| `test_mod_manager.py` | — | ModManager |
| `test_profile_manager.py` | — | ProfileManager |
| `test_load_order.py` | — | LoadOrderManager |
| `test_conflict_resolver.py` | — | ConflictResolver |
| `test_patcher.py` | — | Patcher |
| `test_fallout4.py` | — | Fallout4Rules |
| `test_mo2_integration.py` | — | MO2Integration |
| `test_main_cli.py` | — | argparse CLI (main.py) |
| `test_click_cli.py` | — | Click CLI (cli/main.py) |
| `test_cli_conflicts_xedit.py` | — | conflicts + xedit CLI |
| `test_xedit_integration.py` | — | XEditIntegration |
| `test_xedit_patch_integration.py` | — | xEdit patch workflow |
| `test_backup_manager.py` | — | BackupManager |
| `test_reasoner_writer_fixgen.py` | — | AI reasoner/writer/fix |
| `test_ini_dep_health.py` | — | INIPatcher + HealthChecker |
| `test_webui.py` | — | FastAPI web endpoints |
| `test_new_commands.py` | 29 | mods/ini/esl-candidates CLI |

Run all tests (excluding slow AI brain training):
```bash
cd /home/runner/work/Mossy-manager./Mossy-manager.
python -m pytest tests/ --ignore=tests/test_ai_brain.py -q
```

---

## ✅ Bugs Fixed (Completed Sessions)

### Session 1 — UI redesign + self-contained
- **Removed internet dependency**: `/api/version` no longer calls GitHub API
- **MO2-inspired UI**: Dark charcoal theme, toolbar, left plugin table, right tabbed panel, status bar
- **Self-contained**: All CSS/JS inline — zero CDN or external URLs

### Session 2 — Full codebase audit
| # | Bug | File | Fix |
|---|-----|------|-----|
| 1 | Duplicate unreachable `return` block | `webui/app.py` | Removed dead code |
| 2 | `asyncio.Queue` not thread-safe for SSE | `webui/app.py` | Replaced with `queue.Queue`; generator polls with `get_nowait()` + `asyncio.sleep(0.05)` |
| 3 | Missing `import os` | `cli/main.py` | Added `import os` |
| 4 | `datetime.utcnow()` deprecated (×2) | `cli/main.py` | `datetime.now(timezone.utc)` |
| 5 | `requests` in deps but unused | `requirements.txt`, `setup.py` | Removed `requests`, added `httpx>=0.27.0` |
| 6 | `test_progress_stream` hung forever | `tests/test_webui.py` | Rewrote as unit test of broadcaster |
| 7 | `#xedit-status` inline styles duplicated | `webui/static/index.html` | Moved to CSS class |
| 8 | Sync event listeners duplicated 4× | `webui/static/index.html` | `registerSyncListeners()` helper |
| 9 | Wizard step transitions scattered | `webui/static/index.html` | `showWizardStep(n)` function |
| 10 | `dummy report` + `tmp_test_webui.py` committed | repo root | `git rm`'d; `.gitignore` updated |

### Session 3 — 35 working applications
- Added CLI commands **#30–35**: `mods list`, `mods enable`, `mods disable`,
  `ini apply`, `ini diff`, `loadorder esl-candidates`
- All 6 backed by fully-implemented backend classes (no stubs)
- Added 29 tests in `tests/test_new_commands.py`

---

## 🔧 How to Run

### Install
```bash
pip install -e .          # standard install
pip install -e ".[dev]"   # + pytest, pytest-cov
```

### Launch web UI
```bash
mossy ui                  # opens browser at http://127.0.0.1:8732
```

### Run a quick health check
```bash
mossy status --mo2-path "C:/Games/MO2" --profile Default
```

### Run all tests
```bash
python -m pytest tests/ --ignore=tests/test_ai_brain.py -q
```

### Build standalone executable (Windows)
```bash
pip install pyinstaller
python build.py
# or:  build.bat
```

---

## 📦 Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pyyaml` | ≥6.0 | Config files |
| `toml` | ≥0.10.2 | Config files |
| `click` | ≥8.1.0 | CLI framework |
| `colorama` | ≥0.4.6 | Colored terminal output |
| `tabulate` | ≥0.9.0 | CLI tables |
| `pydantic` | ≥2.8.0 | API request/response models |
| `fastapi` | ≥0.115.0 | Web API server |
| `uvicorn` | ≥0.30.0 | ASGI server |
| `httpx` | ≥0.27.0 | HTTP client (TestClient for FastAPI) |
| `scikit-learn` | ≥1.3.0 | AI brain (ML models) |
| `numpy` | ≥1.24.0 | Numerical operations for AI |

**No internet required at runtime.** `httpx` is only used internally by FastAPI's `TestClient` during testing.

---

## 📁 Repository Layout

```
src/mossy_manager/
├── __init__.py                 version = "1.0.0"
├── config_manager.py
├── mod_manager.py
├── profile_manager.py
├── main.py                     argparse entry-point (mossy-manager)
├── ai/
│   ├── brain.py                ML classifier + anomaly detection
│   ├── fix_generator.py        Generates Python/Pascal/INI/batch fixes
│   ├── reasoner.py             Chain-of-thought rule engine
│   └── script_writer.py        xEdit Pascal + INI + batch scripts
├── cli/
│   └── main.py                 Click CLI — 35 leaf commands
├── core/
│   ├── conflict_resolver.py
│   ├── dependency_graph.py
│   ├── load_order.py
│   └── patcher.py
├── games/
│   └── fallout4.py             FO4 rules, categories, DLC deps
├── integrations/
│   └── mo2.py                  MO2 directory/profile I/O
├── utils/
│   ├── backup_manager.py
│   ├── health_checker.py
│   ├── ini_patcher.py
│   └── xedit_integration.py
└── webui/
    ├── app.py                  FastAPI app + all API routes
    └── static/
        └── index.html          MO2-style self-contained UI
tests/                          444 tests, 0 failures
```

---

## 🔴 Known Limitations / Future Work

| Item | Notes |
|------|-------|
| `test_ai_brain.py` excluded from default run | Training on tiny synthetic data; takes 3–5 min |
| AI models are in-memory only | Add `mossy ai learn` + `--model-dir` to persist across sessions |
| xEdit auto-launch is Windows-only | `subprocess.Popen` on `.exe`; no-op on Linux/macOS |
| ESL-candidate size check is heuristic | Real check requires parsing BSA/ESP binary format with xEdit |
| SSE stream has 50 ms poll interval | Adequate for desktop use; could use `asyncio.Event` for lower latency |

---

*Last updated: Session 3 — 2026-03-06*  
*Tests: 444 passing / 0 failing*  
*Commands: 35 working*
