#!/usr/bin/env node
/**
 * Mossy Manager CLI
 * 
 * Command-line interface for mod merging operations
 */

import { Command } from 'commander';
import * as path from 'path';
import { ModParser } from '../core/ModParser';
import { MergeValidator } from '../merging/MergeValidator';
import { MergePlanner } from '../merging/MergePlanner';
import { MergeExecutor } from '../merging/MergeExecutor';
import { MergeOptions } from '../types';

const program = new Command();

program
  .name('mossy-manager')
  .description('Mossy Manager - Advanced mod merging tool for Bethesda games')
  .version('1.0.0');

// Scan command
program
  .command('scan')
  .description('Scan a directory for mods')
  .argument('<directory>', 'Directory containing mods')
  .action(async (directory: string) => {
    console.log(`Scanning mods in: ${directory}`);
    
    const parser = new ModParser();
    try {
      const mods = await parser.scanModDirectory(directory);
      console.log(`\nFound ${mods.length} mod(s):`);
      
      mods.forEach((mod, index) => {
        console.log(`\n${index + 1}. ${mod.name}`);
        console.log(`   Path: ${mod.path}`);
        console.log(`   Archives: ${mod.archives.length}`);
        mod.archives.forEach(archive => {
          console.log(`     - ${archive.fileName} (${archive.type}, ${formatBytes(archive.size)})`);
        });
        console.log(`   Plugins: ${mod.plugins.length}`);
        if (mod.plugins.length > 0) {
          mod.plugins.forEach(plugin => {
            console.log(`     - ${plugin}`);
          });
        }
      });
    } catch (error) {
      console.error('Error scanning directory:', error);
      process.exit(1);
    }
  });

// Check compatibility command
program
  .command('check')
  .description('Check merge compatibility for mods in a directory')
  .argument('<directory>', 'Directory containing mods')
  .action(async (directory: string) => {
    console.log(`Checking merge compatibility for mods in: ${directory}`);
    
    const parser = new ModParser();
    const planner = new MergePlanner();
    
    try {
      const mods = await parser.scanModDirectory(directory);
      console.log(`Found ${mods.length} mod(s)\n`);
      
      if (mods.length < 2) {
        console.log('Need at least 2 mods to check compatibility');
        return;
      }

      const suggestions = planner.suggestMergeStrategy(mods);
      suggestions.forEach(s => console.log(s));
      
    } catch (error) {
      console.error('Error checking compatibility:', error);
      process.exit(1);
    }
  });

// Merge command
program
  .command('merge')
  .description('Merge compatible mods')
  .argument('<directory>', 'Directory containing mods')
  .option('-o, --output <path>', 'Output directory for merged archives', './merged')
  .option('--no-backup', 'Skip creating backups')
  .option('--overwrite', 'Overwrite existing merged archives')
  .option('--validate', 'Validate merged archives')
  .action(async (directory: string, options: any) => {
    console.log(`Merging mods from: ${directory}`);
    console.log(`Output directory: ${options.output}\n`);
    
    const parser = new ModParser();
    const planner = new MergePlanner();
    const executor = new MergeExecutor();
    
    try {
      // Scan mods
      const mods = await parser.scanModDirectory(directory);
      console.log(`Found ${mods.length} mod(s)`);
      
      if (mods.length < 2) {
        console.log('Need at least 2 mods to merge');
        return;
      }

      // Plan merge groups
      const groups = planner.planMergeGroups(mods);
      console.log(`Planned ${groups.length} merge group(s)\n`);
      
      if (groups.length === 0) {
        console.log('No compatible merge groups found');
        return;
      }

      // Show planned merges
      groups.forEach((group, index) => {
        console.log(`Group ${index + 1}: ${group.name}`);
        console.log(`  Output: ${group.outputFileName}`);
        console.log(`  Mods: ${group.mods.map(m => m.name).join(', ')}`);
      });

      console.log('\nExecuting merges...\n');

      // Execute merges
      const mergeOptions: MergeOptions = {
        outputDirectory: options.output,
        createBackup: options.backup !== false,
        overwriteExisting: options.overwrite || false,
        validateAfterMerge: options.validate || false
      };

      const results = await executor.executeMerges(groups, mergeOptions);

      // Summary
      const successful = results.filter(r => r.success).length;
      const failed = results.filter(r => !r.success).length;

      console.log(`\n=== Summary ===`);
      console.log(`Successful: ${successful}`);
      console.log(`Failed: ${failed}`);

      if (failed > 0) {
        console.log('\nFailed merges:');
        results.filter(r => !r.success).forEach(r => {
          console.log(`  - ${r.outputPath}`);
          r.errors.forEach(e => console.log(`    Error: ${e}`));
        });
      }

    } catch (error) {
      console.error('Error during merge:', error);
      process.exit(1);
    }
  });

// Helper function
function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

program.parse();
