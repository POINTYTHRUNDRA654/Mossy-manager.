"""
Profile Manager - Handles MO2 profile operations
"""

import os
from pathlib import Path
import shutil


class ProfileManager:
    """Manages Mod Organizer 2 profiles"""
    
    def __init__(self, mo2_path=None):
        """Initialize the profile manager
        
        Args:
            mo2_path: Path to MO2 installation (optional)
        """
        self.mo2_path = mo2_path or os.getcwd()
        self.profiles_path = Path(self.mo2_path) / "profiles"
        
    def list_profiles(self):
        """List all available profiles
        
        Returns:
            List of profile names
        """
        if not self.profiles_path.exists():
            return []
        
        profiles = []
        for item in self.profiles_path.iterdir():
            if item.is_dir():
                profiles.append(item.name)
        
        return sorted(profiles)
    
    def create_profile(self, profile_name):
        """Create a new profile
        
        Args:
            profile_name: Name of the profile to create
        """
        profile_path = self.profiles_path / profile_name
        
        if profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' already exists")
        
        # Create profile directory
        profile_path.mkdir(parents=True, exist_ok=True)
        
        # Create basic profile files
        modlist_file = profile_path / "modlist.txt"
        modlist_file.write_text("# Modlist for profile: {}\n".format(profile_name))
        
        print(f"Created profile: {profile_name}")
        return True
    
    def delete_profile(self, profile_name):
        """Delete a profile
        
        Args:
            profile_name: Name of the profile to delete
        """
        profile_path = self.profiles_path / profile_name
        
        if not profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' not found")
        
        shutil.rmtree(profile_path)
        print(f"Deleted profile: {profile_name}")
        return True
    
    def switch_profile(self, profile_name):
        """Switch to a different profile
        
        Args:
            profile_name: Name of the profile to switch to
        """
        profile_path = self.profiles_path / profile_name
        
        if not profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' not found")
        
        print(f"Switched to profile: {profile_name}")
        return True
    
    def get_profile_info(self, profile_name):
        """Get information about a profile
        
        Args:
            profile_name: Name of the profile
            
        Returns:
            Dictionary with profile information
        """
        profile_path = self.profiles_path / profile_name
        
        if not profile_path.exists():
            raise ValueError(f"Profile '{profile_name}' not found")
        
        info = {
            "name": profile_name,
            "path": str(profile_path),
            "exists": True,
        }
        
        modlist_file = profile_path / "modlist.txt"
        if modlist_file.exists():
            info["has_modlist"] = True
        else:
            info["has_modlist"] = False
        
        return info
