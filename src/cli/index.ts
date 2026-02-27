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
import { ConfigManager } from '../utils/ConfigManager';
import { ModManagerDetector } from '../utils/ModManagerDetector';

const program = new Command();
const config = new ConfigManager();

program
  .name('mossy-manager')
  .description('Mossy Manager - Advanced mod merging tool for Bethesda games')
  .version('1.0.0');

// Helper function to get color for archive type
function getArchiveTypeColor(type: string): typeof chalk.blue {
  const colorMap: Record<string, typeof chalk.blue> = {
    'DDS': chalk.magenta,
    'GENERAL': chalk.blue
  };
  return colorMap[type] || chalk.blue;
}

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
          const typeColor = getArchiveTypeColor(archive.type);
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
  .option('--no-backup', 'Skip creating backups of existing merged archives')
  .option('--no-backup-sources', 'Skip copying source BA2 files before merging')
  .option('--overwrite', 'Overwrite existing merged archives')
  .option('--validate', 'Validate merged archives')
  .option('--no-loose', 'Skip merging loose (non-BA2) files')
  .option('--allow-overwrite', 'Allow file overwrites when combining content')
  .option('--report <file>', 'Write a JSON merge report to the given path')
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
      if (totalMods > 0) {
        const reduction = ((totalMods - groups.length) / totalMods * 100).toFixed(1);
        console.log(chalk.bold(`📊 Impact: ${totalMods} archives → ${groups.length} merged archives (${reduction}% reduction)\n`));
      }

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
        backupSources: options.backupSources !== false,
        overwriteExisting: options.overwrite || false,
        validateAfterMerge: options.validate || false,
        includeLooseFiles: options.loose !== false,
        allowFileOverwrite: options.allowOverwrite || false
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
        
        // Save to config for next time
        config.updateLastDirectory(directory);
      }

      // Optional report
      if (options.report) {
        const report = {
          generatedAt: new Date().toISOString(),
          sourceDirectory: directory,
          outputDirectory: options.output,
          options: {
            includeLooseFiles: mergeOptions.includeLooseFiles !== false,
            allowFileOverwrite: mergeOptions.allowFileOverwrite || false,
            validateAfterMerge: mergeOptions.validateAfterMerge || false,
            overwriteExisting: mergeOptions.overwriteExisting || false,
            createBackup: mergeOptions.createBackup !== false
          },
          groups: groups.map(g => ({
            name: g.name,
            mods: g.mods.map(m => m.name),
            output: path.join(options.output, g.outputFileName),
            estimatedSize: g.estimatedSize
          })),
          results
        };

        try {
          fs.writeFileSync(options.report, JSON.stringify(report, null, 2));
          console.log(chalk.green(`\n✓ Report written to: ${options.report}`));
        } catch (err) {
          console.log(chalk.red(`\n✗ Failed to write report: ${err instanceof Error ? err.message : String(err)}`));
        }
      }

    } catch (error) {
      console.error(chalk.red('\n✗ Error during merge:'), error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

// Detect command - Find installed mod managers
program
  .command('detect')
  .description('Detect installed mod managers and suggest directories')
  .action(async () => {
    console.log(chalk.cyan('\n🔍 Detecting installed mod managers...\n'));
    
    const detector = new ModManagerDetector();
    const managers = detector.detectAll();
    
    if (managers.length === 0) {
      console.log(chalk.yellow('⚠ No mod managers detected'));
      console.log(chalk.dim('\nSupported mod managers:'));
      console.log(chalk.dim('  • Mod Organizer 2 (MO2)'));
      console.log(chalk.dim('  • Vortex'));
      
      // Show common game directories
      const gameDirs = detector.getCommonGameDirectories();
      if (gameDirs.length > 0) {
        console.log(chalk.cyan('\n📁 Detected game installations:'));
        gameDirs.forEach(dir => {
          console.log(chalk.green(`  • ${dir}`));
        });
      }
      return;
    }
    
    console.log(chalk.green(`✓ Found ${managers.length} mod manager(s):\n`));
    
    managers.forEach((manager, index) => {
      console.log(chalk.bold(`${index + 1}. ${manager.name}`));
      console.log(chalk.dim(`   Installation: ${manager.path}`));
      console.log(chalk.cyan(`   Mods Directory: ${manager.modsDirectory}`));
      
      // Check if mods directory has content
      try {
        const modDirs = fs.readdirSync(manager.modsDirectory, { withFileTypes: true })
          .filter(dirent => dirent.isDirectory())
          .length;
        console.log(chalk.green(`   ✓ ${modDirs} mod folder(s) found`));
      } catch (error) {
        console.log(chalk.yellow('   ⚠ Cannot read mods directory'));
      }
      console.log('');
    });
    
    console.log(chalk.bold('💡 Quick start:'));
    if (managers.length > 0) {
      const firstManager = managers[0];
      console.log(chalk.cyan(`\n  Scan mods:`));
      console.log(chalk.dim(`  $ mossy-manager scan "${firstManager.modsDirectory}"`));
      console.log(chalk.cyan(`\n  Check compatibility:`));
      console.log(chalk.dim(`  $ mossy-manager check "${firstManager.modsDirectory}"`));
      console.log(chalk.cyan(`\n  Merge mods:`));
      console.log(chalk.dim(`  $ mossy-manager merge "${firstManager.modsDirectory}" --dry-run`));
    }
  });

// Config command - Manage configuration
program
  .command('config')
  .description('View or update configuration')
  .option('--show', 'Show current configuration')
  .option('--set-output <path>', 'Set default output directory')
  .option('--enable-backup', 'Enable backups by default')
  .option('--disable-backup', 'Disable backups by default')
  .action(async (options: any) => {
    if (options.show || (!options.setOutput && !options.enableBackup && !options.disableBackup)) {
      console.log(chalk.cyan('\n⚙️ Current Configuration:\n'));
      const currentConfig = config.getAll();
      
      if (Object.keys(currentConfig).length === 0) {
        console.log(chalk.dim('  No configuration set (using defaults)'));
      } else {
        Object.entries(currentConfig).forEach(([key, value]) => {
          console.log(`  ${chalk.bold(key)}: ${chalk.green(String(value))}`);
        });
      }
      console.log('');
      return;
    }
    
    if (options.setOutput) {
      config.set('defaultOutputDir', options.setOutput);
      console.log(chalk.green(`✓ Default output directory set to: ${options.setOutput}`));
    }
    
    if (options.enableBackup) {
      config.set('defaultBackup', true);
      console.log(chalk.green('✓ Backups enabled by default'));
    }
    
    if (options.disableBackup) {
      config.set('defaultBackup', false);
      console.log(chalk.yellow('⚠ Backups disabled by default'));
    }
    
    config.saveConfig();
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
