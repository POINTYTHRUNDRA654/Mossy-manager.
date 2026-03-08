/**
 * ModParser
 * 
 * Parses mod directories and extracts metadata
 */

import * as fs from 'fs';
import * as path from 'path';
import { ModInfo } from '../types';
import { BA2Handler } from './BA2Handler';

export class ModParser {
  private ba2Handler: BA2Handler;

  constructor() {
    this.ba2Handler = new BA2Handler();
  }

  /**
   * Parse a mod directory and extract information
   */
  async parseMod(modPath: string): Promise<ModInfo> {
    if (!fs.existsSync(modPath)) {
      throw new Error(`Mod path does not exist: ${modPath}`);
    }

    const modName = path.basename(modPath);
    const archives = await this.findArchives(modPath);
    const plugins = this.findPlugins(modPath);

    return {
      name: modName,
      path: modPath,
      archives,
      plugins
    };
  }

  /**
   * Parse multiple mod directories
   */
  async parseMods(modPaths: string[]): Promise<ModInfo[]> {
    const results = await Promise.allSettled(
      modPaths.map(async modPath => {
        const mod = await this.parseMod(modPath);
        return mod;
      })
    );

    results
      .filter(r => r.status === 'rejected')
      .forEach(r => console.error('Error parsing mod:', (r as PromiseRejectedResult).reason));

    return results
      .filter(r => r.status === 'fulfilled')
      .map(r => (r as PromiseFulfilledResult<ModInfo>).value);
  }

  /**
   * Find all BA2 archives in mod directory
   */
  private async findArchives(modPath: string) {
    const ba2Files = this.ba2Handler.findBA2Files(modPath);
    const archives = [];

    for (const ba2File of ba2Files) {
      try {
        const archive = await this.ba2Handler.readArchive(ba2File);
        archives.push(archive);
      } catch (error) {
        console.error(`Error reading archive ${ba2File}:`, error);
      }
    }

    return archives;
  }

  /**
   * Find all plugin files (ESP, ESM, ESL)
   */
  private findPlugins(modPath: string): string[] {
    const plugins: string[] = [];

    if (!fs.existsSync(modPath)) {
      return plugins;
    }

    const files = fs.readdirSync(modPath);
    for (const file of files) {
      const lowerFile = file.toLowerCase();
      if (lowerFile.endsWith('.esp') || lowerFile.endsWith('.esm') || lowerFile.endsWith('.esl')) {
        plugins.push(file);
      }
    }

    return plugins;
  }

  /**
   * Scan a directory tree for mods
   * Useful for scanning MO2's mods directory
   */
  async scanModDirectory(baseDir: string): Promise<ModInfo[]> {
    if (!fs.existsSync(baseDir)) {
      throw new Error(`Directory does not exist: ${baseDir}`);
    }

    const entries = fs.readdirSync(baseDir, { withFileTypes: true });
    const modPaths = entries
      .filter(entry => entry.isDirectory())
      .map(entry => path.join(baseDir, entry.name));

    return this.parseMods(modPaths);
  }
}
