/**
 * ConflictDetector
 * 
 * Detects conflicts between mods that would prevent safe merging
 */

import { ModInfo, BA2Archive } from '../types';

export class ConflictDetector {
  /**
   * Detect file conflicts between two mods
   */
  detectFileConflicts(mod1: ModInfo, mod2: ModInfo): string[] {
    const conflicts: string[] = [];
    
    // Get all file paths from both mods
    const mod1Files = this.getAllFilePaths(mod1);
    const mod2Files = this.getAllFilePaths(mod2);
    
    // Find duplicates
    for (const file of mod1Files) {
      if (mod2Files.has(file)) {
        conflicts.push(file);
      }
    }
    
    return conflicts;
  }

  /**
   * Detect plugin conflicts
   */
  detectPluginConflicts(mod1: ModInfo, mod2: ModInfo): string[] {
    const conflicts: string[] = [];
    
    for (const plugin of mod1.plugins) {
      if (mod2.plugins.includes(plugin)) {
        conflicts.push(plugin);
      }
    }
    
    return conflicts;
  }

  /**
   * Check if mods have conflicting archive types
   */
  hasArchiveTypeConflict(mod1: ModInfo, mod2: ModInfo): boolean {
    const mod1Types = new Set(mod1.archives.map(a => a.type));
    const mod2Types = new Set(mod2.archives.map(a => a.type));
    
    // If one has only GENERAL and other has only DDS, they can coexist
    // But if both have mixed types, it's more complex
    return false; // Simplified - actual logic would be more nuanced
  }

  /**
   * Get all file paths from a mod
   */
  private getAllFilePaths(mod: ModInfo): Set<string> {
    const paths = new Set<string>();
    
    for (const archive of mod.archives) {
      for (const file of archive.files) {
        paths.add(file.path.toLowerCase());
      }
    }
    
    return paths;
  }

  /**
   * Analyze overall conflict severity
   */
  analyzeConflictSeverity(conflicts: string[]): 'none' | 'low' | 'medium' | 'high' {
    if (conflicts.length === 0) {
      return 'none';
    }
    
    if (conflicts.length < 5) {
      return 'low';
    }
    
    if (conflicts.length < 20) {
      return 'medium';
    }
    
    return 'high';
  }
}
