/**
 * Configuration Manager
 * 
 * Handles loading and saving user configuration
 */

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';

export interface Config {
  defaultOutputDir?: string;
  defaultBackup?: boolean;
  defaultValidate?: boolean;
  autoDetectMO2?: boolean;
  lastUsedDirectory?: string;
}

export class ConfigManager {
  private configPath: string;
  private config: Config;

  constructor() {
    // Store config in user's home directory
    const homeDir = os.homedir();
    const configDir = path.join(homeDir, '.mossy-manager');
    this.configPath = path.join(configDir, 'config.json');
    
    // Ensure config directory exists
    if (!fs.existsSync(configDir)) {
      fs.mkdirSync(configDir, { recursive: true });
    }
    
    this.config = this.loadConfig();
  }

  /**
   * Load configuration from file
   */
  private loadConfig(): Config {
    if (fs.existsSync(this.configPath)) {
      try {
        const data = fs.readFileSync(this.configPath, 'utf8');
        return JSON.parse(data);
      } catch (error) {
        console.warn('Failed to load config, using defaults');
        return {};
      }
    }
    return {};
  }

  /**
   * Save configuration to file
   */
  saveConfig(): void {
    try {
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
    } catch (error) {
      console.error('Failed to save config:', error);
    }
  }

  /**
   * Get configuration value
   */
  get<K extends keyof Config>(key: K): Config[K] {
    return this.config[key];
  }

  /**
   * Set configuration value
   */
  set<K extends keyof Config>(key: K, value: Config[K]): void {
    this.config[key] = value;
  }

  /**
   * Get all config
   */
  getAll(): Config {
    return { ...this.config };
  }

  /**
   * Update last used directory
   */
  updateLastDirectory(directory: string): void {
    this.config.lastUsedDirectory = directory;
    this.saveConfig();
  }
}
