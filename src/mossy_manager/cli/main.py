"""
Command-line interface for Mossy Manager
"""

import sys
import logging
from pathlib import Path
from typing import Optional

import click
from colorama import init, Fore, Style
from tabulate import tabulate

from mossy_manager.core.load_order import LoadOrderManager
from mossy_manager.core.conflict_resolver import ConflictResolver
from mossy_manager.core.patcher import Patcher
from mossy_manager.utils.xedit_integration import XEditIntegration

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(verbose):
    """
    Mossy Manager - MO2 Load Order Manager, Conflict Resolution, and Patching Tool
    
    A comprehensive tool for managing Mod Organizer 2 load orders,
    detecting and resolving mod conflicts, and creating compatibility patches.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


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
def optimize_loadorder(plugins_file, output):
    """Optimize load order automatically"""
    manager = LoadOrderManager()
    manager.load_plugins_txt(Path(plugins_file))
    
    click.echo(f"{Fore.CYAN}Optimizing load order...{Style.RESET_ALL}")
    optimized = manager.optimize_load_order()
    
    click.echo(f"{Fore.GREEN}✓ Optimized {len(optimized)} plugins{Style.RESET_ALL}")
    
    if output:
        manager.save_loadorder_txt(Path(output))
        click.echo(f"Saved to: {output}")
    else:
        click.echo("\nOptimized order:")
        for i, plugin_name in enumerate(optimized[:20], 1):
            click.echo(f"  {i:3d}. {plugin_name}")
        if len(optimized) > 20:
            click.echo(f"  ... and {len(optimized) - 20} more")


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
@click.option('--xedit-path', '-x', type=click.Path(exists=True),
              help='Path to xEdit executable (SSEEdit.exe, TES5Edit.exe, etc.)')
@click.option('--game', '-g', default='skyrimse',
              help='Game type (skyrimse, skyrim, fallout4, etc.)')
@click.option('--patch-name', '-p', default='MossyManager_ConflictPatch',
              help='Name for the conflict resolution patch')
@click.option('--output-dir', '-o', type=click.Path(),
              default='./xedit_output', help='Output directory for xEdit files')
@click.option('--auto-launch', is_flag=True, default=False,
              help='Automatically launch xEdit after export')
def resolve_xedit(mods_dir, xedit_path, game, patch_name, output_dir, auto_launch):
    """
    Create conflict resolution patch using xEdit
    
    This command scans for conflicts, exports them to xEdit format,
    generates a helper script, and optionally launches xEdit for
    interactive conflict resolution.
    """
    click.echo(f"{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}║     xEdit Conflict Resolution - Mossy Manager            ║{Style.RESET_ALL}")
    click.echo(f"{Fore.CYAN}╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    # Initialize conflict resolver
    resolver = ConflictResolver(Path(mods_dir))
    
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
    
    # Initialize xEdit integration
    xedit = XEditIntegration(
        xedit_path=Path(xedit_path) if xedit_path else None,
        game_data_path=None
    )
    
    # Auto-detect xEdit if not provided
    if not xedit_path:
        click.echo(f"\n{Fore.CYAN}Step 2: Detecting xEdit installation...{Style.RESET_ALL}")
        detected_path = xedit.detect_xedit(game)
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
    output_path = Path(output_dir)
    
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
@click.option('--game', '-g', default='skyrimse',
              help='Game type (skyrimse, fallout4, etc.)')
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
def auto_optimize(mo2_path, profile, game):
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
    
    # Validate
    issues = Fallout4Rules.validate_load_order(current_loadorder)
    if issues['errors']:
        click.echo(f"{Fore.YELLOW}Found {len(issues['errors'])} errors{Style.RESET_ALL}")
    if issues['warnings']:
        click.echo(f"{Fore.YELLOW}Found {len(issues['warnings'])} warnings{Style.RESET_ALL}")
    
    # Optimize
    optimized = Fallout4Rules.optimize_load_order(current_loadorder)
    optimized_plugins = {p: current_plugins.get(p, True) for p in optimized}
    
    # Save
    mo2.write_plugins_txt(profile, optimized_plugins)
    mo2.write_loadorder_txt(profile, optimized)
    
    click.echo(f"{Fore.GREEN}✓ Load order optimized{Style.RESET_ALL}\n")
    
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
        
        click.echo(f"\n{Fore.GREEN}✓ Conflict detection complete{Style.RESET_ALL}\n")
        
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


@main.command()
def info():
    """Display information about Mossy Manager"""
    click.echo(f"""
{Fore.CYAN}╔═══════════════════════════════════════════════════════════╗
║           MOSSY MANAGER - MO2 Management Tool            ║
╚═══════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}Version:{Style.RESET_ALL} 0.1.0

{Fore.CYAN}Features:{Style.RESET_ALL}
  • Load Order Management - Organize and optimize plugin load order
  • Conflict Resolution - Detect and analyze mod conflicts
  • Patching System - Create and apply compatibility patches

{Fore.CYAN}Commands:{Style.RESET_ALL}
  loadorder  - Manage plugin load order
  conflicts  - Detect and resolve mod conflicts
  patch      - Create and apply patches
  info       - Display this information

{Fore.CYAN}Quick Start:{Style.RESET_ALL}
  1. List load order:
     mossy loadorder list --plugins-file path/to/plugins.txt
  
  2. Scan for conflicts:
     mossy conflicts scan --mods-dir path/to/mods
  
  3. Create a patch:
     mossy patch create --name "MyPatch" --description "Fixes compatibility"

{Fore.CYAN}Documentation:{Style.RESET_ALL}
  https://github.com/POINTYTHRUNDRA654/Mossy-manager.

{Fore.YELLOW}Note:{Style.RESET_ALL} This tool is designed for use with Mod Organizer 2
    """)


if __name__ == '__main__':
    main()
