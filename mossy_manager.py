#!/usr/bin/env python3
"""
Mossy Manager - A Mod Organizer 2 Manager Application
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
import subprocess
import platform
from pathlib import Path


class MossyManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mossy Manager - MO2 Manager")
        self.root.geometry("800x600")
        
        # Settings file path
        self.config_file = Path.home() / ".mossy_manager" / "config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load settings
        self.load_settings()
        
        # Configure the main window
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Mossy Manager", 
            font=('Arial', 18, 'bold')
        )
        title_label.grid(row=0, column=0, pady=10)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create tabs
        self.create_manager_tab()
        self.create_settings_tab()
        self.create_about_tab()
        
        # Status bar
        self.status_bar = ttk.Label(
            main_frame, 
            text="Ready", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def create_manager_tab(self):
        """Create the main manager tab"""
        manager_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(manager_frame, text="Manager")
        
        # MO2 Path selection
        path_frame = ttk.LabelFrame(manager_frame, text="Mod Organizer 2 Location", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(1, weight=1)
        
        ttk.Label(path_frame, text="MO2 Path:").grid(row=0, column=0, sticky=tk.W)
        self.mo2_path_var = tk.StringVar(value=self.settings.get('mo2_path', ''))
        self.mo2_path_entry = ttk.Entry(path_frame, textvariable=self.mo2_path_var)
        self.mo2_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        browse_button = ttk.Button(
            path_frame, 
            text="Browse...", 
            command=self.browse_mo2_path
        )
        browse_button.grid(row=0, column=2)
        
        # Mod list frame
        mod_frame = ttk.LabelFrame(manager_frame, text="Mod List", padding="10")
        mod_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        mod_frame.columnconfigure(0, weight=1)
        mod_frame.rowconfigure(0, weight=1)
        manager_frame.rowconfigure(1, weight=1)
        
        # Mod list with scrollbar
        scrollbar = ttk.Scrollbar(mod_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.mod_listbox = tk.Listbox(
            mod_frame, 
            yscrollcommand=scrollbar.set,
            height=15
        )
        self.mod_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.mod_listbox.yview)
        
        # Buttons
        button_frame = ttk.Frame(mod_frame)
        button_frame.grid(row=1, column=0, columnspan=2, pady=(5, 0))
        
        ttk.Button(
            button_frame, 
            text="Refresh Mods", 
            command=self.refresh_mods
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Launch MO2", 
            command=self.launch_mo2
        ).grid(row=0, column=1, padx=5)
        
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(settings_frame, text="Settings")
        
        # Settings content
        ttk.Label(
            settings_frame, 
            text="Settings and Configuration", 
            font=('Arial', 12, 'bold')
        ).grid(row=0, column=0, pady=10)
        
        # Auto-launch option
        self.auto_launch_var = tk.BooleanVar(value=self.settings.get('auto_launch', False))
        auto_launch_check = ttk.Checkbutton(
            settings_frame,
            text="Auto-launch MO2 on startup",
            variable=self.auto_launch_var
        )
        auto_launch_check.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Theme selection
        theme_frame = ttk.LabelFrame(settings_frame, text="Appearance", padding="10")
        theme_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W)
        self.theme_var = tk.StringVar(value=self.settings.get('theme', 'Light'))
        theme_combo = ttk.Combobox(
            theme_frame,
            textvariable=self.theme_var,
            values=["Light", "Dark"],
            state="readonly",
            width=15
        )
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Save button
        ttk.Button(
            settings_frame,
            text="Save Settings",
            command=self.save_settings
        ).grid(row=3, column=0, pady=20)
        
    def create_about_tab(self):
        """Create the about tab"""
        about_frame = ttk.Frame(self.notebook, padding="20")
        self.notebook.add(about_frame, text="About")
        
        # About content
        ttk.Label(
            about_frame,
            text="Mossy Manager",
            font=('Arial', 16, 'bold')
        ).grid(row=0, column=0, pady=10)
        
        ttk.Label(
            about_frame,
            text="Mod Organizer 2 Manager",
            font=('Arial', 12)
        ).grid(row=1, column=0, pady=5)
        
        ttk.Label(
            about_frame,
            text="Version 1.0.0",
            font=('Arial', 10)
        ).grid(row=2, column=0, pady=5)
        
        ttk.Separator(about_frame, orient='horizontal').grid(
            row=3, column=0, sticky=(tk.W, tk.E), pady=20
        )
        
        about_text = (
            "Mossy Manager is a utility application for managing\n"
            "Mod Organizer 2 installations and configurations.\n\n"
            "Features:\n"
            "• Manage MO2 installation paths\n"
            "• View and organize mods\n"
            "• Quick launch functionality\n"
            "• Customizable settings"
        )
        
        ttk.Label(
            about_frame,
            text=about_text,
            justify=tk.LEFT
        ).grid(row=4, column=0, pady=10)
        
    def browse_mo2_path(self):
        """Browse for MO2 installation directory"""
        directory = filedialog.askdirectory(
            title="Select Mod Organizer 2 Installation Directory"
        )
        if directory:
            self.mo2_path_var.set(directory)
            self.settings['mo2_path'] = directory
            self.save_settings_to_file()
            self.update_status(f"MO2 path set to: {directory}")
            self.refresh_mods()
            
    def refresh_mods(self):
        """Refresh the mod list"""
        self.mod_listbox.delete(0, tk.END)
        mo2_path = self.mo2_path_var.get()
        
        if not mo2_path:
            self.update_status("Please set MO2 path first")
            return
            
        mods_path = Path(mo2_path) / "mods"
        
        if mods_path.exists() and mods_path.is_dir():
            mods = [d.name for d in mods_path.iterdir() if d.is_dir()]
            for mod in sorted(mods):
                self.mod_listbox.insert(tk.END, mod)
            self.update_status(f"Found {len(mods)} mods")
        else:
            self.update_status("Mods directory not found")
            messagebox.showwarning(
                "Directory Not Found",
                "Could not find the 'mods' directory in the specified MO2 path."
            )
            
    def launch_mo2(self):
        """Launch Mod Organizer 2 (cross-platform)"""
        mo2_path = self.mo2_path_var.get()
        
        if not mo2_path:
            messagebox.showerror(
                "Error",
                "Please set the MO2 path first"
            )
            return
            
        mo2_exe = Path(mo2_path) / "ModOrganizer.exe"
        
        if mo2_exe.exists():
            try:
                system = platform.system()
                if system == 'Windows':
                    os.startfile(str(mo2_exe))
                elif system == 'Darwin':  # macOS
                    subprocess.Popen(['open', str(mo2_exe)])
                else:  # Linux and others
                    subprocess.Popen(['xdg-open', str(mo2_exe)])
                self.update_status("Launching Mod Organizer 2...")
            except Exception as e:
                messagebox.showerror(
                    "Launch Error",
                    f"Failed to launch MO2: {str(e)}"
                )
        else:
            messagebox.showerror(
                "Error",
                "ModOrganizer.exe not found in the specified path"
            )
            
    def save_settings(self):
        """Save application settings"""
        # Update settings from UI
        self.settings['auto_launch'] = self.auto_launch_var.get()
        self.settings['theme'] = self.theme_var.get()
        
        # Save to file
        if self.save_settings_to_file():
            messagebox.showinfo(
                "Settings Saved",
                "Your settings have been saved successfully!"
            )
            self.update_status("Settings saved")
        else:
            messagebox.showerror(
                "Save Error",
                "Failed to save settings. Check file permissions."
            )
    
    def load_settings(self):
        """Load settings from file"""
        self.settings = {
            'mo2_path': '',
            'auto_launch': False,
            'theme': 'Light'
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.settings.update(saved_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings_to_file(self):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
        
    def update_status(self, message):
        """Update the status bar"""
        self.status_bar.config(text=message)


def main():
    """Main entry point for the application"""
    root = tk.Tk()
    app = MossyManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
