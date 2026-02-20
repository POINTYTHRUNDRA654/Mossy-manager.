/**
 * BA2Archive Handler
 * 
 * Handles reading and writing BA2 archive files used by Bethesda games.
 * BA2 files are the archive format for Fallout 4, Skyrim SE, and Fallout 76.
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { spawn } from 'child_process';
import { BA2Archive, BA2Type, BA2FileEntry } from '../types';

export class BA2Handler {
  constructor(private bsarchPath?: string) {}

  /**
   * Resolve bsarch executable path.
   */
  private resolveBsarchPath(): string {
    if (this.bsarchPath) return this.bsarchPath;
    const fromEnv = process.env.BSARCH_PATH;
    if (fromEnv && fromEnv.trim().length > 0) {
      return fromEnv.trim();
    }
    return 'bsarch';
  }

  private runBsarch(args: string[], cwd?: string): Promise<{ stdout: string; stderr: string }> {
    const cmd = this.resolveBsarchPath();

    return new Promise((resolve, reject) => {
      const child = spawn(cmd, args, { cwd, windowsHide: true });
      let stdout = '';
      let stderr = '';

      child.stdout.on('data', data => {
        stdout += data.toString();
      });

      child.stderr.on('data', data => {
        stderr += data.toString();
      });

      child.on('error', err => {
        const enoentHint = (err as NodeJS.ErrnoException).code === 'ENOENT'
          ? ' (bsarch not found; set BSARCH_PATH to bsarch.exe or put it on PATH)'
          : '';
        reject(new Error(`Failed to start bsarch: ${err.message}${enoentHint}`));
      });

      child.on('close', code => {
        if (code !== 0) {
          reject(new Error(`bsarch exited with code ${code}: ${stderr || stdout}`));
        } else {
          resolve({ stdout, stderr });
        }
      });
    });
  }

  private async listArchiveFiles(filePath: string): Promise<BA2FileEntry[]> {
    const { stdout } = await this.runBsarch(['list', filePath]);
    const lines = stdout.split(/\r?\n/).map(l => l.trim()).filter(Boolean);

    return lines.map(line => {
      const normalized = line.replace(/\\/g, '/');
      return {
        path: normalized,
        size: 0,
        offset: 0,
        compressed: false
      } as BA2FileEntry;
    });
  }
  /**
   * Read BA2 archive metadata
   * Note: This is a simplified implementation. Full BA2 parsing requires
   * understanding the binary format specification.
   */
  async readArchive(filePath: string): Promise<BA2Archive> {
    if (!this.isValidBA2(filePath)) {
      throw new Error(`Invalid BA2 archive: ${filePath}`);
    }

    const stats = fs.statSync(filePath);
    const fileName = path.basename(filePath);

    // Determine archive type from filename or content
    const type = this.detectArchiveType(filePath);

    const files = await this.listArchiveFiles(filePath);

    return {
      fileName,
      fullPath: filePath,
      type,
      size: stats.size,
      files
    };
  }

  /**
   * Detect BA2 archive type (GENERAL or DDS)
   */
  private detectArchiveType(filePath: string): BA2Type {
    const fileName = path.basename(filePath).toLowerCase();
    
    // DDS archives typically contain "textures" in the name
    if (fileName.includes('textures') || fileName.includes('dds')) {
      return BA2Type.DDS;
    }
    
    return BA2Type.GENERAL;
  }

  /**
   * Check if file is a valid BA2 archive
   */
  isValidBA2(filePath: string): boolean {
    if (!fs.existsSync(filePath)) {
      return false;
    }

    try {
      const buffer = Buffer.alloc(4);
      const fd = fs.openSync(filePath, 'r');
      fs.readSync(fd, buffer, 0, 4, 0);
      fs.closeSync(fd);

      // BA2 magic number is "BTDX" (0x58445442)
      const magic = buffer.toString('ascii');
      return magic === 'BTDX';
    } catch (error) {
      return false;
    }
  }

  /**
   * Get all BA2 files in a directory
   */
  findBA2Files(directory: string): string[] {
    const ba2Files: string[] = [];
    
    if (!fs.existsSync(directory)) {
      return ba2Files;
    }

    const files = fs.readdirSync(directory);
    for (const file of files) {
      const filePath = path.join(directory, file);
      if (file.toLowerCase().endsWith('.ba2') && this.isValidBA2(filePath)) {
        ba2Files.push(filePath);
      }
    }

    return ba2Files;
  }

  /**
   * Merge multiple BA2 archives into one
   * Note: Simplified implementation - production version would handle:
   * - Binary format writing
   * - Compression
   * - Proper offset calculation
   */
  async mergeArchives(
    archives: BA2Archive[],
    outputPath: string,
    type: BA2Type,
    options?: { extraFilesDir?: string; allowOverwrite?: boolean }
  ): Promise<boolean> {
    const allSameType = archives.every(a => a.type === type);
    if (!allSameType) {
      throw new Error('Cannot merge archives of different types');
    }

    const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'mossy-merge-'));
    const combinedDir = path.join(tempRoot, 'combined');
    fs.mkdirSync(combinedDir, { recursive: true });

    try {
      // Pre-populate with loose/extra files if provided
      if (options?.extraFilesDir && fs.existsSync(options.extraFilesDir)) {
        this.copyIntoCombined(options.extraFilesDir, combinedDir, options?.allowOverwrite === true);
      }

      for (let i = 0; i < archives.length; i++) {
        const archive = archives[i];
        const extractDir = path.join(tempRoot, `extract-${i}`);
        fs.mkdirSync(extractDir, { recursive: true });

        await this.runBsarch(['extract', archive.fullPath, extractDir, '-fo4']);
        this.copyIntoCombined(extractDir, combinedDir, options?.allowOverwrite === true);
      }

      const packArgs = ['pack', outputPath, combinedDir, '-fo4'];
      if (type === BA2Type.DDS) {
        packArgs.push('-dds');
      }

      await this.runBsarch(packArgs);
      return true;
    } finally {
      try {
        fs.rmSync(tempRoot, { recursive: true, force: true });
      } catch {
        // ignore cleanup issues
      }
    }
  }

  private copyIntoCombined(sourceDir: string, targetDir: string, allowOverwrite: boolean): void {
    const entries = fs.readdirSync(sourceDir, { withFileTypes: true });
    for (const entry of entries) {
      const srcPath = path.join(sourceDir, entry.name);
      const destPath = path.join(targetDir, entry.name);

      if (entry.isDirectory()) {
        if (!fs.existsSync(destPath)) {
          fs.mkdirSync(destPath, { recursive: true });
        }
        this.copyIntoCombined(srcPath, destPath, allowOverwrite);
      } else {
        if (fs.existsSync(destPath) && !allowOverwrite) {
          throw new Error(`Conflict while merging files. Duplicate file: ${destPath}`);
        }
        fs.copyFileSync(srcPath, destPath);
      }
    }
  }
}
