# Contributing to Mossy Manager

Thank you for your interest in contributing to Mossy Manager! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, MO2 version)
- Relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please create an issue with:
- A clear description of the feature
- Why this feature would be useful
- Example use cases
- Any implementation ideas you have

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** following the code style guidelines
3. **Add tests** for any new functionality
4. **Run the test suite** to ensure nothing broke
5. **Update documentation** as needed
6. **Submit a pull request** with a clear description of changes

## Development Setup

### Prerequisites

- Python 3.8 or higher
- pip
- git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Mossy-manager.
cd Mossy-manager.

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Install testing dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/ -v
```

## Code Style

### Python Style Guide

This project follows [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines:

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (compatible with Black formatter)
- Use descriptive variable names
- Add docstrings to all functions, classes, and modules
- Use type hints where appropriate

### Example

```python
def load_plugins_txt(self, filepath: Path) -> None:
    """
    Load plugins from plugins.txt file
    
    Args:
        filepath: Path to plugins.txt file
    """
    # Implementation here
```

### Documentation Strings

Use Google-style docstrings:

```python
def function_name(arg1: str, arg2: int) -> bool:
    """
    Brief description of function.
    
    Longer description if needed, explaining behavior,
    edge cases, etc.
    
    Args:
        arg1: Description of arg1
        arg2: Description of arg2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When arg1 is invalid
    """
```

## Testing

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Test both success and failure cases
- Use fixtures for common test data

### Test Structure

```python
class TestFeatureName:
    """Test FeatureName class"""
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        feature = FeatureName()
        
        # Act
        result = feature.do_something()
        
        # Assert
        assert result == expected_value
    
    def test_edge_case(self):
        """Test edge case"""
        # Test implementation
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_load_order.py -v

# Run with coverage
pytest tests/ --cov=mossy_manager --cov-report=html

# Run specific test
pytest tests/test_load_order.py::TestPlugin::test_plugin_creation -v
```

## Project Structure

```
Mossy-manager/
├── src/
│   └── mossy_manager/
│       ├── __init__.py
│       ├── core/              # Core functionality
│       │   ├── load_order.py
│       │   ├── conflict_resolver.py
│       │   └── patcher.py
│       ├── cli/               # Command-line interface
│       │   └── main.py
│       └── utils/             # Utility functions
├── tests/                     # Test files
│   ├── test_load_order.py
│   ├── test_conflict_resolver.py
│   └── test_patcher.py
├── demo/                      # Example files
├── setup.py                   # Package configuration
├── requirements.txt           # Dependencies
└── README.md                  # Main documentation
```

## Adding New Features

### 1. Load Order Features

Add to `src/mossy_manager/core/load_order.py`:
- New validation rules
- Additional sorting algorithms
- Plugin dependency resolution

### 2. Conflict Resolution Features

Add to `src/mossy_manager/core/conflict_resolver.py`:
- New conflict types
- Advanced detection algorithms
- Resolution strategies

### 3. Patching Features

Add to `src/mossy_manager/core/patcher.py`:
- New operation types
- Patch templates
- Automated patch generation

### 4. CLI Commands

Add to `src/mossy_manager/cli/main.py`:
- New command groups
- Additional options
- Output formatting

## Commit Message Guidelines

Use clear, descriptive commit messages:

```
Add feature to detect script conflicts

- Implement script file scanning
- Add severity classification for scripts
- Update tests for script detection
```

Format:
- First line: Brief summary (50 chars or less)
- Blank line
- Detailed description in bullet points if needed

## Documentation

When adding features, update:
- Function/class docstrings
- README.md (if user-facing)
- EXAMPLES.md (with usage examples)
- Type hints and annotations

## Release Process

1. Update version in `setup.py` and `__init__.py`
2. Update CHANGELOG.md (if exists)
3. Run full test suite
4. Create a git tag: `git tag v0.x.x`
5. Push tag: `git push origin v0.x.x`

## Questions?

- Open an issue for questions
- Check existing issues and documentation first
- Be patient - maintainers are volunteers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Mossy Manager! 🎉
