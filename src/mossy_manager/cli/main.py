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
