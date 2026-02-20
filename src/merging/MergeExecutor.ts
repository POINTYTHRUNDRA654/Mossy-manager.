/**
 * MergeExecutor
 * 
 * Executes the actual merging of mod archives
 */

import * as fs from 'fs';
import * as path from 'path';
import { MergeGroup, MergeOptions, MergeResult } from '../types';
import { BA2Handler } from '../core/BA2Handler';

export class MergeExecutor {
  private ba2Handler: BA2Handler;

  constructor() {
    this.ba2Handler = new BA2Handler();
  }

  /**
   * Execute a merge operation
   */
  async executeMerge(
    group: MergeGroup,
    options: MergeOptions
  ): Promise<MergeResult> {
    const errors: string[] = [];
    const includeLoose = options.includeLooseFiles !== false;
    const allowOverwrite = options.allowFileOverwrite === true;
    const tempRoot = fs.mkdtempSync(path.join(process.cwd(), 'mossy-merge-loose-'));
    const looseCombined = path.join(tempRoot, 'loose');
    fs.mkdirSync(looseCombined, { recursive: true });

    try {
      // Validate output directory
      if (!fs.existsSync(options.outputDirectory)) {
        fs.mkdirSync(options.outputDirectory, { recursive: true });
      }

      const outputPath = path.join(options.outputDirectory, group.outputFileName);

      // Check if output file exists
      if (fs.existsSync(outputPath) && !options.overwriteExisting) {
        errors.push(`Output file already exists: ${outputPath}`);
        return {
          success: false,
          outputPath,
          mergedMods: [],
          fileCount: 0,
          errors
        };
      }

      // Create backup if requested
      if (options.createBackup && fs.existsSync(outputPath)) {
        const backupPath = `${outputPath}.backup`;
        fs.copyFileSync(outputPath, backupPath);
      }

      // Collect all archives from the group
      const allArchives = group.mods.flatMap(mod => mod.archives);

      // Optionally gather loose files (non-BA2) with collision checks
      if (includeLoose) {
        for (const mod of group.mods) {
          this.copyLooseFiles(mod.path, looseCombined, allowOverwrite);
        }
      }
      
      if (allArchives.length === 0) {
        errors.push('No archives to merge');
        return {
          success: false,
          outputPath,
          mergedMods: [],
          fileCount: 0,
          errors
        };
      }

      // Determine archive type (all should be same type)
      const archiveType = allArchives[0].type;

      // Perform the merge (packs BA2s and incorporates loose files)
      const mergeSuccess = await this.ba2Handler.mergeArchives(
        allArchives,
        outputPath,
        archiveType,
        {
          extraFilesDir: includeLoose ? looseCombined : undefined,
          allowOverwrite
        }
      );

      if (!mergeSuccess) {
        errors.push('Merge operation failed');
        return {
          success: false,
          outputPath,
          mergedMods: [],
          fileCount: 0,
          errors
        };
      }

      // Validate after merge if requested
      if (options.validateAfterMerge) {
        const valid = this.ba2Handler.isValidBA2(outputPath);
        if (!valid) {
          errors.push('Merged archive failed validation');
          return {
            success: false,
            outputPath,
            mergedMods: group.mods.map(m => m.name),
            fileCount: 0,
            errors
          };
        }
      }

      // Calculate total file count
      const totalFiles = allArchives.reduce((sum, archive) => sum + archive.files.length, 0);

      return {
        success: true,
        outputPath,
        mergedMods: group.mods.map(m => m.name),
        fileCount: totalFiles,
        errors: []
      };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors.push(`Unexpected error: ${message}`);
      return {
        success: false,
        outputPath: '',
        mergedMods: [],
        fileCount: 0,
        errors
      };
    } finally {
      try {
        fs.rmSync(tempRoot, { recursive: true, force: true });
      } catch {
        // ignore cleanup
      }
    }
  }

  /**
   * Copy non-BA2 loose files into targetDir with collision checks.
   */
  private copyLooseFiles(sourceModDir: string, targetDir: string, allowOverwrite: boolean): void {
    const entries = fs.readdirSync(sourceModDir, { withFileTypes: true });
    for (const entry of entries) {
      const srcPath = path.join(sourceModDir, entry.name);
      const destPath = path.join(targetDir, entry.name);

      // Skip BA2 archives (handled separately)
      if (!entry.isDirectory() && entry.name.toLowerCase().endsWith('.ba2')) {
        continue;
      }

      if (entry.isDirectory()) {
        if (!fs.existsSync(destPath)) {
          fs.mkdirSync(destPath, { recursive: true });
        }
        this.copyLooseFiles(srcPath, destPath, allowOverwrite);
      } else {
        if (fs.existsSync(destPath) && !allowOverwrite) {
          throw new Error(`Conflict while merging loose files. Duplicate file: ${destPath}`);
        }
        fs.copyFileSync(srcPath, destPath);
      }
    }
  }

  /**
   * Execute multiple merge operations
   */
  async executeMerges(
    groups: MergeGroup[],
    options: MergeOptions
  ): Promise<MergeResult[]> {
    const results: MergeResult[] = [];

    for (const group of groups) {
      console.log(`Merging ${group.name}...`);
      const result = await this.executeMerge(group, options);
      results.push(result);

      if (result.success) {
        console.log(`✓ Successfully merged ${result.mergedMods.length} mods`);
      } else {
        console.error(`✗ Merge failed: ${result.errors.join(', ')}`);
      }
    }

    return results;
  }
}
