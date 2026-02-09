/**
 * Mod Manager Detector
 * 
 * Auto-detects installed mod managers and their mod directories
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface ModManagerInfo {
  name: string;
  path: string;
  modsDirectory: string;
}

export class ModManagerDetector {
  /**
   * Detect all installed mod managers
   */
  detectAll(): ModManagerInfo[] {
    const managers: ModManagerInfo[] = [];
    
    const mo2 = this.detectMO2();
    if (mo2) managers.push(mo2);
    
    const vortex = this.detectVortex();
    if (vortex) managers.push(vortex);
    
    return managers;
  }

  /**
   * Detect Mod Organizer 2 installation
   * Supports Windows and Linux (via Wine/Proton)
   * Note: macOS is not officially supported by Mod Organizer 2
   */
  detectMO2(): ModManagerInfo | null {
    const platform = os.platform();
    const possiblePaths: string[] = [];
    
    if (platform === 'win32') {
      // Common Windows installation paths
      const drives = ['C:', 'D:', 'E:'];
      const basePaths = [
        'Program Files/Mod Organizer 2',
        'Program Files (x86)/Mod Organizer 2',
        'Games/Mod Organizer 2',
        'Modding/MO2',
        'Steam/steamapps/common/Mod Organizer 2'
      ];
      
      drives.forEach(drive => {
        basePaths.forEach(basePath => {
          possiblePaths.push(path.join(drive, basePath));
        });
      });
    } else if (platform === 'linux') {
      // Linux paths (often through Wine/Proton)
      const home = os.homedir();
      possiblePaths.push(
        path.join(home, '.wine/drive_c/Program Files/Mod Organizer 2'),
        path.join(home, '.wine/drive_c/Program Files (x86)/Mod Organizer 2'),
        path.join(home, '.local/share/Steam/steamapps/compatdata/*/pfx/drive_c/Program Files/Mod Organizer 2')
      );
    } else {
      // macOS and other platforms not supported
      return null;
    }
    
    // Check each possible path
    for (const moPath of possiblePaths) {
      if (fs.existsSync(moPath)) {
        const modsDir = path.join(moPath, 'mods');
        if (fs.existsSync(modsDir)) {
          return {
            name: 'Mod Organizer 2',
            path: moPath,
            modsDirectory: modsDir
          };
        }
      }
    }
    
    return null;
  }

  /**
   * Detect Vortex installation
   */
  detectVortex(): ModManagerInfo | null {
    const platform = os.platform();
    const appData = platform === 'win32' 
      ? process.env.APPDATA || path.join(os.homedir(), 'AppData/Roaming')
      : path.join(os.homedir(), '.config');
    
    const vortexPath = path.join(appData, 'Vortex');
    
    if (fs.existsSync(vortexPath)) {
      // Vortex stores mods in a configurable location
      // Check common locations
      const possibleModDirs = [
        path.join(vortexPath, 'mods'),
        path.join(os.homedir(), 'Games/Vortex Mods')
      ];
      
      for (const modDir of possibleModDirs) {
        if (fs.existsSync(modDir)) {
          return {
            name: 'Vortex',
            path: vortexPath,
            modsDirectory: modDir
          };
        }
      }
    }
    
    return null;
  }

  /**
   * Get common game mod directories
   */
  getCommonGameDirectories(): string[] {
    const platform = os.platform();
    const dirs: string[] = [];
    
    if (platform === 'win32') {
      const drives = ['C:', 'D:', 'E:'];
      const games = [
        'Steam/steamapps/common/Fallout 4/Data',
        'Steam/steamapps/common/Skyrim Special Edition/Data',
        'Steam/steamapps/common/Fallout 76/Data',
        'Games/Fallout 4/Data',
        'Games/Skyrim Special Edition/Data'
      ];
      
      drives.forEach(drive => {
        games.forEach(game => {
          dirs.push(path.join(drive, game));
        });
      });
    }
    
    return dirs.filter(dir => fs.existsSync(dir));
  }
}
