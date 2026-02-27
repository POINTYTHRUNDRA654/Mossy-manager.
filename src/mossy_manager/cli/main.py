"""
Command-line interface for Mossy Manager
"""

import sys
import logging
import webbrowser
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import threading
import time

import click
from colorama import init, Fore, Style
from tabulate import tabulate
import uvicorn

from mossy_manager.core.load_order import LoadOrderManager
from mossy_manager.core.conflict_resolver import ConflictResolver
from mossy_manager.core.patcher import Patcher
from mossy_manager.utils.xedit_integration import XEditIntegration
from mossy_manager.utils.backup_manager import BackupManager
from mossy_manager.utils.health_checker import ModHealthChecker
from mossy_manager.integrations.mo2 import MO2Integration
from mossy_manager.games.fallout4 import Fallout4Rules
from mossy_manager.config_manager import ConfigManager
from mossy_manager.webui.app import app as web_app
from mossy_manager.ai.brain import ModAIBrain
from mossy_manager.ai.reasoner import ModReasoner
from mossy_manager.ai.script_writer import ScriptWriter
from mossy_manager.ai.fix_generator import FixGenerator

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
@click.option('--verbose', '-v', is_flag=True, # The above code is a Python comment. It starts with a
# `#` symbol, which indicates that the following text
# is a comment and will not be executed as code. In
# this case, the comment mentions `help='Enable verbose
# logging'`, which seems to be a placeholder for some
# code or explanation related to enabling verbose
# logging.
help='Enable verbose logging')
def main(verbose):
    """
    Mossy Manager - MO2 Load Order Manager, Conflict Resolution, and Patching Tool
    
    A comprehensive tool for managing Mod Organizer 2 load orders,
    detecting and resolving mod conflicts, and creating compatibility patches.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@main.command('detect')
@click.option('--mo2-config', type=click.Path(),
              help='Write a small MO2 executable ini file to this location')
def detect(mo2_config):
    """Auto-detect installations and provide MO2 configuration guidance"""
    from mossy_manager.utils.xedit_integration import XEditIntegration

    # detect MO2
    detected_mo2 = MO2Integration.detect_mo2_installation()
    if detected_mo2:
        click.echo(f"{Fore.GREEN}Detected Mod Organizer 2 at: {detected_mo2}{Style.RESET_ALL}")
        click.echo("\nTo add Mossy Manager as an executable in MO2, use the following values:")
        click.echo("  Title     : Mossy Manager")
        click.echo(f"  Binary    : {detected_mo2 / 'tools' / 'MossyManager' / 'MossyManager.exe'}")
        click.echo("  Arguments : auto --profile \"Default\"")
        click.echo("  Start in  : (leave blank, the tool autodetects MO2)")
        if mo2_config:
            # write a simple ini snippet that MO2 can import/drop into its tools folder
            try:
                # the path written to ini should be relative to MO2 if possible
                rel_path = os.path.relpath(detected_mo2 / 'tools' / 'MossyManager' / 'MossyManager.exe',
                                           start=detected_mo2)
            except Exception:
                rel_path = str(detected_mo2 / 'tools' / 'MossyManager' / 'MossyManager.exe')
            ini_content = (
                "[General]\n"
                "name=Mossy Manager\n"
                f"path={rel_path}\n"
                "args=auto --profile \"Default\"\n"
                "workDir=\n"
            )
            with open(mo2_config, 'w', encoding='utf-8') as f:
                f.write(ini_content)
            click.echo(f"INI snippet written to: {mo2_config}")
    else:
        click.echo(f"{Fore.RED}Mod Organizer 2 installation not detected.{Style.RESET_ALL}")

    # detect xEdit for convenience
    xedit_path = None
    try:
        xedit_path = XEditIntegration.detect_xedit('fallout4',
                                                   search_roots=[detected_mo2] if detected_mo2 else None)
    except Exception:
        pass
    if xedit_path:
        click.echo(f"{Fore.GREEN}Detected xEdit at: {xedit_path}{Style.RESET_ALL}")
    else:
        click.echo("xEdit installation not found (you can provide --xedit-path to other commands)")


@main.group()
def loadorder():
    """Manage plugin load order"""
    pass


@loadorder.command('list')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              help='Path to plugins.txt file')
@click.option('--loadorder-file', '-l', type=click.Path(exists=True),
              help='Path to loadorder.txt file')
def list_loadorder(plugins_file, loadorder_file):
    """List current load order"""
    manager = LoadOrderManager()
    
    if plugins_file:
        manager.load_plugins_txt(Path(plugins_file))
    
    if loadorder_file:
        manager.load_loadorder_txt(Path(loadorder_file))
    
    if not manager.plugins:
        click.echo(f"{Fore.YELLOW}No plugins loaded. "
                  f"Specify --plugins-file or --loadorder-file{Style.RESET_ALL}")
        return
    
    # Display statistics
    stats = manager.get_statistics()
    click.echo(f"\n{Fore.CYAN}=== Load Order Statistics ==={Style.RESET_ALL}")
    click.echo(f"Total Plugins: {stats['total']}")
    click.echo(f"Enabled: {Fore.GREEN}{stats['enabled']}{Style.RESET_ALL}")
    click.echo(f"Disabled: {Fore.RED}{stats['disabled']}{Style.RESET_ALL}")
    click.echo(f"Masters (.esm): {stats['masters']}")
    click.echo(f"Light (.esl): {stats['light']}")
    click.echo(f"Regular (.esp): {stats['regular']}")
    
    # Display load order
    click.echo(f"\n{Fore.CYAN}=== Current Load Order ==={Style.RESET_ALL}")
    
    table_data = []
    for plugin_name in manager.get_load_order():
        plugin = manager.plugins[plugin_name]
        status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if plugin.enabled else \
                f"{Fore.RED}✗{Style.RESET_ALL}"
        
        plugin_type = "Master" if plugin.is_master else \
                     ("Light" if plugin.is_light else "Regular")
        
        table_data.append([plugin.priority, status, plugin_name, plugin_type])
    
    headers = ["Priority", "Enabled", "Plugin Name", "Type"]
    click.echo(tabulate(table_data, headers=headers, tablefmt="simple"))


@loadorder.command('validate')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              required=True, help='Path to plugins.txt file')
@click.option('--loadorder-file', '-l', type=click.Path(exists=True),
              help='Path to loadorder.txt file')
def validate_loadorder(plugins_file, loadorder_file):
    """Validate load order for issues"""
    manager = LoadOrderManager()
    manager.load_plugins_txt(Path(plugins_file))
    
    if loadorder_file:
        manager.load_loadorder_txt(Path(loadorder_file))
    
    is_valid, issues = manager.validate_load_order()
    
    if is_valid:
        click.echo(f"{Fore.GREEN}✓ Load order is valid!{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.RED}✗ Load order has issues:{Style.RESET_ALL}\n")
        for issue in issues:
            click.echo(f"  • {issue}")


@loadorder.command('optimize')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              required=True, help='Path to plugins.txt file')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for optimized load order')
@click.option('--apply', is_flag=True, default=False,
              help='Write plugins/loadorder (default is dry-run)')
@click.option('--backup', is_flag=True, default=True,
              help='Create backup of plugins/loadorder before writing (when --apply)')
def optimize_loadorder(plugins_file, output, apply, backup):
    """Optimize load order automatically"""
    manager = LoadOrderManager()
    manager.load_plugins_txt(Path(plugins_file))
    
    click.echo(f"{Fore.CYAN}Optimizing load order...{Style.RESET_ALL}")
    optimized = manager.optimize_load_order()
    
    click.echo(f"{Fore.GREEN}✓ Optimized {len(optimized)} plugins{Style.RESET_ALL}")
    
    if apply:
        # Backup when writing
        if backup:
            plugins_path = Path(plugins_file)
            backup_path = plugins_path.parent / f"plugins_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            try:
                import shutil
                shutil.copyfile(plugins_file, backup_path)
                click.echo(f"Backup created: {backup_path}")
            except Exception as e:
                click.echo(f"{Fore.YELLOW}Warning: backup failed: {e}{Style.RESET_ALL}")
        # Save loadorder and plugins
        if output:
            manager.save_loadorder_txt(Path(output))
            click.echo(f"Saved to: {output}")
        else:
            # overwrite original loadorder.txt alongside plugins
            default_lo = Path(plugins_file).parent / 'loadorder.txt'
            manager.save_loadorder_txt(default_lo)
            click.echo(f"Saved to: {default_lo}")
    else:
        click.echo(f"{Fore.YELLOW}DRY RUN: not writing files. Use --apply to write.{Style.RESET_ALL}")
        click.echo("\nOptimized order (first 20):")
        for i, plugin_name in enumerate(optimized[:20], 1):
            click.echo(f"  {i:3d}. {plugin_name}")
        if len(optimized) > 20:
            click.echo(f"  ... and {len(optimized) - 20} more")


@loadorder.command('auto-fo4')
@click.option('--mo2-path', '-m', type=click.Path(),
              help='Path to Mod Organizer 2 installation')
@click.option('--profile', '-p', required=False,
              help='MO2 profile name (if omitted, uses active profile)')
@click.option('--backup', is_flag=True, default=True,
              help='Create backup of the profile before writing')
@click.option('--report', type=click.Path(),
              help='Write JSON optimization report to this path')
@click.option('--dry-run', is_flag=True,
              help='Show results without writing changes')
# conflict options
@click.option('--scan-conflicts', is_flag=True,
              help='Run a conflict scan on the mods directory after optimization')
@click.option('--resolve-xedit', is_flag=True,
              help='Automatically export conflicts to xEdit and optionally launch')
@click.option('--xedit-path', '-x', type=click.Path(exists=True),
              help='Path to xEdit executable (used with --resolve-xedit)')
@click.option('--patch-name', '-n', default='MossyManager_ConflictPatch',
              help='Name for xEdit patch when --resolve-xedit is used')
def auto_fo4_loadorder(mo2_path, profile, backup, report, dry_run,
                        scan_conflicts, resolve_xedit, xedit_path, patch_name):
    """
    Auto-optimize Fallout 4 load order for an MO2 profile using up-to-date rules.
    Reads plugins/loadorder/modlist, computes best order, and (unless dry-run) writes back.

    If `--profile` is omitted the command will look for an active profile via
    MO2's `_active_profile.txt` marker. This makes it convenient when running
    from inside MO2 where the active profile is already selected.
    """
    click.echo(f"{Fore.CYAN}═ Fallout 4 Load Order Auto-Optimize ═{Style.RESET_ALL}")

    # Detect MO2
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        detected = MO2Integration.detect_mo2_installation()
        if not detected:
            click.echo(f"{Fore.RED}✗ Could not detect Mod Organizer 2. Specify --mo2-path.{Style.RESET_ALL}")
            return
        mo2 = MO2Integration(detected)
        click.echo(f"Detected MO2 at: {detected}")

    # determine profile to use
    if not profile:
        # try MO2 active profile marker
        from mossy_manager.profile_manager import ProfileManager
        pm = ProfileManager(mo2.mo2_path)
        active = pm.get_active_profile()
        if active:
            profile = active
            click.echo(f"Using active profile: {profile}")
    profiles = mo2.list_profiles()
    if profile not in profiles:
        click.echo(f"{Fore.RED}✗ Profile '{profile}' not found.{Style.RESET_ALL}")
        if profiles:
            click.echo("Available profiles:")
            for p in profiles:
                click.echo(f"  • {p}")
        return

    # Read current state
    plugins_enabled = mo2.read_plugins_txt(profile)
    current_order = mo2.read_loadorder_txt(profile)
    if not current_order:
        click.echo(f"{Fore.RED}✗ No plugins found in profile.{Style.RESET_ALL}")
        return

    # optional conflict scan ahead of optimization
    if scan_conflicts or resolve_xedit:
        click.echo(f"{Fore.CYAN}╔═════════ Checking conflicts before optimization ═════════╗{Style.RESET_ALL}")
        resolver = ConflictResolver(Path(mo2.mods_path or '.'))
        # scan each mod folder within mo2
        mods_root = Path(mo2.mods_path or '.')
        for mod_dir in mods_root.iterdir():
            if mod_dir.is_dir():
                resolver.scan_mod_files(mod_dir.name, mod_dir)
        # export conflict list used later by xEdit
        pre_conflicts = resolver.export_for_xedit()

        if scan_conflicts:
            report = resolver.generate_report()
            click.echo(report)
            stats = resolver.get_statistics()
            click.echo(f"{Fore.CYAN}=== Conflict Statistics ==={Style.RESET_ALL}")
            click.echo(f"Total Conflicts: {stats['total_conflicts']}")
            click.echo(f"Critical: {Fore.RED}{stats['critical']}{Style.RESET_ALL}")
            click.echo(f"High: {Fore.YELLOW}{stats['high']}{Style.RESET_ALL}")
            click.echo(f"Medium: {stats['medium']}")
            click.echo(f"Low: {stats['low']}")
        # keep pre_conflicts when resolve_xedit is requested as well

    # continue with validation and optimization

    click.echo(f"Loaded {len(current_order)} plugins from profile {profile}.")

    # Validate and optimize
    issues = Fallout4Rules.validate_load_order(current_order)
    optimized = Fallout4Rules.optimize_load_order(current_order)

    moved = []
    index_map = {name: i for i, name in enumerate(current_order)}
    for new_idx, name in enumerate(optimized):
        old_idx = index_map.get(name)
        if old_idx is not None and old_idx != new_idx:
            moved.append({
                'plugin': name,
                'from': old_idx,
                'to': new_idx
            })

    recommendations = Fallout4Rules.get_recommendations(optimized)

    click.echo(f"{Fore.CYAN}Planned changes:{Style.RESET_ALL} {len(moved)} plugins move position.")
    if issues['errors']:
        click.echo(f"{Fore.RED}Errors:{Style.RESET_ALL}")
        for err in issues['errors'][:5]:
            click.echo(f"  • {err}")
        if len(issues['errors']) > 5:
            click.echo(f"  ... and {len(issues['errors']) - 5} more")
    if issues['warnings']:
        click.echo(f"{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
        for warn in issues['warnings'][:5]:
            click.echo(f"  • {warn}")
        if len(issues['warnings']) > 5:
            click.echo(f"  ... and {len(issues['warnings']) - 5} more")
    if recommendations:
        click.echo(f"{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
        for rec in recommendations[:5]:
            click.echo(f"  • {rec}")

    if dry_run:
        click.echo(f"{Fore.YELLOW}Dry-run: no files written.{Style.RESET_ALL}")
    else:
        # Backup
        if backup:
            profile_path = mo2.get_profile_path(profile)
            if profile_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_dir = profile_path.parent / f"{profile}_backup_{timestamp}"
                import shutil
                shutil.copytree(profile_path, backup_dir)
                click.echo(f"Backup created: {backup_dir}")

        # Preserve enabled flags
        optimized_plugins = {p: plugins_enabled.get(p, True) for p in optimized}
        mo2.write_plugins_txt(profile, optimized_plugins)
        mo2.write_loadorder_txt(profile, optimized)
        click.echo(f"{Fore.GREEN}✓ Load order written to profile.{Style.RESET_ALL}")

        # after successful write, optionally resolve with xEdit
        if resolve_xedit:
            click.echo(f"{Fore.CYAN}╔═════════ Exporting conflicts to xEdit ═════════╗{Style.RESET_ALL}")
            # prepare xEdit integration (reuse conflict scan results)
            xedit = XEditIntegration(xedit_path=xedit_path)
            # invoke high-level helper which handles export/script/launch
            result = xedit.create_conflict_resolution_patch(
                conflicts=pre_conflicts,
                patch_name=patch_name,
                output_dir=Path('.') / 'xedit_output'
            )
            if result.get('success'):
                click.echo(f"  {Fore.GREEN}✓ Conflicts exported to: {result.get('export_path')}{Style.RESET_ALL}")
                click.echo(f"  {Fore.GREEN}✓ xEdit script generated: {result.get('script_path')}{Style.RESET_ALL}")
                if result.get('xedit_launched'):
                    click.echo(f"\n{Fore.GREEN}✓ xEdit launched successfully!{Style.RESET_ALL}")
            else:
                click.echo(f"\n{Fore.RED}✗ Error exporting conflicts: {result.get('error')}{Style.RESET_ALL}")

    # Report
    if report:
        report_data = {
          'generated_at': datetime.utcnow().isoformat() + 'Z',
          'profile': profile,
          'mo2_path': str(mo2.mo2_path) if mo2.mo2_path else None,
          'counts': {
            'total': len(current_order),
            'moved': len(moved)
          },
          'issues': issues,
          'recommendations': recommendations,
          'current_order': current_order,
          'optimized_order': optimized,
          'moved': moved
        }
        try:
            with open(report, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2)
            click.echo(f"Report written to: {report}")
        except Exception as e:
            click.echo(f"{Fore.RED}✗ Failed to write report: {e}{Style.RESET_ALL}")


@main.group()
def conflicts():
    """Detect and resolve mod conflicts"""
    pass


@conflicts.command('scan')
@click.option('--mods-dir', '-m', type=click.Path(exists=True),
              required=True, help='Path to MO2 mods directory')
@click.option('--output', '-o', type=click.Path(),
              help='Output file for conflict report')
def scan_conflicts(mods_dir, output):
    """Scan for conflicts between mods"""
    resolver = ConflictResolver(Path(mods_dir))
    
    mods_path = Path(mods_dir)
    
    if not mods_path.exists():
        click.echo(f"{Fore.RED}Error: Mods directory not found: {mods_dir}{Style.RESET_ALL}")
        return
    
    click.echo(f"{Fore.CYAN}Scanning mods for conflicts...{Style.RESET_ALL}")
    
    # Scan each mod directory
    mod_count = 0
    for mod_dir in mods_path.iterdir():
        if mod_dir.is_dir():
            resolver.scan_mod_files(mod_dir.name, mod_dir)
            mod_count += 1
    
    click.echo(f"Scanned {mod_count} mods")
    
    # Generate report
    report = resolver.generate_report()
    
    if output:
        with open(output, 'w') as f:
            f.write(report)
        click.echo(f"\n{Fore.GREEN}Report saved to: {output}{Style.RESET_ALL}")
    
    click.echo("\n" + report)
    
    # Display statistics
    stats = resolver.get_statistics()
    click.echo(f"\n{Fore.CYAN}=== Conflict Statistics ==={Style.RESET_ALL}")
    click.echo(f"Total Conflicts: {stats['total_conflicts']}")
    click.echo(f"Critical: {Fore.RED}{stats['critical']}{Style.RESET_ALL}")
    click.echo(f"High: {Fore.YELLOW}{stats['high']}{Style.RESET_ALL}")
    click.echo(f"Medium: {stats['medium']}")
    click.echo(f"Low: {stats['low']}")


@conflicts.command('resolve-xedit')
@click.option('--mods-dir', '-m', type=click.Path(exists=True),
              required=True, help='Path to MO2 mods directory')
@click.option('--mo2-path', type=click.Path(),
              help='Path to Mod Organizer 2 (used to locate bundled tools)')
@click.option('--xedit-path', '-x', type=click.Path(exists=True),
              help='Path to xEdit executable (SSEEdit.exe, TES5Edit.exe, etc.)')
@click.option('--game', '-g', default='fallout4',
              help='Game type (fallout4)')
@click.option('--patch-name', '-p', default='MossyManager_ConflictPatch',
              help='Name for the conflict resolution patch')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./xedit_output', help='Output directory for xEdit files')
@click.option('--auto-launch', is_flag=True, default=False,
              help='Automatically launch xEdit after export')
@click.option('--backup/--no-backup', default=True,
              help='Backup existing output directory before writing (when --apply)')
@click.option('--apply', is_flag=True, default=False,
              help='Perform export/script generation (default is dry-run)')
def resolve_xedit(mods_dir, mo2_path, xedit_path, game, patch_name, output_dir, auto_launch, backup, apply):
    """
    Create conflict resolution patch using xEdit
    
    This command scans for conflicts, exports them to xEdit format,
    generates a helper script, and optionally launches xEdit for
    interactive conflict resolution.
    """
    click.echo(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║     xEdit Conflict Resolution - Mossy Manager            ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Initialize conflict resolver and config
    resolver = ConflictResolver(Path(mods_dir))
    config = ConfigManager()

    # Determine MO2 path (for tool discovery) if not provided
    mo2 = None
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        detected_mo2 = MO2Integration.detect_mo2_installation()
        if detected_mo2:
            mo2 = MO2Integration(detected_mo2)
            mo2_path = str(detected_mo2)
    
    # Scan mods for conflicts
    click.echo(f"{Fore.CYAN}Step 1: Scanning mods for conflicts...{Style.RESET_ALL}")
    mods_path = Path(mods_dir)
    
    if not mods_path.exists():
        click.echo(f"{Fore.RED}Error: Mods directory not found: {mods_dir}{Style.RESET_ALL}")
        return
    
    mod_count = 0
    for mod_dir in mods_path.iterdir():
        if mod_dir.is_dir():
            resolver.scan_mod_files(mod_dir.name, mod_dir)
            mod_count += 1
    
    click.echo(f"  Scanned {mod_count} mods")
    
    # Detect conflicts
    conflicts = resolver.export_for_xedit()
    
    if not conflicts:
        click.echo(f"\n{Fore.GREEN}✓ No conflicts detected! No patch needed.{Style.RESET_ALL}")
        return
    
    click.echo(f"  Found {len(conflicts)} conflicts")
    
    # Display conflict summary
    stats = resolver.get_statistics()
    click.echo(f"\n{Fore.CYAN}Conflict Summary:{Style.RESET_ALL}")
    click.echo(f"  Critical: {Fore.RED}{stats['critical']}{Style.RESET_ALL}")
    click.echo(f"  High:     {Fore.YELLOW}{stats['high']}{Style.RESET_ALL}")
    click.echo(f"  Medium:   {stats['medium']}")
    click.echo(f"  Low:      {stats['low']}")

    if not apply:
        click.echo(f"\n{Fore.YELLOW}DRY RUN: no exports generated. Use --apply to write xEdit files.{Style.RESET_ALL}")
        return
    
    # Prepare output path and optional backup
    output_path = Path(output_dir)
    if backup and output_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = output_path.parent / f"{output_path.name}_backup_{timestamp}"
        try:
            import shutil
            shutil.copytree(output_path, backup_path)
            click.echo(f"  Backup created: {backup_path}")
        except Exception as e:
            click.echo(f"  {Fore.YELLOW}Warning: backup failed: {e}{Style.RESET_ALL}")

    # Initialize xEdit integration, honoring config default if no CLI path
    xedit_path_final = Path(xedit_path) if xedit_path else None
    if not xedit_path_final:
        cfg_xedit = config.get_config('xedit_path')
        if cfg_xedit:
            candidate = Path(cfg_xedit)
            if candidate.exists():
                xedit_path_final = candidate

    xedit = XEditIntegration(
        xedit_path=xedit_path_final,
        game_data_path=None
    )

    # Auto-detect xEdit if not provided; search MO2/tools first
    if not xedit_path_final:
        click.echo(f"\n{Fore.CYAN}Step 2: Detecting xEdit installation...{Style.RESET_ALL}")

        # Prefer FO4Edit bundled inside MO2 (e.g., MO2/tools/FO4Edit)
        search_roots = []
        if mo2_path:
            search_roots.append(Path(mo2_path))
            tools_dir = Path(mo2_path) / 'tools'
            if tools_dir.exists():
                search_roots.append(tools_dir)

        # If MO2 is known, try a direct tool lookup first
        if mo2:
            mo2_tool = mo2.find_tool(['FO4Edit.exe', 'xEdit.exe', 'SSEEdit.exe', 'TES5Edit.exe'])
            if mo2_tool:
                xedit.xedit_path = mo2_tool
                click.echo(f"  {Fore.GREEN}✓ Found xEdit in MO2 tools: {mo2_tool}{Style.RESET_ALL}")
        
        if not xedit.xedit_path:
            detected_path = xedit.detect_xedit(game, search_roots=search_roots)
            if detected_path:
                xedit.xedit_path = detected_path
                click.echo(f"  {Fore.GREEN}✓ Found xEdit: {detected_path}{Style.RESET_ALL}")
            else:
                click.echo(f"  {Fore.YELLOW}⚠ xEdit not auto-detected{Style.RESET_ALL}")
                click.echo(f"  Please specify --xedit-path manually")
                if not auto_launch:
                    click.echo(f"  Continuing without auto-launch...")
    
    # Create conflict resolution patch
    click.echo(f"\n{Fore.CYAN}Step 3: Generating xEdit files...{Style.RESET_ALL}")
    click.echo(f"  Writing exports to: {output_path.resolve()}")
    
    result = xedit.create_conflict_resolution_patch(
        conflicts=conflicts,
        patch_name=patch_name,
        output_dir=output_path
    )
    
    if result['success']:
        click.echo(f"  {Fore.GREEN}✓ Conflicts exported to: {result['export_path']}{Style.RESET_ALL}")
        click.echo(f"  {Fore.GREEN}✓ xEdit script generated: {result['script_path']}{Style.RESET_ALL}")
        
        if result['xedit_launched']:
            click.echo(f"\n{Fore.GREEN}✓ xEdit launched successfully!{Style.RESET_ALL}")
            click.echo(f"\n{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
            click.echo(f"  1. In xEdit, review the conflicts")
            click.echo(f"  2. Use xEdit's conflict detection features")
            click.echo(f"  3. Create a new patch plugin ('{patch_name}.esp')")
            click.echo(f"  4. Copy conflicting records to your patch")
            click.echo(f"  5. Resolve conflicts manually")
            click.echo(f"  6. Save and close xEdit")
            click.echo(f"  7. Add the patch to your load order")
        else:
            if xedit.xedit_path:
                click.echo(f"\n{Fore.YELLOW}⚠ xEdit not launched (auto-launch disabled){Style.RESET_ALL}")
            else:
                click.echo(f"\n{Fore.YELLOW}⚠ xEdit path not configured{Style.RESET_ALL}")
            
            click.echo(f"\n{Fore.CYAN}Manual Launch:{Style.RESET_ALL}")
            click.echo(f"  1. Open xEdit manually")
            click.echo(f"  2. Load the conflicting plugins")
            click.echo(f"  3. Use the generated script: {result['script_path']}")
            click.echo(f"  4. Follow xEdit's conflict resolution workflow")
    else:
        click.echo(f"\n{Fore.RED}✗ Error creating xEdit files{Style.RESET_ALL}")
        if 'error' in result:
            click.echo(f"  Error: {result['error']}")


@conflicts.command('xedit-help')
def xedit_help():
    """Display help for xEdit integration"""
    xedit = XEditIntegration()
    help_text = xedit.get_configuration_help()
    click.echo(help_text)


@main.group()
def patch():
    """Create and apply patches"""
    pass


@patch.command('create')
@click.option('--name', '-n', required=True, help='Patch name')
@click.option('--description', '-d', default='', help='Patch description')
@click.option('--output', '-o', type=click.Path(),
              help='Output directory for patch file')
def create_patch(name, description, output):
    """Create a new patch"""
    patches_dir = Path(output) if output else Path("./patches")
    patcher = Patcher(patches_dir)
    
    patch = patcher.create_patch(name, description)
    
    # Save the patch
    filepath = patcher.save_patch(patch)
    
    click.echo(f"{Fore.GREEN}✓ Created patch: {name}{Style.RESET_ALL}")
    click.echo(f"Saved to: {filepath}")
    click.echo(f"\nEdit the patch file to add operations.")


@patch.command('list')
@click.option('--patches-dir', '-p', type=click.Path(exists=True),
              default='./patches', help='Patches directory')
def list_patches(patches_dir):
    """List all available patches"""
    patcher = Patcher(Path(patches_dir))
    patches = patcher.list_patches()
    
    if not patches:
        click.echo(f"{Fore.YELLOW}No patches found in {patches_dir}{Style.RESET_ALL}")
        return
    
    click.echo(f"{Fore.CYAN}=== Available Patches ==={Style.RESET_ALL}\n")
    
    for i, patch_name in enumerate(patches, 1):
        click.echo(f"{i:2d}. {patch_name}")


@patch.command('apply')
@click.option('--patch-file', '-p', type=click.Path(exists=True),
              required=True, help='Path to patch file')
@click.option('--mod-dir', '-m', type=click.Path(exists=True),
              required=True, help='Path to mod directory')
@click.option('--dry-run', is_flag=True, help='Simulate without making changes')
def apply_patch(patch_file, mod_dir, dry_run):
    """Apply a patch to a mod"""
    patcher = Patcher()
    
    # Load the patch
    patch = patcher.load_patch(Path(patch_file))
    
    click.echo(f"{Fore.CYAN}Applying patch: {patch.name}{Style.RESET_ALL}")
    click.echo(f"To mod: {mod_dir}")
    
    if dry_run:
        click.echo(f"{Fore.YELLOW}DRY RUN - No changes will be made{Style.RESET_ALL}")
    
    # Validate first
    validation = patcher.validate_patch(patch, Path(mod_dir))
    
    if not validation['valid']:
        click.echo(f"\n{Fore.RED}Validation failed:{Style.RESET_ALL}")
        for error in validation['errors']:
            click.echo(f"  • {error}")
        return
    
    if validation['warnings']:
        click.echo(f"\n{Fore.YELLOW}Warnings:{Style.RESET_ALL}")
        for warning in validation['warnings']:
            click.echo(f"  • {warning}")
    
    # Apply the patch
    result = patcher.apply_patch(patch, Path(mod_dir), dry_run)
    
    if result['success']:
        click.echo(f"\n{Fore.GREEN}✓ Patch applied successfully!{Style.RESET_ALL}")
        click.echo(f"Operations applied: {result['applied_operations']}")
    else:
        click.echo(f"\n{Fore.RED}✗ Patch application failed{Style.RESET_ALL}")
        click.echo(f"Operations applied: {result['applied_operations']}")
        click.echo(f"Operations failed: {result['failed_operations']}")
        
        if result['errors']:
            click.echo("\nErrors:")
            for error in result['errors']:
                click.echo(f"  • {error}")


@patch.command('create-xedit')
@click.option('--name', '-n', required=True, help='Patch name')
@click.option('--description', '-d', default='', help='Patch description')
@click.option('--xedit-path', '-x', type=click.Path(exists=True),
              help='Path to xEdit executable')
@click.option('--game', '-g', default='fallout4',
              help='Game type (fallout4)')
@click.option('--target-plugin', '-t',
              help='Target plugin name (e.g., MyPatch.esp)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./xedit_patches', help='Output directory for xEdit files')
@click.option('--auto-launch', is_flag=True,
              help='Automatically launch xEdit')
def create_patch_xedit(name, description, xedit_path, game, target_plugin, 
                      output_dir, auto_launch):
    """
    Create a patch that can be edited in xEdit
    
    This creates a new patch in Mossy Manager format and generates
    xEdit-compatible files for editing in xEdit.
    """
    click.echo(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║        Create Patch with xEdit - Mossy Manager           ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Create patch in Mossy Manager
    click.echo(f"{Fore.CYAN}Step 1: Creating patch in Mossy Manager...{Style.RESET_ALL}")
    patcher = Patcher()
    patch = patcher.create_patch(name, description)
    
    # Add placeholder operation
    patch.add_operation('merge', 
                       file='Data/example.ini',
                       content='# Patch content - edit in xEdit')
    
    # Save the patch
    patch_file = patcher.save_patch(patch)
    click.echo(f"  ✓ Created patch: {name}")
    click.echo(f"  ✓ Saved to: {patch_file}")
    
    # Initialize xEdit integration
    click.echo(f"\n{Fore.CYAN}Step 2: Preparing xEdit files...{Style.RESET_ALL}")
    xedit = XEditIntegration(
        xedit_path=Path(xedit_path) if xedit_path else None
    )
    
    # Auto-detect xEdit if not provided
    if not xedit_path and auto_launch:
        click.echo(f"  Detecting xEdit installation...")
        detected_path = xedit.detect_xedit(game)
        if detected_path:
            xedit.xedit_path = detected_path
            click.echo(f"  {Fore.GREEN}✓ Found xEdit: {detected_path}{Style.RESET_ALL}")
        else:
            click.echo(f"  {Fore.YELLOW}⚠ xEdit not auto-detected{Style.RESET_ALL}")
    
    # Export patch for xEdit
    output_path = Path(output_dir)
    patch_data = patcher.export_for_xedit(patch)
    
    result = xedit.create_patch_with_xedit(
        patch_data=patch_data,
        output_dir=output_path,
        target_plugin=target_plugin
    )
    
    if result['success']:
        click.echo(f"  {Fore.GREEN}✓ Patch exported: {result['export_path']}{Style.RESET_ALL}")
        click.echo(f"  {Fore.GREEN}✓ Script generated: {result['script_path']}{Style.RESET_ALL}")
        
        if result['xedit_launched']:
            click.echo(f"\n{Fore.GREEN}✓ xEdit launched successfully!{Style.RESET_ALL}")
            click.echo(f"\n{Fore.CYAN}Next Steps:{Style.RESET_ALL}")
            click.echo(f"  1. In xEdit, the script will create/load the target plugin")
            click.echo(f"  2. Add your patch modifications")
            click.echo(f"  3. Save and close xEdit")
            click.echo(f"  4. The patch is ready to use in your load order")
        else:
            click.echo(f"\n{Fore.CYAN}Manual Steps:{Style.RESET_ALL}")
            click.echo(f"  1. Open xEdit manually")
            click.echo(f"  2. Run the generated script: {result['script_path']}")
            click.echo(f"  3. Make your patch modifications")
            click.echo(f"  4. Save and close xEdit")
    else:
        click.echo(f"\n{Fore.RED}✗ Error creating xEdit files{Style.RESET_ALL}")
        if 'error' in result:
            click.echo(f"  Error: {result['error']}")


@patch.command('export-xedit')
@click.option('--patch-file', '-p', type=click.Path(exists=True),
              required=True, help='Path to patch file')
@click.option('--xedit-path', '-x', type=click.Path(exists=True),
              help='Path to xEdit executable')
@click.option('--target-plugin', '-t',
              help='Target plugin name (e.g., MyPatch.esp)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./xedit_patches', help='Output directory')
@click.option('--auto-launch', is_flag=True,
              help='Automatically launch xEdit')
def export_patch_xedit(patch_file, xedit_path, target_plugin, output_dir, auto_launch):
    """
    Export existing patch to xEdit format
    
    Takes an existing Mossy Manager patch and exports it in a format
    that can be edited in xEdit.
    """
    click.echo(f"{Fore.CYAN}Exporting patch to xEdit format...{Style.RESET_ALL}\n")
    
    # Load the patch
    patcher = Patcher()
    patch = patcher.load_patch(Path(patch_file))
    
    click.echo(f"Patch: {patch.name}")
    click.echo(f"Operations: {len(patch.operations)}")
    
    # Initialize xEdit integration
    xedit = XEditIntegration(
        xedit_path=Path(xedit_path) if xedit_path else None
    )
    
    # Export patch
    output_path = Path(output_dir)
    patch_data = patcher.export_for_xedit(patch)
    
    result = xedit.create_patch_with_xedit(
        patch_data=patch_data,
        output_dir=output_path,
        target_plugin=target_plugin
    )
    
    if result['success']:
        click.echo(f"\n{Fore.GREEN}✓ Export successful!{Style.RESET_ALL}")
        click.echo(f"Patch data: {result['export_path']}")
        click.echo(f"xEdit script: {result['script_path']}")
        
        if result['xedit_launched']:
            click.echo(f"\n{Fore.GREEN}✓ xEdit launched{Style.RESET_ALL}")
        elif auto_launch:
            click.echo(f"\n{Fore.YELLOW}⚠ xEdit not launched (path not configured){Style.RESET_ALL}")
            click.echo(f"Specify --xedit-path to enable auto-launch")
    else:
        click.echo(f"\n{Fore.RED}✗ Export failed{Style.RESET_ALL}")
        if 'error' in result:
            click.echo(f"Error: {result['error']}")


@main.group()
def fallout4():
    """Fallout 4 specific commands with advanced load order optimization"""
    pass


@fallout4.command('optimize')
@click.option('--mo2-path', '-m', type=click.Path(),
              help='Path to Mod Organizer 2 installation')
@click.option('--profile', '-p', required=True,
              help='MO2 profile name')
@click.option('--backup', is_flag=True, default=True,
              help='Create backup before optimizing')
def fo4_optimize(mo2_path, profile, backup):
    """
    Optimize Fallout 4 load order using advanced rules
    
    This command uses comprehensive Fallout 4 modding knowledge to
    create an optimized load order based on plugin categories,
    dependencies, and best practices.
    """
    from mossy_manager.integrations.mo2 import MO2Integration
    from mossy_manager.games.fallout4 import Fallout4Rules
    
    click.echo(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║     Fallout 4 Load Order Optimization - Mossy Manager    ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Initialize MO2 integration
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        click.echo(f"{Fore.CYAN}Detecting Mod Organizer 2...{Style.RESET_ALL}")
        mo2_path_detected = MO2Integration.detect_mo2_installation()
        if mo2_path_detected:
            click.echo(f"  {Fore.GREEN}✓ Found MO2 at: {mo2_path_detected}{Style.RESET_ALL}")
            mo2 = MO2Integration(mo2_path_detected)
        else:
            click.echo(f"  {Fore.RED}✗ Could not detect MO2 installation{Style.RESET_ALL}")
            click.echo(f"  Please specify --mo2-path manually")
            return
    
    # Check if profile exists
    profiles = mo2.list_profiles()
    if profile not in profiles:
        click.echo(f"{Fore.RED}Error: Profile '{profile}' not found{Style.RESET_ALL}")
        click.echo(f"\nAvailable profiles:")
        for p in profiles:
            click.echo(f"  • {p}")
        return
    
    click.echo(f"{Fore.CYAN}Profile: {profile}{Style.RESET_ALL}\n")
    
    # Read current load order
    click.echo(f"{Fore.CYAN}Step 1: Reading current load order...{Style.RESET_ALL}")
    current_plugins = mo2.read_plugins_txt(profile)
    current_loadorder = mo2.read_loadorder_txt(profile)
    
    if not current_loadorder:
        click.echo(f"  {Fore.RED}✗ No plugins found in profile{Style.RESET_ALL}")
        return
    
    click.echo(f"  {Fore.GREEN}✓ Loaded {len(current_loadorder)} plugins{Style.RESET_ALL}")
    
    # Create backup if requested
    if backup:
        click.echo(f"\n{Fore.CYAN}Step 2: Creating backup...{Style.RESET_ALL}")
        profile_path = mo2.get_profile_path(profile)
        if profile_path:
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = profile_path.parent / f"{profile}_backup_{timestamp}"
            shutil.copytree(profile_path, backup_dir)
            click.echo(f"  {Fore.GREEN}✓ Backup created: {backup_dir.name}{Style.RESET_ALL}")
    
    # Validate current load order
    click.echo(f"\n{Fore.CYAN}Step 3: Validating current load order...{Style.RESET_ALL}")
    issues = Fallout4Rules.validate_load_order(current_loadorder)
    
    if issues['errors']:
        click.echo(f"  {Fore.RED}Errors found:{Style.RESET_ALL}")
        for error in issues['errors']:
            click.echo(f"    • {error}")
    
    if issues['warnings']:
        click.echo(f"  {Fore.YELLOW}Warnings:{Style.RESET_ALL}")
        for warning in issues['warnings'][:5]:  # Show first 5
            click.echo(f"    • {warning}")
        if len(issues['warnings']) > 5:
            click.echo(f"    ... and {len(issues['warnings']) - 5} more")
    
    if not issues['errors'] and not issues['warnings']:
        click.echo(f"  {Fore.GREEN}✓ No issues found{Style.RESET_ALL}")
    
    # Optimize load order
    click.echo(f"\n{Fore.CYAN}Step 4: Optimizing load order...{Style.RESET_ALL}")
    optimized = Fallout4Rules.optimize_load_order(current_loadorder)
    
    # Show changes
    changes = 0
    for i, plugin in enumerate(optimized):
        if i >= len(current_loadorder) or current_loadorder[i] != plugin:
            changes += 1
    
    click.echo(f"  {Fore.GREEN}✓ Optimization complete{Style.RESET_ALL}")
    click.echo(f"    Plugins reordered: {changes}")
    
    # Get recommendations
    recommendations = Fallout4Rules.get_recommendations(optimized)
    if recommendations:
        click.echo(f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
        for rec in recommendations[:3]:
            click.echo(f"  • {rec}")
    
    # Write optimized load order
    click.echo(f"\n{Fore.CYAN}Step 5: Writing optimized load order...{Style.RESET_ALL}")
    
    # Preserve enabled/disabled state
    optimized_plugins = {}
    for plugin in optimized:
        optimized_plugins[plugin] = current_plugins.get(plugin, True)
    
    success1 = mo2.write_plugins_txt(profile, optimized_plugins)
    success2 = mo2.write_loadorder_txt(profile, optimized)
    
    if success1 and success2:
        click.echo(f"  {Fore.GREEN}✓ Load order saved successfully{Style.RESET_ALL}")
        click.echo(f"\n{Fore.GREEN}═══ Optimization Complete ═══{Style.RESET_ALL}")
        click.echo(f"\nYour Fallout 4 load order has been optimized!")
        click.echo(f"Launch the game through Mod Organizer 2 to apply changes.")
    else:
        click.echo(f"  {Fore.RED}✗ Error saving load order{Style.RESET_ALL}")


@main.command('auto')
@click.option('--mo2-path', '-m', type=click.Path(),
              help='Path to Mod Organizer 2 installation')
@click.option('--profile', '-p', required=True,
              help='MO2 profile name')
@click.option('--game', '-g', default='fallout4',
              type=click.Choice(['fallout4'], case_sensitive=False),
              help='Game type')
@click.option('--report', type=click.Path(),
              help='Write a combined JSON report (load order + conflicts + recommendations)')
@click.option('--backup', is_flag=True, default=True,
              help='Create a profile backup before writing changes')
@click.option('--apply', is_flag=True, default=False,
              help='Apply changes (writes plugins/loadorder). Default is dry-run.')
def auto_optimize(mo2_path, profile, game, report, backup, apply):
    """
    Automatic complete workflow: optimize, detect conflicts, and create patches
    
    This command performs the complete Mossy Manager workflow:
    1. Optimize load order using game-specific rules
    2. Scan for conflicts
    3. Generate conflict report
    4. Suggest patches needed
    
    This is the all-in-one solution for getting your game running smoothly!
    """
    from mossy_manager.integrations.mo2 import MO2Integration
    from mossy_manager.games.fallout4 import Fallout4Rules
    
    click.echo(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║        Mossy Manager - Automatic Optimization            ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║             Complete Workflow for {game.upper()}             ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Initialize MO2
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        click.echo(f"{Fore.CYAN}▶ Detecting Mod Organizer 2...{Style.RESET_ALL}")
        mo2_path_detected = MO2Integration.detect_mo2_installation()
        if mo2_path_detected:
            click.echo(f"  {Fore.GREEN}✓ Found MO2 at: {mo2_path_detected}{Style.RESET_ALL}\n")
            mo2 = MO2Integration(mo2_path_detected)
        else:
            click.echo(f"  {Fore.RED}✗ Could not detect MO2{Style.RESET_ALL}\n")
            return
    
    # Check profile
    if profile not in mo2.list_profiles():
        click.echo(f"{Fore.RED}Error: Profile '{profile}' not found{Style.RESET_ALL}")
        return
    
    # PHASE 1: Load Order Optimization
    click.echo(f"{Fore.CYAN}═══ PHASE 1: Load Order Optimization ═══{Style.RESET_ALL}\n")
    
    current_loadorder = mo2.read_loadorder_txt(profile)
    current_plugins = mo2.read_plugins_txt(profile)
    
    click.echo(f"Current plugins: {len(current_loadorder)}")
    
    # Backup profile if requested (only when apply is set)
    backup_dir = None
    if apply and backup:
        profile_path = mo2.get_profile_path(profile)
        if profile_path:
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = profile_path.parent / f"{profile}_backup_{timestamp}"
            shutil.copytree(profile_path, backup_dir)
            click.echo(f"Backup created: {backup_dir}")

    # Validate
    issues = Fallout4Rules.validate_load_order(current_loadorder)
    if issues['errors']:
        click.echo(f"{Fore.YELLOW}Found {len(issues['errors'])} errors{Style.RESET_ALL}")
    if issues['warnings']:
        click.echo(f"{Fore.YELLOW}Found {len(issues['warnings'])} warnings{Style.RESET_ALL}")
    
    # Optimize
    optimized = Fallout4Rules.optimize_load_order(current_loadorder)
    optimized_plugins = {p: current_plugins.get(p, True) for p in optimized}
    
    if apply:
        mo2.write_plugins_txt(profile, optimized_plugins)
        mo2.write_loadorder_txt(profile, optimized)
        click.echo(f"{Fore.GREEN}✓ Load order optimized{Style.RESET_ALL}\n")
    else:
        click.echo(f"{Fore.YELLOW}DRY RUN: optimized order calculated; not written. Use --apply to write.{Style.RESET_ALL}\n")
    
    # PHASE 2: Conflict Detection
    click.echo(f"{Fore.CYAN}═══ PHASE 2: Conflict Detection ═══{Style.RESET_ALL}\n")
    
    if mo2.mods_path and mo2.mods_path.exists():
        resolver = ConflictResolver(mo2.mods_path)
        
        # Scan mods
        mod_count = 0
        for mod_dir in mo2.mods_path.iterdir():
            if mod_dir.is_dir():
                resolver.scan_mod_files(mod_dir.name, mod_dir)
                mod_count += 1
        
        click.echo(f"Scanned {mod_count} mods")
        
        # Generate report
        stats = resolver.get_statistics()
        click.echo(f"Conflicts found: {stats['total_conflicts']}")
        click.echo(f"  Critical: {stats['critical']}")
        click.echo(f"  High: {stats['high']}")
        click.echo(f"  Medium: {stats['medium']}")
        click.echo(f"  Low: {stats['low']}")

        # Category summary
        analysis = resolver.analyze_conflicts(optimized)
        if analysis.get('by_category'):
            click.echo("  By category:")
            for cat, count in sorted(analysis['by_category'].items(), key=lambda kv: -kv[1]):
                click.echo(f"    • {cat}: {count}")
        
        click.echo(f"\n{Fore.GREEN}✓ Conflict detection complete{Style.RESET_ALL}\n")

        # Combined report (optional)
        if report:
            combined = {
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'profile': profile,
                'backup': str(backup_dir) if backup_dir else None,
                'load_order': {
                    'count': len(current_loadorder),
                    'issues': issues,
                    'optimized': optimized,
                    'slot_count': len([p for p in optimized if not p.lower().endswith('.esl')])
                },
                'conflicts': {
                    'summary': analysis
                },
                'recommendations': Fallout4Rules.get_recommendations(optimized)
            }
            try:
                with open(report, 'w', encoding='utf-8') as f:
                    json.dump(combined, f, indent=2)
                click.echo(f"{Fore.GREEN}Combined report saved:{Style.RESET_ALL} {report}")
            except Exception as e:
                click.echo(f"{Fore.RED}✗ Failed to write combined report: {e}{Style.RESET_ALL}")
        
        # PHASE 3: Recommendations
        click.echo(f"{Fore.CYAN}═══ PHASE 3: Recommendations ═══{Style.RESET_ALL}\n")
        
        recommendations = Fallout4Rules.get_recommendations(optimized)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                click.echo(f"{i}. {rec}")
        else:
            click.echo(f"{Fore.GREEN}No additional recommendations{Style.RESET_ALL}")
        
        # Suggest patches for critical conflicts
        if stats['critical'] > 0 or stats['high'] > 0:
            click.echo(f"\n{Fore.YELLOW}⚠ High-priority conflicts detected{Style.RESET_ALL}")
            click.echo(f"Consider creating patches with:")
            click.echo(f"  mossy conflicts resolve-xedit --mods-dir \"{mo2.mods_path}\" --profile \"{profile}\"")
    else:
        click.echo(f"{Fore.YELLOW}⚠ Mods directory not found, skipping conflict detection{Style.RESET_ALL}\n")
    
    # COMPLETE
    click.echo(f"\n{Fore.GREEN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.GREEN}║              AUTOMATIC OPTIMIZATION COMPLETE              ║{Style.RESET_ALL}")
    click.echo(f"{Fore.GREEN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    click.echo(f"{Fore.CYAN}Your game is ready!{Style.RESET_ALL}")
    click.echo(f"Launch {game.upper()} through Mod Organizer 2 to play with your optimized setup.")


@main.command('ui')
@click.option('--host', default='127.0.0.1', show_default=True, help='Host to bind the web UI')
@click.option('--port', default=8732, show_default=True, type=int, help='Port for the web UI')
@click.option('--open/--no-open', 'open_browser', default=True, show_default=True,
              help='Automatically open the browser')
def ui(host, port, open_browser):
    """Launch the local web UI (LOOT-style page)"""

    url = f"http://{host}:{port}/"
    if open_browser:
        threading.Thread(target=lambda: (time.sleep(0.8), webbrowser.open(url)), daemon=True).start()
        click.echo(f"Opening browser at {url}")
    else:
        click.echo(f"Start your browser at {url}")

    click.echo("Starting web server... (Ctrl+C to stop)")
    uvicorn.run(web_app, host=host, port=port, log_level="info")


@main.command()
def info():
    """Display information about Mossy Manager"""
    click.echo(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║           MOSSY MANAGER - MO2 Management Tool            ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}Version:{Style.RESET_ALL} 1.0.0
{Fore.GREEN}Game:{Style.RESET_ALL} Fallout 4

{Fore.CYAN}Features:{Style.RESET_ALL}
  • Load Order Management - Organize and optimize Fallout 4 plugin load order
  • Conflict Resolution - Detect and analyze mod conflicts
  • Patching System - Create and apply compatibility patches
  • xEdit Integration - Launch FO4Edit for advanced conflict resolution
  • Web UI - Browser-based LOOT-style interface (mossy ui)

{Fore.CYAN}Commands:{Style.RESET_ALL}
  loadorder      - Manage plugin load order (list, validate, optimize, auto-fo4)
  conflicts      - Detect and resolve mod conflicts (scan, resolve-xedit)
  patch          - Create and apply patches (create, list, apply, create-xedit)
  fallout4       - Fallout 4 specific commands (optimize)
  auto           - Complete automatic workflow: optimize + conflict detection
  ui             - Launch the local web UI
  info           - Display this information

{Fore.CYAN}Quick Start:{Style.RESET_ALL}
  1. Auto-optimize Fallout 4 load order:
     mossy loadorder auto-fo4 --profile "Default"

  2. Scan for conflicts:
     mossy conflicts scan --mods-dir path/to/mods

  3. Full automatic workflow:
     mossy auto --profile "Default" --apply

  4. Launch web UI:
     mossy ui

{Fore.CYAN}Documentation:{Style.RESET_ALL}
  https://github.com/POINTYTHRUNDRA654/Mossy-manager.

{Fore.YELLOW}Note:{Style.RESET_ALL} This tool is designed for use with Mod Organizer 2 (Fallout 4)
    """)




# ============================================================
# AI command group
# ============================================================

@main.group()
def ai():
    """AI-powered analysis and recommendations (machine learning brain)"""
    pass


@ai.command('analyze')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              help='Path to plugins.txt file')
@click.option('--mo2-path', '-m', type=click.Path(),
              help='Path to Mod Organizer 2 installation (auto-detect if omitted)')
@click.option('--profile', type=str, default=None,
              help='MO2 profile name (uses plugins.txt if omitted)')
@click.option('--output', '-o', type=click.Path(),
              help='Save full JSON report to this file')
def ai_analyze(plugins_file, mo2_path, profile, output):
    """
    Run a full AI analysis of your Fallout 4 load order.

    Combines conflict-risk prediction, anomaly detection, category
    clustering and the built-in Fallout 4 rule engine to produce a
    prioritised, plain-English recommendation list.
    """
    click.echo(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════╗")
    click.echo(f"║     Mossy Manager — AI Brain (Machine Learning)  ║")
    click.echo(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    # ── Collect load order ────────────────────────────────────────────
    load_order = []
    if plugins_file:
        mgr = LoadOrderManager()
        mgr.load_plugins_txt(Path(plugins_file))
        load_order = mgr.get_load_order()
    elif mo2_path or profile:
        if mo2_path:
            mo2 = MO2Integration(Path(mo2_path))
        else:
            detected = MO2Integration.detect_mo2_installation()
            if not detected:
                click.echo(f"{Fore.RED}✗ Could not detect MO2. Specify --mo2-path.{Style.RESET_ALL}")
                return
            mo2 = MO2Integration(detected)
        if profile:
            load_order = mo2.read_loadorder_txt(profile)

    if not load_order:
        click.echo(f"{Fore.YELLOW}⚠ No plugins loaded. Specify --plugins-file or --mo2-path + --profile.{Style.RESET_ALL}")
        return

    click.echo(f"Analysing {Fore.GREEN}{len(load_order)}{Style.RESET_ALL} plugins with AI brain…\n")

    brain = ModAIBrain()
    report = brain.full_analysis(load_order)

    # ── Print risk summary ────────────────────────────────────────────
    rs = report.get("risk_summary", {})
    click.echo(f"{Fore.CYAN}Risk Summary:{Style.RESET_ALL}")
    colour = {
        "critical": Fore.RED,
        "high": Fore.YELLOW,
        "medium": Fore.WHITE,
        "low": Fore.GREEN,
    }
    for level in ("critical", "high", "medium", "low"):
        count = rs.get(level, 0)
        c = colour.get(level, "")
        click.echo(f"  {c}{level.capitalize():8s}{Style.RESET_ALL} {count}")

    # ── Print anomalies ───────────────────────────────────────────────
    anomalies = report.get("anomalies", {}).get("anomalies", [])
    if anomalies:
        click.echo(f"\n{Fore.YELLOW}Load-Order Anomalies ({len(anomalies)}):{Style.RESET_ALL}")
        for a in anomalies[:5]:
            click.echo(f"  • [{a['position']:3d}] {a['plugin']}")
            click.echo(f"        {Fore.YELLOW}{a['reason']}{Style.RESET_ALL}")
        if len(anomalies) > 5:
            click.echo(f"  … and {len(anomalies) - 5} more")

    # ── Print recommendations ─────────────────────────────────────────
    recs = report.get("recommendations", [])
    if recs:
        click.echo(f"\n{Fore.CYAN}AI Recommendations ({len(recs)}):{Style.RESET_ALL}")
        for r in recs[:10]:
            p = r.get("priority", 4)
            c = Fore.RED if p == 1 else (Fore.YELLOW if p == 2 else
                (Fore.WHITE if p == 3 else Fore.CYAN))
            badge = {1: "CRITICAL", 2: "HIGH", 3: "MEDIUM", 4: "INFO"}.get(p, "INFO")
            click.echo(f"  {c}[{badge}]{Style.RESET_ALL} {r['message']}")
            detail = r.get("ai_detail", "")
            if detail:
                click.echo(f"         {detail}")
        if len(recs) > 10:
            click.echo(f"  … and {len(recs) - 10} more (use --output to see all)")

    # ── Cluster summary ───────────────────────────────────────────────
    clusters = report.get("clusters", {}).get("summary", {})
    if clusters:
        click.echo(f"\n{Fore.CYAN}Plugin Clusters:{Style.RESET_ALL}")
        for cid, desc in list(clusters.items())[:6]:
            click.echo(f"  • {desc}")

    # ── Optionally save JSON ──────────────────────────────────────────
    if output:
        try:
            Path(output).write_text(json.dumps(report, indent=2, default=str))
            click.echo(f"\n{Fore.GREEN}✓ Full report saved to: {output}{Style.RESET_ALL}")
        except Exception as exc:
            click.echo(f"{Fore.RED}✗ Could not write report: {exc}{Style.RESET_ALL}")

    click.echo(f"\n{Fore.GREEN}✓ AI analysis complete.{Style.RESET_ALL}\n")


@ai.command('score')
@click.argument('plugin_a')
@click.argument('plugin_b')
def ai_score(plugin_a, plugin_b):
    """
    Score the compatibility between two plugins.

    Example:
      mossy ai score WeaponOverhaul.esp ArmorMod.esp
    """
    brain = ModAIBrain()
    score = brain.score_compatibility(plugin_a, plugin_b)
    pct = int(score * 100)
    if pct >= 75:
        colour = Fore.GREEN
        verdict = "Likely compatible"
    elif pct >= 40:
        colour = Fore.YELLOW
        verdict = "May conflict — check manually"
    else:
        colour = Fore.RED
        verdict = "High conflict risk"

    click.echo(f"\nCompatibility: {colour}{pct}%{Style.RESET_ALL}  —  {verdict}")
    click.echo(f"  {plugin_a}  ↔  {plugin_b}\n")


@ai.command('risk')
@click.argument('plugin_name')
@click.option('--files', '-f', multiple=True,
              help='Files in the mod (repeat flag for multiple)')
def ai_risk(plugin_name, files):
    """
    Predict conflict-risk severity for a plugin.

    Example:
      mossy ai risk MyMod.esp --files scripts/myscript.pex --files textures/thing.dds
    """
    brain = ModAIBrain()
    result = brain.predict_conflict_risk(plugin_name, list(files) if files else None)

    colour = {
        "critical": Fore.RED,
        "high": Fore.YELLOW,
        "medium": Fore.WHITE,
        "low": Fore.GREEN,
    }.get(result["severity"], Fore.WHITE)

    click.echo(f"\nConflict Risk: {colour}{result['severity'].upper()}{Style.RESET_ALL}")
    click.echo(f"  {result['explanation']}")
    click.echo(f"\nProbabilities:")
    for label, prob in sorted(result["probabilities"].items()):
        bar = "█" * int(prob * 20)
        click.echo(f"  {label:8s} {bar:<20s} {int(prob * 100):3d}%")
    click.echo()


@ai.command('learn')
@click.argument('plugin_name')
@click.argument('severity', type=click.Choice(['low', 'medium', 'high', 'critical']))
@click.option('--files', '-f', multiple=True,
              help='Files in the mod (repeat for multiple)')
@click.option('--model-dir', type=click.Path(),
              default='./mossy_ai_model',
              help='Directory to persist the updated model')
def ai_learn(plugin_name, severity, files, model_dir):
    """
    Teach the AI the actual severity for a mod.

    This improves future predictions.  Example:
      mossy ai learn WeaponMod.esp high --files scripts/weapon.pex
    """
    brain = ModAIBrain(model_path=Path(model_dir))
    brain.learn_from_outcome(plugin_name, list(files) if files else None, severity)
    saved = brain.save(Path(model_dir))
    click.echo(f"\n{Fore.GREEN}✓ AI brain updated and saved to: {saved}{Style.RESET_ALL}")
    click.echo(f"  '{plugin_name}' → severity={severity}\n")


@ai.command('reason')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              help='Path to plugins.txt to analyse')
@click.option('--problem', '-d', default='',
              help='Free-text problem description (crash, CTD, texture, etc.)')
@click.option('--output', '-o', type=click.Path(),
              help='Save full JSON reasoning trace to this file')
def ai_reason(plugins_file, problem, output):
    """
    Advanced chain-of-thought reasoning about your load order or a problem.

    Examples:
      mossy ai reason --plugins-file plugins.txt
      mossy ai reason --problem "game crashes on load"
      mossy ai reason --plugins-file plugins.txt --problem "purple textures"
    """
    click.echo(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════╗")
    click.echo(f"║     Mossy Manager — Advanced Reasoner            ║")
    click.echo(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    load_order = []
    if plugins_file:
        mgr = LoadOrderManager()
        mgr.load_plugins_txt(Path(plugins_file))
        load_order = mgr.get_load_order()
        click.echo(f"Loaded {Fore.GREEN}{len(load_order)}{Style.RESET_ALL} plugins from {plugins_file}\n")

    reasoner = ModReasoner()

    if problem:
        result = reasoner.diagnose(problem, load_order)
    elif load_order:
        result = reasoner.reason_about_load_order(load_order)
    else:
        click.echo(f"{Fore.YELLOW}⚠ Provide --plugins-file and/or --problem.{Style.RESET_ALL}")
        return

    # ── Print steps ───────────────────────────────────────────────────
    sev_colour = {
        "critical": Fore.RED,
        "error":    Fore.RED,
        "warning":  Fore.YELLOW,
        "info":     Fore.CYAN,
    }
    click.echo(f"{Fore.CYAN}Reasoning trace ({len(result.steps)} step(s)):{Style.RESET_ALL}")
    for s in result.steps:
        c = sev_colour.get(s.severity, Fore.WHITE)
        badge = f"[{s.severity.upper():8s}]"
        click.echo(f"  {c}{badge}{Style.RESET_ALL} {s.rule}")
        click.echo(f"    Observed : {s.observation}")
        click.echo(f"    Concluded: {s.deduction}")

    # ── Conclusion ────────────────────────────────────────────────────
    overall_c = sev_colour.get(result.severity, Fore.WHITE)
    click.echo(f"\n{Fore.CYAN}Conclusion:{Style.RESET_ALL}")
    click.echo(f"  {overall_c}{result.conclusion}{Style.RESET_ALL}")
    click.echo(f"  Confidence: {int(result.confidence * 100)}%\n")

    # ── Action plan ───────────────────────────────────────────────────
    if result.action_plan:
        click.echo(f"{Fore.CYAN}Action Plan:{Style.RESET_ALL}")
        for i, action in enumerate(result.action_plan, 1):
            click.echo(f"  {i}. {action}")
        click.echo()

    # ── Save JSON ─────────────────────────────────────────────────────
    if output:
        try:
            Path(output).write_text(
                json.dumps(result.to_dict(), indent=2, default=str)
            )
            click.echo(f"{Fore.GREEN}✓ Reasoning trace saved to: {output}{Style.RESET_ALL}\n")
        except Exception as exc:
            click.echo(f"{Fore.RED}✗ Could not write output: {exc}{Style.RESET_ALL}")

    click.echo(f"{Fore.CYAN}Tip: run 'mossy ai script' to auto-generate fix scripts.{Style.RESET_ALL}\n")


@ai.command('script')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              help='Path to plugins.txt')
@click.option('--problem', '-d', default='',
              help='Free-text problem description')
@click.option('--patch-name', default='MossyAutoFix',
              help='Name for generated patch plugin (default: MossyAutoFix)')
@click.option('--type', 'script_type',
              type=click.Choice([
                  'conflict_patch', 'clean_itms', 'esl_flag',
                  'papyrus_logging', 'archive_invalidation',
                  'performance_high', 'performance_low',
                  'safe_launch', 'backup_profiles', 'auto',
              ]),
              default='auto',
              help='Script type to generate (default: auto — chosen by AI reasoning)')
@click.option('--plugins', multiple=True,
              help='Plugin names for esl_flag / conflict_patch (repeat flag)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./mossy_scripts',
              help='Directory to write scripts into (default: ./mossy_scripts)')
def ai_script(plugins_file, problem, patch_name, script_type, plugins, output_dir):
    """
    Generate advanced scripts for Fallout 4 mod management.

    Examples:
      mossy ai script --type conflict_patch --patch-name MyFix --plugins ModA.esp ModB.esp
      mossy ai script --type papyrus_logging
      mossy ai script --type safe_launch
      mossy ai script --plugins-file plugins.txt --problem "CTD on load" --type auto
    """
    click.echo(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════╗")
    click.echo(f"║     Mossy Manager — Script Writer                ║")
    click.echo(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    writer = ScriptWriter(output_dir=Path(output_dir))
    out_dir = Path(output_dir)
    written: list = []

    # ── Auto mode: reason first, then generate ────────────────────────
    if script_type == 'auto':
        load_order: list = []
        if plugins_file:
            mgr = LoadOrderManager()
            mgr.load_plugins_txt(Path(plugins_file))
            load_order = mgr.get_load_order()

        reasoner = ModReasoner()
        if problem:
            reasoning = reasoner.diagnose(problem, load_order)
        elif load_order:
            reasoning = reasoner.reason_about_load_order(load_order)
        else:
            click.echo(f"{Fore.YELLOW}⚠ In auto mode provide --plugins-file and/or --problem.{Style.RESET_ALL}")
            return

        scripts = writer.from_reasoning(
            reasoning,
            patch_name=patch_name,
            plugins=list(plugins) if plugins else None,
        )
        written = writer.write_all(scripts, out_dir)

        click.echo(f"Reasoner found {len(reasoning.steps)} issue(s). "
                   f"Generated {len(scripts)} script(s):\n")
        for path in written:
            click.echo(f"  {Fore.GREEN}✓{Style.RESET_ALL} {path}")

    # ── Explicit xEdit scripts ─────────────────────────────────────────
    elif script_type == 'conflict_patch':
        content = writer.xedit_conflict_patch(patch_name, list(plugins))
        p = writer.write(f"{patch_name}_conflict_patch.pas", content, out_dir)
        written = [p]

    elif script_type == 'clean_itms':
        if not plugins:
            click.echo(f"{Fore.RED}✗ --plugins required for clean_itms{Style.RESET_ALL}")
            return
        for plugin_name in plugins:
            content = writer.xedit_clean_itms(plugin_name)
            p = writer.write(f"{plugin_name}_clean_itms.pas", content, out_dir)
            written.append(p)

    elif script_type == 'esl_flag':
        if not plugins:
            click.echo(f"{Fore.RED}✗ --plugins required for esl_flag{Style.RESET_ALL}")
            return
        content = writer.xedit_esl_flag(list(plugins))
        p = writer.write(f"{patch_name}_esl_flag.pas", content, out_dir)
        written = [p]

    # ── INI tweaks ────────────────────────────────────────────────────
    elif script_type in ('papyrus_logging', 'archive_invalidation',
                         'performance_high', 'performance_low'):
        content = writer.ini_tweak(script_type)
        p = writer.write(f"{script_type}.ini", content, out_dir)
        written = [p]

    # ── Batch scripts ─────────────────────────────────────────────────
    elif script_type == 'safe_launch':
        content = writer.batch_safe_launch()
        p = writer.write("safe_launch.bat", content, out_dir)
        written = [p]

    elif script_type == 'backup_profiles':
        content = writer.batch_backup_profiles()
        p = writer.write("backup_profiles.ps1", content, out_dir)
        written = [p]

    for path in written:
        click.echo(f"{Fore.GREEN}✓ Script written:{Style.RESET_ALL} {path}")

    if written:
        click.echo(f"\n{Fore.CYAN}Open the script(s) above to review before use.{Style.RESET_ALL}\n")


@ai.command('fix')
@click.option('--plugins-file', '-p', type=click.Path(exists=True),
              help='Path to plugins.txt to analyse')
@click.option('--loadorder-file', '-l', type=click.Path(),
              help='Path to loadorder.txt (enables direct Python fix application)')
@click.option('--problem', '-d', default='',
              help='Free-text problem description (crash, CTD, texture, etc.)')
@click.option('--patch-name', default='MossyAutoFix',
              help='Base name for generated patch files (default: MossyAutoFix)')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./mossy_fixes',
              help='Directory to write fix scripts into (default: ./mossy_fixes)')
@click.option('--apply', 'do_apply', is_flag=True, default=False,
              help='Automatically apply Python fixes that can run without xEdit')
def ai_fix(plugins_file, loadorder_file, problem, patch_name, output_dir, do_apply):
    """
    Reason about your load order and generate complete, working fix scripts.

    For every issue found the engine writes a ready-to-run script:
      • Python (.py)    — load-order fixes, applied immediately with --apply
      • Pascal (.pas)   — xEdit conflict patches with exact record guards
      • INI fragment    — Fallout4Custom.ini tweaks (Papyrus logging, etc.)
      • Batch (.bat)    — safe F4SE launch wrapper with plugin-cap check

    Examples:
      mossy ai fix --plugins-file plugins.txt --apply
      mossy ai fix --plugins-file plugins.txt --problem "CTD on load"
      mossy ai fix --problem "purple textures" --output-dir ./my_fixes
    """
    click.echo(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════╗")
    click.echo(f"║   Mossy Manager — Fix Generator                  ║")
    click.echo(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    # ── Load plugins ──────────────────────────────────────────────────
    load_order: list = []
    if plugins_file:
        mgr = LoadOrderManager()
        mgr.load_plugins_txt(Path(plugins_file))
        load_order = mgr.get_load_order()
        click.echo(f"Loaded {Fore.GREEN}{len(load_order)}{Style.RESET_ALL} plugins\n")

    if not load_order and not problem:
        click.echo(f"{Fore.YELLOW}⚠ Provide --plugins-file and/or --problem.{Style.RESET_ALL}")
        return

    # ── Reason about the load order / problem ────────────────────────
    reasoner = ModReasoner()
    if problem:
        reasoning = reasoner.diagnose(problem, load_order)
    else:
        reasoning = reasoner.reason_about_load_order(load_order)

    lo_path = Path(loadorder_file) if loadorder_file else None

    click.echo(f"Reasoner found {Fore.YELLOW}{len(reasoning.steps)}{Style.RESET_ALL} issue(s):\n")
    sev_colour = {"critical": Fore.RED, "error": Fore.RED,
                  "warning": Fore.YELLOW, "info": Fore.CYAN}
    for s in reasoning.steps:
        c = sev_colour.get(s.severity, Fore.WHITE)
        click.echo(f"  {c}[{s.severity.upper():8s}]{Style.RESET_ALL} {s.rule}: {s.observation[:80]}")

    # ── Generate fixes ────────────────────────────────────────────────
    fg = FixGenerator(patch_name=patch_name)
    fixes = fg.generate_fixes(reasoning, load_order=load_order, loadorder_path=lo_path)

    click.echo(f"\nGenerated {Fore.GREEN}{len(fixes)}{Style.RESET_ALL} fix script(s):\n")
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for fix in fixes:
        dest = out_dir / fix.filename
        dest.write_text(fix.code, encoding="utf-8")
        auto_tag = f" {Fore.GREEN}[auto-apply available]{Style.RESET_ALL}" if fix.can_auto_apply else ""
        click.echo(f"  [{fix.fix_type:10s}] {dest}{auto_tag}")
        click.echo(f"               {fix.description[:80]}")

        if do_apply and fix.can_auto_apply:
            try:
                result = fix.apply()
                click.echo(f"  {Fore.GREEN}  ✓ Applied:{Style.RESET_ALL} {result}")
            except Exception as exc:
                click.echo(f"  {Fore.RED}  ✗ Apply failed:{Style.RESET_ALL} {exc}")

    click.echo(f"\n{Fore.CYAN}All scripts written to: {out_dir}{Style.RESET_ALL}")
    if not do_apply:
        click.echo(f"{Fore.CYAN}Tip: re-run with --apply to auto-apply Python fixes.{Style.RESET_ALL}\n")


# ============================================================
# Backup command group
# ============================================================

@main.group()
def backup():
    """Create, list, restore and clean up profile backups"""
    pass


def _get_backup_manager(backups_dir: Optional[str]) -> BackupManager:
    default = Path.home() / ".mossy-manager" / "backups"
    return BackupManager(Path(backups_dir) if backups_dir else default)


@backup.command('create')
@click.option('--mo2-path', '-m', type=click.Path(), help='Path to MO2 installation')
@click.option('--profile', '-p', required=True, help='Profile name to back up')
@click.option('--label', '-l', default='', help='Optional label for this backup')
@click.option('--backups-dir', type=click.Path(),
              help='Directory to store backups (default: ~/.mossy-manager/backups)')
def backup_create(mo2_path, profile, label, backups_dir):
    """Create a timestamped backup of an MO2 profile."""
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        detected = MO2Integration.detect_mo2_installation()
        if not detected:
            click.echo(f"{Fore.RED}✗ Could not detect MO2. Specify --mo2-path.{Style.RESET_ALL}")
            return
        mo2 = MO2Integration(detected)

    profile_path = mo2.get_profile_path(profile)
    if not profile_path:
        click.echo(f"{Fore.RED}✗ Profile '{profile}' not found.{Style.RESET_ALL}")
        return

    mgr = _get_backup_manager(backups_dir)
    dest = mgr.create_backup(profile_path, label=label, profile_name=profile)
    click.echo(f"{Fore.GREEN}✓ Backup created:{Style.RESET_ALL} {dest}")


@backup.command('list')
@click.option('--profile', '-p', default=None, help='Filter by profile name')
@click.option('--backups-dir', type=click.Path(),
              help='Directory where backups are stored')
def backup_list(profile, backups_dir):
    """List all available backups."""
    mgr = _get_backup_manager(backups_dir)
    entries = mgr.list_backups(profile_name=profile)

    if not entries:
        click.echo(f"{Fore.YELLOW}No backups found.{Style.RESET_ALL}")
        return

    click.echo(f"\n{Fore.CYAN}Available backups ({len(entries)}):{Style.RESET_ALL}\n")
    rows = []
    for i, e in enumerate(entries, 1):
        size_mb = round(e.size_bytes / (1024 * 1024), 1)
        rows.append([i, e.label, e.source_profile, e.created_at[:19], f"{size_mb} MB"])
    click.echo(tabulate(rows,
                        headers=["#", "Label", "Profile", "Created", "Size"],
                        tablefmt="simple"))
    click.echo()


@backup.command('restore')
@click.option('--backup-path', '-b', type=click.Path(exists=True), required=True,
              help='Path to the backup directory to restore')
@click.option('--target', '-t', type=click.Path(), required=True,
              help='Destination path to restore into')
@click.option('--overwrite/--no-overwrite', default=True,
              help='Overwrite the destination if it already exists')
def backup_restore(backup_path, target, overwrite):
    """Restore a backup to a specified directory."""
    mgr = _get_backup_manager(None)
    try:
        mgr.restore_backup(Path(backup_path), Path(target), overwrite=overwrite)
        click.echo(f"{Fore.GREEN}✓ Restored to: {target}{Style.RESET_ALL}")
    except FileExistsError as exc:
        click.echo(f"{Fore.RED}✗ {exc}{Style.RESET_ALL}")
    except Exception as exc:
        click.echo(f"{Fore.RED}✗ Restore failed: {exc}{Style.RESET_ALL}")


@backup.command('cleanup')
@click.option('--profile', '-p', default=None, help='Only clean up backups for this profile')
@click.option('--keep', '-k', default=5, show_default=True,
              help='Number of most-recent backups to keep')
@click.option('--backups-dir', type=click.Path(),
              help='Directory where backups are stored')
def backup_cleanup(profile, keep, backups_dir):
    """Delete old backups, keeping the N most recent."""
    mgr = _get_backup_manager(backups_dir)
    deleted = mgr.cleanup_old_backups(keep=keep, profile_name=profile)
    if deleted:
        click.echo(f"{Fore.GREEN}✓ Deleted {deleted} old backup(s).{Style.RESET_ALL}")
    else:
        click.echo(f"{Fore.CYAN}Nothing to clean up.{Style.RESET_ALL}")


# ============================================================
# Status command
# ============================================================

@main.command('status')
@click.option('--mo2-path', '-m', type=click.Path(), help='Path to MO2 installation')
@click.option('--profile', '-p', default=None, help='Profile to analyse (optional)')
@click.option('--json', 'output_json', is_flag=True, default=False,
              help='Output health report as JSON')
@click.option('--no-ai', is_flag=True, default=False,
              help='Skip AI brain analysis (faster)')
def status(mo2_path, profile, output_json, no_ai):
    """
    One-shot health check: MO2 installation, profile summary,
    plugin cap, dependency issues, orphaned mods, and AI quick-scan.

    Uses ModHealthChecker to produce a scored health report (0-100).
    """
    if not output_json:
        click.echo(f"\n{Fore.CYAN}╔══════════════════════════════════════════════════╗")
        click.echo(f"║         Mossy Manager — Status Report            ║")
        click.echo(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    # ── MO2 detection ─────────────────────────────────────────────────
    if mo2_path:
        mo2 = MO2Integration(Path(mo2_path))
    else:
        detected = MO2Integration.detect_mo2_installation()
        mo2 = MO2Integration(detected) if detected else MO2Integration()

    if not output_json:
        if mo2.mo2_path:
            click.echo(f"{Fore.GREEN}✓ MO2:{Style.RESET_ALL} {mo2.mo2_path}")
        else:
            click.echo(f"{Fore.YELLOW}⚠ MO2 not detected — use --mo2-path to specify.{Style.RESET_ALL}")

    profiles = mo2.list_profiles()
    if not output_json:
        click.echo(f"  Profiles: {len(profiles)}")
        for p in profiles[:5]:
            click.echo(f"    • {p}")
        if len(profiles) > 5:
            click.echo(f"    … and {len(profiles) - 5} more")

    # ── Load the target profile ───────────────────────────────────────
    target_profile = profile or (profiles[0] if profiles else None)
    load_order = []
    if target_profile:
        load_order = mo2.read_loadorder_txt(target_profile)

    if not load_order:
        if output_json:
            click.echo(json.dumps({"error": "No load order found", "score": 0}))
        else:
            click.echo(f"\n{Fore.YELLOW}⚠ No load order found. Specify --mo2-path and --profile.{Style.RESET_ALL}\n")
        return

    # ── Run health checker ────────────────────────────────────────────
    checker = ModHealthChecker(run_ai=not no_ai)
    report  = checker.check(load_order, profile=target_profile, mo2=mo2)

    if output_json:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return

    # ── Render coloured report ────────────────────────────────────────
    score_colour = (
        Fore.GREEN  if report.score >= 80 else
        Fore.YELLOW if report.score >= 50 else
        Fore.RED
    )
    click.echo(f"\n{Fore.CYAN}Profile: {target_profile}{Style.RESET_ALL}")
    click.echo(f"  Plugins   : {report.plugin_count}  "
               f"(slot usage: {report.slot_count}/255)")
    click.echo(f"  ESL slots : {report.esl_candidates} plugin(s) could be ESL-flagged")
    click.echo(f"  Health    : {score_colour}{report.score}/100{Style.RESET_ALL}\n")

    sev_colour = {
        "critical": Fore.RED,
        "error":    Fore.RED,
        "warning":  Fore.YELLOW,
        "info":     Fore.CYAN,
    }
    sev_icon = {
        "critical": "✗",
        "error":    "✗",
        "warning":  "⚠",
        "info":     "ℹ",
    }
    if report.issues:
        for issue in report.issues:
            c = sev_colour.get(issue.severity, Fore.WHITE)
            icon = sev_icon.get(issue.severity, " ")
            plugin_tag = f" [{issue.plugin}]" if issue.plugin else ""
            click.echo(f"  {c}{icon} [{issue.severity.upper():8s}]{plugin_tag}{Style.RESET_ALL} "
                       f"{issue.message[:100]}")
    else:
        click.echo(f"  {Fore.GREEN}✓ No issues found — load order looks healthy!{Style.RESET_ALL}")

    click.echo(f"\n{Fore.CYAN}─ Run 'mossy ai analyze' for a full AI report ─{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}─ Run 'mossy ai fix'     to generate fix scripts ─{Style.RESET_ALL}\n")


if __name__ == '__main__':
    main()