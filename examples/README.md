# Mossy Manager Examples

This directory contains example files and usage demonstrations for Mossy Manager.

## Quick Start Example

Here's a simple example of using Mossy Manager to manage your MO2 installation:

### 1. Set up your configuration

```bash
# Set your MO2 installation path
mossy-manager config set --key mo2_path --value "C:/Modding/MO2"

# Set your default profile
mossy-manager config set --key default_profile --value "Default"

# Verify configuration
mossy-manager config show
```

### 2. Manage Profiles

```bash
# List existing profiles
mossy-manager profile list --path "C:/Modding/MO2"

# Create a new profile for testing
mossy-manager profile create --name "Testing" --path "C:/Modding/MO2"

# Switch to the new profile
mossy-manager profile switch --name "Testing" --path "C:/Modding/MO2"
```

### 3. Manage Mods

```bash
# List all installed mods
mossy-manager mod list --path "C:/Modding/MO2"

# Get information about a specific mod
mossy-manager mod info --name "SkyUI" --path "C:/Modding/MO2"

# Enable a mod
mossy-manager mod enable --name "SkyUI" --path "C:/Modding/MO2"

# Disable a mod
mossy-manager mod disable --name "SkyUI" --path "C:/Modding/MO2"
```

### 4. View Installation Info

```bash
# Get information about your MO2 installation
mossy-manager info --path "C:/Modding/MO2"
```

## Example Use Cases

### Use Case 1: Quick Profile Switching

If you maintain multiple modded setups (e.g., vanilla+, hardcore, performance), you can quickly switch between them:

```bash
mossy-manager profile switch --name "vanilla-plus"
mossy-manager profile switch --name "hardcore-survival"
mossy-manager profile switch --name "performance"
```

### Use Case 2: Batch Mod Management

You can create scripts to manage multiple mods at once:

```bash
#!/bin/bash
# enable-graphics-mods.sh

mossy-manager mod enable --name "Enhanced Textures"
mossy-manager mod enable --name "Realistic Lighting"
mossy-manager mod enable --name "Better Weather"
```

### Use Case 3: Profile Backup

Before testing new mods, create a backup profile:

```bash
mossy-manager profile create --name "Backup-$(date +%Y%m%d)"
```

## Tips and Best Practices

1. **Always specify the path**: While Mossy Manager can work from the current directory, it's safer to always specify the full path to your MO2 installation.

2. **Use configuration**: Set up your configuration once to avoid typing the same paths repeatedly:
   ```bash
   mossy-manager config set --key mo2_path --value "/your/mo2/path"
   ```

3. **Create test profiles**: Before making major changes, create a test profile to experiment safely.

4. **Regular backups**: Use profile management to create regular backups of your working setups.

## Troubleshooting

### "No mods found" error
Make sure you're pointing to the correct MO2 installation directory. The path should contain a "mods" subdirectory.

### "Profile not found" error
Check that the profile name is spelled correctly and exists in the MO2 installation.

### Configuration not saving
Ensure you have write permissions to your home directory where the configuration file is stored (`~/.mossy-manager/config.ini`).

## More Information

For more detailed information, see the main [README.md](../README.md) in the root directory.
