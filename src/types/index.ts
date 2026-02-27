/**
 * Types and interfaces for Mossy Manager mod merging system
 */

export interface ModInfo {
  name: string;
  path: string;
  version?: string;
  author?: string;
  category?: string;
  archives: BA2Archive[];
  plugins: string[]; // ESP/ESM files
}

export interface BA2Archive {
  fileName: string;
  fullPath: string;
  type: BA2Type;
  size: number;
  files: BA2FileEntry[];
}

export enum BA2Type {
  GENERAL = 'GENERAL',
  DDS = 'DDS'
}

export interface BA2FileEntry {
  path: string;
  size: number;
  offset: number;
  compressed: boolean;
  hash?: string;
}

export interface MergeCompatibility {
  canMerge: boolean;
  reasons: string[];
  warnings: string[];
  conflictingFiles: string[];
}

export interface MergeGroup {
  id: string;
  name: string;
  mods: ModInfo[];
  outputFileName: string;
  estimatedSize: number;
}

export interface MergeResult {
  success: boolean;
  outputPath: string;
  mergedMods: string[];
  fileCount: number;
  errors: string[];
}

export interface MergeOptions {
  outputDirectory: string;
  compressionLevel?: number;
  createBackup?: boolean;
  overwriteExisting?: boolean;
  validateAfterMerge?: boolean;
  includeLooseFiles?: boolean;
  allowFileOverwrite?: boolean;
  /**
   * When true, the original BA2 archives will be copied to a timestamped
   * subdirectory inside the output folder before merging.  Provides an easy
   * rollback in case something goes wrong.
   */
  backupSources?: boolean;
}
