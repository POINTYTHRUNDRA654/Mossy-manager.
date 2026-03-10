"""
Auto-Update System for Mossy Manager

Provides automatic update checking and installation so users can update
without uninstalling/reinstalling. Preserves all user settings and data.

Update Process:
1. Check for updates (compares current version with latest release)
2. Download new version to temp location
3. On next launch, replace old executable with new one
4. Start the new version

User settings are preserved (stored in AppData, not in exe directory):
- ~/.mossy_manager/config.yaml
- ~/.mossy_manager/backups/
- AppData/Local/ModOrganizer/
"""

import logging
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from packaging import version

# Import version from package
try:
    from mossy_manager import __version__ as PACKAGE_VERSION
except ImportError:
    PACKAGE_VERSION = "1.0.0"

logger = logging.getLogger(__name__)

# Version information
CURRENT_VERSION = PACKAGE_VERSION
UPDATE_CHECK_URL = "https://api.github.com/repos/POINTYTHRUNDRA654/Mossy-manager/releases/latest"
UPDATE_CHECK_INTERVAL_DAYS = 1  # Check for updates daily


class UpdateManager:
    """
    Manages automatic updates for Mossy Manager.

    Features:
    - Checks for new versions from GitHub releases
    - Downloads updates automatically
    - Installs updates on next launch
    - Preserves all user settings and data
    """

    def __init__(self):
        self.current_version = CURRENT_VERSION

        # Update cache location (in AppData, persists across updates)
        self.cache_dir = Path.home() / ".mossy_manager" / "updates"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.update_cache_file = self.cache_dir / "update_check.json"
        self.pending_update_file = self.cache_dir / "pending_update.exe"
        self.update_log_file = self.cache_dir / "update.log"

    def check_for_updates(self, force: bool = False) -> Optional[Dict]:
        """
        Check if a newer version is available.

        Args:
            force: If True, bypass cache and check immediately

        Returns:
            Dict with update info if available, None otherwise:
            {
                'version': '1.1.0',
                'url': 'https://github.com/.../MossyManager.exe',
                'release_notes': 'What's new...',
                'published_at': '2026-03-08T00:00:00Z'
            }
        """
        # Check cache first (unless forced)
        if not force and self.update_cache_file.exists():
            try:
                cache = json.loads(self.update_cache_file.read_text())
                last_check = datetime.fromisoformat(cache['last_check'])

                # If checked recently, use cached result
                if datetime.now() - last_check < timedelta(days=UPDATE_CHECK_INTERVAL_DAYS):
                    logger.info(f"Using cached update check from {last_check}")
                    return cache.get('update_info')
            except Exception as e:
                logger.warning(f"Failed to read update cache: {e}")

        # Check for updates online
        try:
            import requests

            logger.info("Checking for updates...")
            response = requests.get(UPDATE_CHECK_URL, timeout=10)
            response.raise_for_status()

            release_data = response.json()

            latest_version = release_data['tag_name'].lstrip('v')  # Remove 'v' prefix if present

            # Compare versions
            if version.parse(latest_version) > version.parse(self.current_version):
                logger.info(f"New version available: {latest_version} (current: {self.current_version})")

                # Find the MossyManager_gui.exe asset (or fallback to MossyManager.exe)
                download_url = None
                for asset in release_data.get('assets', []):
                    if asset['name'] in ('MossyManager_gui.exe', 'MossyManager.exe'):
                        download_url = asset['browser_download_url']
                        break

                if not download_url:
                    logger.warning("No MossyManager.exe found in release assets")
                    return None

                update_info = {
                    'version': latest_version,
                    'url': download_url,
                    'release_notes': release_data.get('body', 'No release notes available'),
                    'published_at': release_data.get('published_at'),
                    'size_mb': asset.get('size', 0) / (1024 * 1024)
                }

                # Cache the result
                cache = {
                    'last_check': datetime.now().isoformat(),
                    'update_info': update_info
                }
                self.update_cache_file.write_text(json.dumps(cache, indent=2))

                return update_info
            else:
                logger.info(f"Already on latest version: {self.current_version}")

                # Cache "no update available"
                cache = {
                    'last_check': datetime.now().isoformat(),
                    'update_info': None
                }
                self.update_cache_file.write_text(json.dumps(cache, indent=2))

                return None

        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None

    def download_update(self, update_info: Dict) -> bool:
        """
        Download the update to pending location.

        Args:
            update_info: Update info from check_for_updates()

        Returns:
            True if download successful
        """
        try:
            import requests

            download_url = update_info['url']
            logger.info(f"Downloading update from {download_url}")

            # Download with progress
            response = requests.get(download_url, stream=True, timeout=300)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            with open(self.pending_update_file, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    # Log progress every 5 MB
                    if downloaded % (5 * 1024 * 1024) == 0:
                        progress = (downloaded / total_size * 100) if total_size > 0 else 0
                        logger.info(f"Download progress: {progress:.1f}% ({downloaded / (1024*1024):.1f} MB)")

            logger.info(f"Update downloaded successfully: {self.pending_update_file}")
            logger.info(f"Size: {self.pending_update_file.stat().st_size / (1024*1024):.1f} MB")

            return True

        except Exception as e:
            logger.error(f"Failed to download update: {e}")
            if self.pending_update_file.exists():
                self.pending_update_file.unlink()
            return False

    def has_pending_update(self) -> bool:
        """Check if there's a pending update ready to install."""
        return self.pending_update_file.exists()

    def apply_update(self) -> bool:
        """
        Apply the pending update.

        This should be called on next launch, before the main app starts.
        Replaces the current executable with the downloaded one.

        Returns:
            True if update applied successfully
        """
        if not self.has_pending_update():
            logger.info("No pending update to apply")
            return False

        try:
            # Get path to current executable
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                current_exe = Path(sys.executable)
            else:
                # Running from source (development mode)
                logger.warning("Cannot apply update in development mode")
                return False

            logger.info(f"Applying update: {self.pending_update_file} -> {current_exe}")

            # Backup current version
            backup_exe = current_exe.parent / f"{current_exe.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.exe"
            shutil.copy2(current_exe, backup_exe)
            logger.info(f"Backed up current version: {backup_exe}")

            # Replace executable
            # On Windows, we can't replace a running exe directly
            # So we use a batch script that waits for this process to exit, then replaces the file

            batch_script = self.cache_dir / "apply_update.bat"

            # Find the repository root (go up from cache_dir)
            repo_root = self.cache_dir.parent.parent.parent.parent  # ~/.mossy_manager/updates -> repo root
            build_script = repo_root / "build.py"

            batch_content = f"""@echo off
echo Applying Mossy Manager update...
timeout /t 2 /nobreak >nul
move /Y "{self.pending_update_file}" "{current_exe}"
if errorlevel 1 (
    echo Update failed! Restoring backup...
    move /Y "{backup_exe}" "{current_exe}"
    pause
    exit /b 1
)
echo Update applied successfully!
del "{backup_exe}"

REM Rebuild the executable to ensure latest version is compiled
if exist "{build_script}" (
    echo Rebuilding executable...
    cd /d "{repo_root}"
    python build.py
    if errorlevel 1 (
        echo Warning: Build failed, but update was applied. Starting existing executable...
    )
) else (
    echo Note: build.py not found, skipping rebuild
)

start "" "{current_exe}"
del "%~f0"
"""
            batch_script.write_text(batch_content)

            # Launch the batch script and exit
            logger.info("Launching update installer...")
            subprocess.Popen(['cmd', '/c', str(batch_script)], shell=False)

            # Log update
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'from_version': self.current_version,
                'to_version': 'unknown',  # Will be known after restart
                'status': 'pending'
            }

            if self.update_log_file.exists():
                logs = json.loads(self.update_log_file.read_text())
            else:
                logs = []

            logs.append(log_entry)
            self.update_log_file.write_text(json.dumps(logs, indent=2))

            return True

        except Exception as e:
            logger.error(f"Failed to apply update: {e}")
            return False

    def get_update_history(self) -> list:
        """Get history of applied updates."""
        if not self.update_log_file.exists():
            return []

        try:
            return json.loads(self.update_log_file.read_text())
        except Exception:
            return []


def check_and_apply_pending_update():
    """
    Check for and apply pending updates on startup.

    This should be called early in the application startup,
    before the main GUI or CLI is launched.
    """
    updater = UpdateManager()

    if updater.has_pending_update():
        logger.info("Pending update found, applying...")
        success = updater.apply_update()

        if success:
            logger.info("Update will be applied after restart")
            # The batch script will restart the app
            sys.exit(0)
        else:
            logger.error("Failed to apply update")
