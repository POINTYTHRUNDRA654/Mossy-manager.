/**
 * MergeValidator
 * 
 * Validates whether mods can be safely merged together
 */

import { ModInfo, MergeCompatibility } from '../types';
import { ConflictDetector } from './ConflictDetector';

export class MergeValidator {
  private conflictDetector: ConflictDetector;

  constructor() {
    this.conflictDetector = new ConflictDetector();
  }

  /**
   * Check if two mods can be merged
   */
  canMergeMods(mod1: ModInfo, mod2: ModInfo): MergeCompatibility {
    const reasons: string[] = [];
    const warnings: string[] = [];
    const conflictingFiles: string[] = [];

    // Check for file conflicts
    const fileConflicts = this.conflictDetector.detectFileConflicts(mod1, mod2);
    if (fileConflicts.length > 0) {
      conflictingFiles.push(...fileConflicts);
      const severity = this.conflictDetector.analyzeConflictSeverity(fileConflicts);
      
      if (severity === 'high') {
        reasons.push(`High number of file conflicts (${fileConflicts.length} files)`);
      } else if (severity === 'medium') {
        warnings.push(`Medium number of file conflicts (${fileConflicts.length} files)`);
      } else {
        warnings.push(`Low number of file conflicts (${fileConflicts.length} files)`);
      }
    }

    // Check for plugin conflicts
    const pluginConflicts = this.conflictDetector.detectPluginConflicts(mod1, mod2);
    if (pluginConflicts.length > 0) {
      reasons.push(`Plugin conflicts: ${pluginConflicts.join(', ')}`);
    }

    // Check if mods have archives
    if (mod1.archives.length === 0 && mod2.archives.length === 0) {
      reasons.push('Neither mod has BA2 archives to merge');
    }

    // Check archive compatibility
    if (this.hasIncompatibleArchives(mod1, mod2)) {
      warnings.push('Mods have different archive types (mixing GENERAL and DDS)');
    }

    // Determine if merge is possible
    const canMerge = reasons.length === 0;

    return {
      canMerge,
      reasons,
      warnings,
      conflictingFiles
    };
  }

  /**
   * Validate a group of mods for merging
   */
  validateMergeGroup(mods: ModInfo[]): MergeCompatibility {
    if (mods.length < 2) {
      return {
        canMerge: false,
        reasons: ['Need at least 2 mods to merge'],
        warnings: [],
        conflictingFiles: []
      };
    }

    const allReasons: string[] = [];
    const allWarnings: string[] = [];
    const allConflicts: Set<string> = new Set();

    // Check each pair of mods
    for (let i = 0; i < mods.length; i++) {
      for (let j = i + 1; j < mods.length; j++) {
        const result = this.canMergeMods(mods[i], mods[j]);
        allReasons.push(...result.reasons);
        allWarnings.push(...result.warnings);
        result.conflictingFiles.forEach(f => allConflicts.add(f));
      }
    }

    return {
      canMerge: allReasons.length === 0,
      reasons: [...new Set(allReasons)], // Remove duplicates
      warnings: [...new Set(allWarnings)],
      conflictingFiles: Array.from(allConflicts)
    };
  }

  /**
   * Check if mods have incompatible archives
   */
  private hasIncompatibleArchives(mod1: ModInfo, mod2: ModInfo): boolean {
    return this.conflictDetector.hasArchiveTypeConflict(mod1, mod2);
  }

  /**
   * Generate merge recommendations
   */
  getRecommendations(mods: ModInfo[]): string[] {
    const recommendations: string[] = [];

    // Recommend grouping by type
    const textureOnlyMods = mods.filter(m => 
      m.archives.every(a => a.type === 'DDS')
    );
    const meshOnlyMods = mods.filter(m => 
      m.archives.every(a => a.type === 'GENERAL')
    );

    if (textureOnlyMods.length >= 2) {
      recommendations.push(`Found ${textureOnlyMods.length} texture-only mods that could be merged together`);
    }

    if (meshOnlyMods.length >= 2) {
      recommendations.push(`Found ${meshOnlyMods.length} mesh/general mods that could be merged together`);
    }

    return recommendations;
  }
}
