#!/usr/bin/env node
/**
 * Mossy Manager CLI
 * 
 * Command-line interface for mod merging operations
 */

import { Command } from 'commander';
import * as path from 'path';
import * as fs from 'fs';
import chalk from 'chalk';
import inquirer from 'inquirer';
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

// Helper function to validate directory exists
function validateDirectory(directory: string): boolean {
  if (!fs.existsSync(directory)) {
    console.error(chalk.red(`✗ Error: Directory does not exist: ${directory}`));
    console.log(chalk.yellow('\nTip: Make sure the path is correct and try again.'));
    return false;
  }
  
  const stats = fs.statSync(directory);
  if (!stats.isDirectory()) {
    console.error(chalk.red(`✗ Error: Path is not a directory: ${directory}`));
    return false;
  }
  
  return true;
}

// Helper function to check write permissions
function checkWritePermissions(directory: string): boolean {
  try {
    fs.accessSync(directory, fs.constants.W_OK);
    return true;
  } catch (error) {
    console.error(chalk.red(`✗ Error: No write permission for directory: ${directory}`));
    console.log(chalk.yellow('\nTip: Check directory permissions or choose a different output location.'));
    return false;
  }
}

// Scan command
program
  .command('scan')
  .description('Scan a directory for mods')
  .argument('<directory>', 'Directory containing mods')
  .action(async (directory: string) => {
    console.log(chalk.cyan(`\n🔍 Scanning mods in: ${directory}\n`));
    
    // Validate directory
    if (!validateDirectory(directory)) {
      process.exit(1);
    }
    
    const parser = new ModParser();
    try {
      const mods = await parser.scanModDirectory(directory);
      
      if (mods.length === 0) {
        console.log(chalk.yellow('⚠ No mods found in directory'));
        console.log(chalk.dim('\nTip: Make sure the directory contains mod folders with BA2 archives.'));
        return;
      }
      
      console.log(chalk.green(`✓ Found ${mods.length} mod(s):\n`));
      
      mods.forEach((mod, index) => {
        console.log(chalk.bold(`${index + 1}. ${mod.name}`));
        console.log(chalk.dim(`   Path: ${mod.path}`));
        console.log(`   Archives: ${chalk.cyan(mod.archives.length.toString())}`);
        mod.archives.forEach(archive => {
          const typeColor = archive.type === 'DDS' ? chalk.magenta : chalk.blue;
          console.log(`     ${typeColor('•')} ${archive.fileName} (${typeColor(archive.type)}, ${formatBytes(archive.size)})`);
        });
        console.log(`   Plugins: ${chalk.cyan(mod.plugins.length.toString())}`);
        if (mod.plugins.length > 0) {
          mod.plugins.forEach(plugin => {
            console.log(`     ${chalk.yellow('•')} ${plugin}`);
          });
        }
        console.log('');
      });
    } catch (error) {
      console.error(chalk.red('✗ Error scanning directory:'), error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Check compatibility command
program
  .command('check')
  .description('Check merge compatibility for mods in a directory')
  .argument('<directory>', 'Directory containing mods')
  .option('--detailed', 'Show detailed conflict information')
  .action(async (directory: string, options: any) => {
    console.log(chalk.cyan(`\n🔍 Checking merge compatibility for mods in: ${directory}\n`));
    
    // Validate directory
    if (!validateDirectory(directory)) {
      process.exit(1);
    }
    
    const parser = new ModParser();
    const planner = new MergePlanner();
    const validator = new MergeValidator();
    
    try {
      const mods = await parser.scanModDirectory(directory);
      
      if (mods.length === 0) {
        console.log(chalk.yellow('⚠ No mods found in directory'));
        return;
      }
      
      console.log(chalk.green(`✓ Found ${mods.length} mod(s)\n`));
      
      if (mods.length < 2) {
        console.log(chalk.yellow('⚠ Need at least 2 mods to check compatibility'));
        console.log(chalk.dim('\nTip: Add more mods to the directory to enable merging.'));
        return;
      }

      // Show recommendations
      const recommendations = validator.getRecommendations(mods);
      if (recommendations.length > 0) {
        console.log(chalk.bold('📋 Recommendations:'));
        recommendations.forEach(rec => console.log(chalk.cyan(`  • ${rec}`)));
        console.log('');
      }

      const suggestions = planner.suggestMergeStrategy(mods);
      suggestions.forEach(s => {
        if (s.includes('✓') || s.includes('Found')) {
          console.log(chalk.green(s));
        } else if (s.includes('reduction')) {
          console.log(chalk.bold.cyan(s));
        } else {
          console.log(s);
        }
      });
      
      // Show warnings
      const groups = planner.planMergeGroups(mods);
      if (groups.length > 0) {
        console.log(chalk.yellow('\n⚠ Important:'));
        console.log(chalk.yellow('  • Always backup your mods before merging'));
        console.log(chalk.yellow('  • Test merged archives in-game'));
        console.log(chalk.yellow('  • Use --validate option when merging'));
      }
      
    } catch (error) {
      console.error(chalk.red('✗ Error checking compatibility:'), error instanceof Error ? error.message : error);
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
  .option('--dry-run', 'Preview merge without executing')
  .option('-y, --yes', 'Skip confirmation prompts')
  .action(async (directory: string, options: any) => {
    console.log(chalk.cyan(`\n🔄 Merging mods from: ${directory}`));
    console.log(chalk.dim(`Output directory: ${options.output}\n`));
    
    // Validate input directory
    if (!validateDirectory(directory)) {
      process.exit(1);
    }
    
    // Ensure output directory exists or can be created
    if (!fs.existsSync(options.output)) {
      try {
        fs.mkdirSync(options.output, { recursive: true });
        console.log(chalk.green(`✓ Created output directory: ${options.output}\n`));
      } catch (error) {
        console.error(chalk.red(`✗ Error: Cannot create output directory: ${options.output}`));
        process.exit(1);
      }
    } else {
      // Check write permissions
      if (!checkWritePermissions(options.output)) {
        process.exit(1);
      }
    }
    
    const parser = new ModParser();
    const planner = new MergePlanner();
    const executor = new MergeExecutor();
    
    try {
      // Scan mods
      console.log(chalk.cyan('📂 Scanning mods...'));
      const mods = await parser.scanModDirectory(directory);
      console.log(chalk.green(`✓ Found ${mods.length} mod(s)\n`));
      
      if (mods.length < 2) {
        console.log(chalk.yellow('⚠ Need at least 2 mods to merge'));
        console.log(chalk.dim('\nTip: Add more mods to the directory to enable merging.'));
        return;
      }

      // Plan merge groups
      console.log(chalk.cyan('📊 Planning merge groups...'));
      const groups = planner.planMergeGroups(mods);
      console.log(chalk.green(`✓ Planned ${groups.length} merge group(s)\n`));
      
      if (groups.length === 0) {
        console.log(chalk.yellow('⚠ No compatible merge groups found'));
        console.log(chalk.dim('\nPossible reasons:'));
        console.log(chalk.dim('  • Mods have conflicting files'));
        console.log(chalk.dim('  • Mods have conflicting plugins'));
        console.log(chalk.dim('  • Less than 2 compatible mods available'));
        console.log(chalk.dim('\nTip: Run "check" command to see compatibility details.'));
        return;
      }

      // Show planned merges with details
      console.log(chalk.bold('📋 Merge Plan:\n'));
      groups.forEach((group, index) => {
        console.log(chalk.bold.cyan(`Group ${index + 1}: ${group.name}`));
        console.log(chalk.dim(`  Output: ${group.outputFileName}`));
        console.log(chalk.dim(`  Size: ${formatBytes(group.estimatedSize)}`));
        console.log(`  Mods (${group.mods.length}):`);
        group.mods.forEach(mod => {
          console.log(chalk.green(`    • ${mod.name}`));
        });
        console.log('');
      });

      // Calculate statistics
      const totalMods = groups.reduce((sum, g) => sum + g.mods.length, 0);
      const reduction = ((totalMods - groups.length) / totalMods * 100).toFixed(1);
      console.log(chalk.bold(`📊 Impact: ${totalMods} archives → ${groups.length} merged archives (${reduction}% reduction)\n`));

      // Dry run mode
      if (options.dryRun) {
        console.log(chalk.yellow('🔍 DRY RUN MODE - No changes will be made\n'));
        console.log(chalk.green('✓ Merge plan complete. Run without --dry-run to execute.'));
        return;
      }

      // Interactive confirmation (unless -y flag is used)
      if (!options.yes) {
        console.log(chalk.yellow('⚠ Warning: This will create merged archives'));
        if (options.backup !== false) {
          console.log(chalk.dim('  Backups will be created for safety'));
        } else {
          console.log(chalk.red('  ⚠ Backups are DISABLED (--no-backup)'));
        }
        console.log('');
        
        const answer = await inquirer.prompt([{
          type: 'confirm',
          name: 'proceed',
          message: 'Do you want to proceed with the merge?',
          default: false
        }]);
        
        if (!answer.proceed) {
          console.log(chalk.yellow('\n✗ Merge cancelled by user'));
          return;
        }
        console.log('');
      }

      console.log(chalk.cyan('🔄 Executing merges...\n'));

      // Execute merges
      const mergeOptions: MergeOptions = {
        outputDirectory: options.output,
        createBackup: options.backup !== false,
        overwriteExisting: options.overwrite || false,
        validateAfterMerge: options.validate || false
      };

      const results = await executor.executeMerges(groups, mergeOptions);

      // Summary with colors
      const successful = results.filter(r => r.success).length;
      const failed = results.filter(r => !r.success).length;

      console.log(chalk.bold('\n═══ Merge Summary ═══\n'));
      console.log(chalk.green(`✓ Successful: ${successful}`));
      if (failed > 0) {
        console.log(chalk.red(`✗ Failed: ${failed}`));
      } else {
        console.log(chalk.dim(`  Failed: ${failed}`));
      }

      if (failed > 0) {
        console.log(chalk.red('\n✗ Failed merges:'));
        results.filter(r => !r.success).forEach(r => {
          console.log(chalk.red(`  • ${r.outputPath}`));
          r.errors.forEach(e => console.log(chalk.dim(`    Error: ${e}`)));
        });
      }

      if (successful > 0) {
        console.log(chalk.green('\n✓ Merge completed successfully!'));
        console.log(chalk.dim(`\nMerged archives saved to: ${options.output}`));
        console.log(chalk.yellow('\n⚠ Important: Test the merged archives in-game before removing originals!'));
      }

    } catch (error) {
      console.error(chalk.red('\n✗ Error during merge:'), error instanceof Error ? error.message : error);
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
