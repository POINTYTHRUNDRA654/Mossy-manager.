/**
 * MergePlanner
 * 
 * Plans optimal merge groups for mods based on compatibility analysis
 */

import { ModInfo, MergeGroup, BA2Type } from '../types';
import { MergeValidator } from './MergeValidator';

export class MergePlanner {
  private validator: MergeValidator;

  constructor() {
    this.validator = new MergeValidator();
  }

  /**
   * Create merge groups from a list of mods
   * Groups mods by compatibility and type
   */
  planMergeGroups(mods: ModInfo[]): MergeGroup[] {
    const groups: MergeGroup[] = [];

    // Separate mods by archive type
    const textureOnlyMods = this.filterByArchiveType(mods, BA2Type.DDS);
    const generalOnlyMods = this.filterByArchiveType(mods, BA2Type.GENERAL);
    const mixedMods = mods.filter(m => !this.isSingleArchiveType(m));

    // Create groups for texture-only mods
    if (textureOnlyMods.length >= 2) {
      const textureGroups = this.createCompatibleGroups(textureOnlyMods, 'Textures');
      groups.push(...textureGroups);
    }

    // Create groups for general-only mods
    if (generalOnlyMods.length >= 2) {
      const generalGroups = this.createCompatibleGroups(generalOnlyMods, 'General');
      groups.push(...generalGroups);
    }

    // Handle mixed mods separately (more complex)
    if (mixedMods.length >= 2) {
      const mixedGroups = this.createCompatibleGroups(mixedMods, 'Mixed');
      groups.push(...mixedGroups);
    }

    return groups;
  }

  /**
   * Create compatible merge groups from a list of mods
   */
  private createCompatibleGroups(mods: ModInfo[], category: string): MergeGroup[] {
    const groups: MergeGroup[] = [];
    const used = new Set<string>();

    // Greedy algorithm: try to create largest compatible groups
    for (let i = 0; i < mods.length; i++) {
      if (used.has(mods[i].name)) continue;

      const group: ModInfo[] = [mods[i]];
      used.add(mods[i].name);

      // Try to add compatible mods to this group
      for (let j = i + 1; j < mods.length; j++) {
        if (used.has(mods[j].name)) continue;

        // Check if this mod is compatible with all mods in group
        const compatible = group.every(existingMod => {
          const result = this.validator.canMergeMods(existingMod, mods[j]);
          return result.canMerge || result.warnings.length <= 1;
        });

        if (compatible) {
          group.push(mods[j]);
          used.add(mods[j].name);
        }
      }

      // Only create group if we have at least 2 mods
      if (group.length >= 2) {
        groups.push(this.createMergeGroup(group, category));
      }
    }

    return groups;
  }

  /**
   * Create a merge group object
   */
  private createMergeGroup(mods: ModInfo[], category: string): MergeGroup {
    const modNames = mods.map(m => m.name).join('_');
    const id = `merge_${category}_${Date.now()}`;
    const outputFileName = `MossyMerge_${category}_${mods.length}mods.ba2`;
    
    // Calculate estimated size
    const estimatedSize = mods.reduce((sum, mod) => {
      return sum + mod.archives.reduce((archiveSum, archive) => archiveSum + archive.size, 0);
    }, 0);

    return {
      id,
      name: `${category} Merge (${mods.length} mods)`,
      mods,
      outputFileName,
      estimatedSize
    };
  }

  /**
   * Filter mods that only have one type of archive
   */
  private filterByArchiveType(mods: ModInfo[], type: BA2Type): ModInfo[] {
    return mods.filter(mod => {
      if (mod.archives.length === 0) return false;
      return mod.archives.every(archive => archive.type === type);
    });
  }

  /**
   * Check if mod has only one type of archive
   */
  private isSingleArchiveType(mod: ModInfo): boolean {
    if (mod.archives.length === 0) return false;
    const firstType = mod.archives[0].type;
    return mod.archives.every(archive => archive.type === firstType);
  }

  /**
   * Suggest optimal merge strategy
   */
  suggestMergeStrategy(mods: ModInfo[]): string[] {
    const suggestions: string[] = [];
    
    const groups = this.planMergeGroups(mods);
    
    if (groups.length === 0) {
      suggestions.push('No compatible merge groups found.');
      suggestions.push('This could be because:');
      suggestions.push('- Mods have conflicting files');
      suggestions.push('- Mods have conflicting plugins');
      suggestions.push('- Less than 2 compatible mods available');
    } else {
      suggestions.push(`Found ${groups.length} merge group(s):`);
      groups.forEach((group, index) => {
        suggestions.push(`  ${index + 1}. ${group.name} - ${group.mods.length} mods`);
        suggestions.push(`     Output: ${group.outputFileName}`);
        suggestions.push(`     Estimated size: ${this.formatBytes(group.estimatedSize)}`);
      });
      
      const totalMods = groups.reduce((sum, g) => sum + g.mods.length, 0);
      const reductionPct = ((totalMods - groups.length) / totalMods * 100).toFixed(1);
      suggestions.push(`\nMerging would reduce ${totalMods} archives to ${groups.length} (${reductionPct}% reduction)`);
    }

    return suggestions;
  }

  /**
   * Format bytes to human-readable string
   */
  private formatBytes(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
}
