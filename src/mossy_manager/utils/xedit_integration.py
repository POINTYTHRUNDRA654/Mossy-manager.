"""
xEdit Integration for Mossy Manager
Provides integration with xEdit (SSEEdit, TES5Edit, FO4Edit, etc.) for advanced conflict resolution
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


class XEditIntegration:
    """
    Integration with xEdit tools for advanced conflict resolution
    
    xEdit is a powerful tool for editing Bethesda game plugins and creating
    conflict resolution patches. This class provides methods to:
    - Export conflict information in xEdit-compatible format
    - Launch xEdit with specific plugins for conflict resolution
    - Generate xEdit scripts for automated patch creation
    """
    
    def __init__(self, xedit_path: Optional[Path] = None, game_data_path: Optional[Path] = None):
        """
        Initialize xEdit integration
        
        Args:
            xedit_path: Path to xEdit executable (SSEEdit.exe, TES5Edit.exe, etc.)
            game_data_path: Path to game's Data directory
        """
        self.xedit_path = xedit_path
        self.game_data_path = game_data_path
        self.supported_games = {
            'skyrim': 'TES5Edit.exe',
            'skyrimse': 'SSEEdit.exe',
            'fallout4': 'FO4Edit.exe',
            'fallout3': 'FO3Edit.exe',
            'falloutnv': 'FNVEdit.exe',
            'oblivion': 'TES4Edit.exe',
        }
        
    def detect_xedit(self, game: str = 'skyrimse') -> Optional[Path]:
        """
        Try to detect xEdit installation
        
        Args:
            game: Game name (skyrim, skyrimse, fallout4, etc.)
            
        Returns:
            Path to xEdit executable if found, None otherwise
        """
        exe_name = self.supported_games.get(game.lower())
        if not exe_name:
            logger.warning(f"Unsupported game: {game}")
            return None
        
        # Common installation paths to check
        search_paths = [
            Path.home() / "Downloads",
            Path("C:/") / "Modding" / "Tools",
            Path("C:/") / "Games" / "Modding",
            Path.home() / "Documents" / "Modding",
        ]
        
        for base_path in search_paths:
            if base_path.exists():
                for item in base_path.rglob(exe_name):
                    if item.is_file():
                        logger.info(f"Found xEdit at: {item}")
                        return item
        
        return None
    
    def export_conflicts_for_xedit(self, 
                                   conflicts: List[Dict[str, Any]], 
                                   output_path: Path) -> None:
        """
        Export conflicts in a format suitable for xEdit processing
        
        Args:
            conflicts: List of conflict dictionaries
            output_path: Path to save the export file
        """
        logger.info(f"Exporting {len(conflicts)} conflicts for xEdit")
        
        export_data = {
            'version': '1.0',
            'tool': 'Mossy Manager',
            'conflicts': []
        }
        
        for conflict in conflicts:
            conflict_entry = {
                'type': conflict.get('type', 'unknown'),
                'resource': conflict.get('resource', ''),
                'severity': conflict.get('severity', 'medium'),
                'mods': conflict.get('mods', []),
                'plugins': self._extract_plugins_from_conflict(conflict)
            }
            export_data['conflicts'].append(conflict_entry)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported conflicts to: {output_path}")
    
    def _extract_plugins_from_conflict(self, conflict: Dict[str, Any]) -> List[str]:
        """Extract plugin names from conflict information"""
        plugins = []
        resource = conflict.get('resource', '')
        
        # If the conflict involves plugin files directly
        if resource.lower().endswith(('.esp', '.esm', '.esl')):
            plugins.append(resource)
        
        return plugins
    
    def generate_xedit_script(self, 
                             conflicts: List[Dict[str, Any]], 
                             output_path: Path,
                             patch_name: str = "MossyManager_Patch") -> Path:
        """
        Generate a Pascal script for xEdit to create conflict resolution patch
        
        Args:
            conflicts: List of conflicts to resolve
            output_path: Path to save the script
            patch_name: Name for the generated patch
            
        Returns:
            Path to the generated script file
        """
        logger.info(f"Generating xEdit script for {len(conflicts)} conflicts")
        
        script_content = self._build_xedit_script(conflicts, patch_name)
        
        script_path = output_path / f"{patch_name}_script.pas"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"Generated xEdit script: {script_path}")
        return script_path
    
    def _build_xedit_script(self, conflicts: List[Dict[str, Any]], patch_name: str) -> str:
        """Build the Pascal script content for xEdit"""
        
        # Extract unique plugins from conflicts
        plugins = set()
        for conflict in conflicts:
            conflict_plugins = self._extract_plugins_from_conflict(conflict)
            plugins.update(conflict_plugins)
        
        plugin_list = ', '.join(f"'{p}'" for p in plugins)
        
        script = f'''unit {patch_name.replace(" ", "_")}_Script;

{{
  Mossy Manager - Automated Conflict Resolution Script
  Generated for patch: {patch_name}
  
  This script creates a conflict resolution patch by analyzing
  conflicts between the specified plugins.
}}

var
  patchPlugin: IInterface;

function Initialize: integer;
begin
  Result := 0;
  
  // Create new patch plugin
  patchPlugin := AddNewFileName('{patch_name}.esp', False);
  if not Assigned(patchPlugin) then begin
    AddMessage('Failed to create patch plugin');
    Result := 1;
    Exit;
  end;
  
  AddMessage('Created patch plugin: {patch_name}.esp');
  AddMessage('Resolving conflicts from plugins: {plugin_list}');
  
  // Note: Actual conflict resolution requires manual intervention in xEdit
  // This script sets up the patch file. Use xEdit''s conflict detection
  // and resolution features to complete the patch.
end;

function Process(e: IInterface): integer;
begin
  Result := 0;
  // Processing logic would go here for automated resolution
  // In practice, most conflict resolution requires manual review
end;

function Finalize: integer;
begin
  Result := 0;
  AddMessage('Patch creation complete. Review and save in xEdit.');
end;

end.
'''
        return script
    
    def launch_xedit(self, 
                    plugins: List[str],
                    script_path: Optional[Path] = None,
                    auto_load: bool = True) -> bool:
        """
        Launch xEdit with specified plugins
        
        Args:
            plugins: List of plugin files to load
            script_path: Optional path to xEdit script to run
            auto_load: Whether to automatically load plugins
            
        Returns:
            True if xEdit was launched successfully
        """
        if not self.xedit_path or not self.xedit_path.exists():
            logger.error("xEdit path not configured or not found")
            return False
        
        logger.info(f"Launching xEdit: {self.xedit_path}")
        
        # Build command line arguments
        cmd = [str(self.xedit_path)]
        
        if auto_load:
            cmd.append('-autoload')
        
        # Add specific plugins to load
        for plugin in plugins:
            cmd.extend(['-l', plugin])
        
        # Add script if provided
        if script_path and script_path.exists():
            cmd.extend(['-script', str(script_path)])
        
        # Set data path if configured
        if self.game_data_path:
            cmd.extend(['-D', str(self.game_data_path)])
        
        try:
            # Launch xEdit (non-blocking)
            logger.info(f"Executing: {' '.join(cmd)}")
            subprocess.Popen(cmd, cwd=self.xedit_path.parent)
            logger.info("xEdit launched successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to launch xEdit: {e}")
            return False
    
    def create_conflict_resolution_patch(self,
                                        conflicts: List[Dict[str, Any]],
                                        patch_name: str,
                                        output_dir: Path) -> Dict[str, Any]:
        """
        High-level method to create conflict resolution patch using xEdit
        
        Args:
            conflicts: List of conflicts to resolve
            patch_name: Name for the patch
            output_dir: Directory for output files
            
        Returns:
            Dictionary with results and paths
        """
        logger.info(f"Creating conflict resolution patch: {patch_name}")
        
        result = {
            'success': False,
            'patch_name': patch_name,
            'conflicts_exported': False,
            'script_generated': False,
            'xedit_launched': False,
            'export_path': None,
            'script_path': None
        }
        
        try:
            # Export conflicts
            export_path = output_dir / f"{patch_name}_conflicts.json"
            self.export_conflicts_for_xedit(conflicts, export_path)
            result['conflicts_exported'] = True
            result['export_path'] = str(export_path)
            
            # Generate xEdit script
            script_path = self.generate_xedit_script(conflicts, output_dir, patch_name)
            result['script_generated'] = True
            result['script_path'] = str(script_path)
            
            # Extract plugins from conflicts
            plugins = []
            for conflict in conflicts:
                plugins.extend(self._extract_plugins_from_conflict(conflict))
            plugins = list(set(plugins))  # Remove duplicates
            
            # Launch xEdit if path is configured
            if self.xedit_path and plugins:
                result['xedit_launched'] = self.launch_xedit(plugins, script_path)
            
            result['success'] = True
            logger.info("Conflict resolution patch creation initiated")
            
        except Exception as e:
            logger.error(f"Error creating conflict resolution patch: {e}")
            result['error'] = str(e)
        
        return result
    
    def get_configuration_help(self) -> str:
        """Get help text for configuring xEdit"""
        return """
xEdit Configuration Guide
========================

xEdit is a powerful tool for editing Bethesda game plugins. To use it with Mossy Manager:

1. Download xEdit for your game:
   - Skyrim Special Edition: SSEEdit
   - Skyrim: TES5Edit
   - Fallout 4: FO4Edit
   - Fallout 3: FO3Edit
   - Fallout New Vegas: FNVEdit
   
   Download from: https://www.nexusmods.com/

2. Extract xEdit to a known location, e.g.:
   C:/Modding/Tools/SSEEdit/
   
3. Configure Mossy Manager with xEdit path:
   mossy conflicts resolve-xedit --xedit-path "C:/Modding/Tools/SSEEdit/SSEEdit.exe"

4. Workflow:
   - Scan for conflicts with Mossy Manager
   - Export conflicts to xEdit format
   - Launch xEdit to create resolution patch
   - Review and save the patch in xEdit
   - Use the patch in your load order

Supported Games:
""" + "\n".join(f"  - {game}: {exe}" for game, exe in self.supported_games.items())
