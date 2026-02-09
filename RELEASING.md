# Release Instructions

This document describes how to create and publish releases for Mossy Manager.

## Automated Releases (Recommended)

The project uses GitHub Actions to automatically build executables for Windows, Linux, and macOS.

### Creating a New Release

1. **Update Version**: Ensure version numbers are updated in:
   - `mossy_manager.py` (in the About tab)
   - `README.md` (if version is mentioned)

2. **Create and Push a Tag**:
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

3. **Automatic Build**: GitHub Actions will:
   - Build executables for all platforms
   - Create a new release
   - Upload the executables as release assets

### Manual Release Process

If you prefer to build and release manually:

1. **Build Locally**:
   ```bash
   # On your target platform
   ./build.sh  # Linux/Mac
   # or
   build.bat   # Windows
   ```

2. **Test the Executable**: Verify the executable works correctly

3. **Create GitHub Release**:
   - Go to the Releases page on GitHub
   - Click "Draft a new release"
   - Create a new tag (e.g., v1.0.0)
   - Fill in the release notes
   - Upload the executable files:
     - `dist/MossyManager.exe` (Windows)
     - `dist/MossyManager` (Linux/Mac)

## Version Numbering

We follow semantic versioning (MAJOR.MINOR.PATCH):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

## Release Checklist

Before creating a release:

- [ ] All tests pass
- [ ] Version numbers updated
- [ ] README.md is up to date
- [ ] CHANGELOG updated (if you maintain one)
- [ ] Build succeeds on all target platforms
- [ ] Manual testing completed
- [ ] No known critical bugs

## Artifacts

Each release should include:
- Windows executable (`.exe`)
- Linux executable
- macOS executable (if applicable)
- Source code (automatically included by GitHub)

## Troubleshooting Build Issues

### Linux/macOS Build Fails
- Ensure Python 3.8+ is installed
- Check that PyInstaller is properly installed
- Verify all dependencies are available

### Windows Build Fails
- Run as Administrator if permission issues occur
- Check Windows Defender isn't blocking PyInstaller
- Ensure Visual C++ Redistributable is installed

### Artifact Upload Fails
- Check GitHub token permissions
- Verify workflow has write access to releases
- Ensure artifact names don't conflict

## Post-Release

After creating a release:
1. Test the release downloads
2. Update any documentation links
3. Announce the release (if applicable)
4. Monitor for user feedback

## Rollback

If a release has critical issues:
1. Mark the release as "pre-release" or delete it
2. Fix the issue
3. Create a new patch release
