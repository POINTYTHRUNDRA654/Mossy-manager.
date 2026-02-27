#!/usr/bin/env python3
"""
Mossy Manager - Main entry point
A tool to manage Mod Organizer 2 profiles, mods, and configurations
"""

import sys
import os
import argparse
from mossy_manager.mod_manager import ModManager
from mossy_manager.profile_manager import ProfileManager
from mossy_manager.config_manager import ConfigManager


def print_banner():
    """Print the application banner"""
    banner = """
    ╔═══════════════════════════════════════╗
    ║       Mossy Manager v1.0.0            ║
    ║   Mod Organizer 2 Management Tool     ║
    ╚═══════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point for the application"""
    print_banner()

    parser = argparse.ArgumentParser(
        description="Mossy Manager - Manage your Mod Organizer 2 setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Mod management commands
    mod_parser = subparsers.add_parser("mod", help="Manage mods")
    mod_parser.add_argument("action", choices=["list", "enable", "disable", "info"],
                            help="Action to perform")
    mod_parser.add_argument("--name", help="Mod name")
    mod_parser.add_argument("--path", help="MO2 installation path")

    # Profile management commands
    profile_parser = subparsers.add_parser("profile", help="Manage profiles")
    profile_parser.add_argument("action", choices=["list", "create", "delete", "switch"],
                                help="Action to perform")
    profile_parser.add_argument("--name", help="Profile name")
    profile_parser.add_argument("--path", help="MO2 installation path")

    # Config management commands
    config_parser = subparsers.add_parser("config", help="Manage configuration")
    config_parser.add_argument("action", choices=["show", "set", "get"],
                               help="Action to perform")
    config_parser.add_argument("--key", help="Configuration key")
    config_parser.add_argument("--value", help="Configuration value")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show MO2 installation info")
    info_parser.add_argument("--path", help="MO2 installation path")

    # Detect command (added for auto-detection of MO2/xEdit and MO2 configuration)
    detect_parser = subparsers.add_parser(
        "detect", help="Auto-detect MO2, xEdit, and suggest MO2 executable settings"
    )
    detect_parser.add_argument(
        "--mo2-config", help="Write a simple MO2 executable ini snippet to this file"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    try:
        # Handle commands
        if args.command == "mod":
            mod_manager = ModManager(args.path)

            if args.action == "list":
                print("\n📦 Available Mods:")
                mods = mod_manager.list_mods()
                if not mods:
                    print("  No mods found. Please specify a valid MO2 path.")
                for mod in mods:
                    print(f"  • {mod}")

            elif args.action == "enable":
                if not args.name:
                    print("Error: --name required for enable action")
                    return 1
                mod_manager.enable_mod(args.name)
                print(f"✓ Enabled mod: {args.name}")

            elif args.action == "disable":
                if not args.name:
                    print("Error: --name required for disable action")
                    return 1
                mod_manager.disable_mod(args.name)
                print(f"✓ Disabled mod: {args.name}")

            elif args.action == "info":
                if not args.name:
                    print("Error: --name required for info action")
                    return 1
                info = mod_manager.get_mod_info(args.name)
                print(f"\n📋 Mod Information: {args.name}")
                for key, value in info.items():
                    print(f"  {key}: {value}")

        elif args.command == "profile":
            profile_manager = ProfileManager(args.path)

            if args.action == "list":
                print("\n👤 Available Profiles:")
                profiles = profile_manager.list_profiles()
                if not profiles:
                    print("  No profiles found. Please specify a valid MO2 path.")
                for profile in profiles:
                    print(f"  • {profile}")

            elif args.action == "create":
                if not args.name:
                    print("Error: --name required for create action")
                    return 1
                profile_manager.create_profile(args.name)
                print(f"✓ Created profile: {args.name}")

            elif args.action == "delete":
                if not args.name:
                    print("Error: --name required for delete action")
                    return 1
                profile_manager.delete_profile(args.name)
                print(f"✓ Deleted profile: {args.name}")

            elif args.action == "switch":
                if not args.name:
                    print("Error: --name required for switch action")
                    return 1
                profile_manager.switch_profile(args.name)
                print(f"✓ Switched to profile: {args.name}")

        elif args.command == "config":
            config_manager = ConfigManager()

            if args.action == "show":
                print("\n⚙️  Current Configuration:")
                config = config_manager.get_all_config()
                for key, value in config.items():
                    print(f"  {key}: {value}")

            elif args.action == "set":
                if not args.key or not args.value:
                    print("Error: --key and --value required for set action")
                    return 1
                config_manager.set_config(args.key, args.value)
                print(f"✓ Set {args.key} = {args.value}")

            elif args.action == "get":
                if not args.key:
                    print("Error: --key required for get action")
                    return 1
                value = config_manager.get_config(args.key)
                print(f"{args.key}: {value}")

        elif args.command == "info":
            print("\n🔍 MO2 Installation Info:")
            print(f"  Path: {args.path or 'Not specified'}")
            print(f"  Status: Ready to manage")
            print("\nUse 'mossy-manager --help' to see available commands")

        elif args.command == "detect":
            from mossy_manager.integrations.mo2 import MO2Integration
            from mossy_manager.utils.xedit_integration import XEditIntegration

            detected = MO2Integration.detect_mo2_installation()
            if detected:
                print(f"Detected MO2 at: {detected}")
                print("To add Mossy Manager in MO2 executables use:")
                print("  Title     : Mossy Manager")
                print(f"  Binary    : {detected}/tools/MossyManager/MossyManager.exe")
                print("  Arguments : auto --profile \"Default\"")
                print("  Start in  : (leave blank)")
                if args.mo2_config:
                    try:
                        rel = os.path.relpath(
                            os.path.join(detected, 'tools', 'MossyManager', 'MossyManager.exe'),
                            start=detected
                        )
                    except Exception:
                        rel = os.path.join(detected, 'tools', 'MossyManager', 'MossyManager.exe')
                    ini_str = (
                        "[General]\n"
                        "name=Mossy Manager\n"
                        f"path={rel}\n"
                        "args=auto --profile \"Default\"\n"
                        "workDir=\n"
                    )
                    with open(args.mo2_config, 'w', encoding='utf-8') as f:
                        f.write(ini_str)
                    print(f"INI snippet written to: {args.mo2_config}")
            else:
                print("Mod Organizer 2 installation not detected.")

            xedit_path = None
            try:
                xedit_path = XEditIntegration.detect_xedit('fallout4',
                                                           search_roots=[detected] if detected else None)
            except Exception:
                pass
            if xedit_path:
                print(f"Detected xEdit at: {xedit_path}")
            else:
                print("xEdit installation not found (other commands may accept --xedit-path)")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
