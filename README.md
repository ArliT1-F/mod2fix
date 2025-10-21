# mod2fix

**The Ultimate Minecraft Mod Error Diagnostic Tool**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🎯 Overview

mod2fix analyzes Minecraft mod crashes, identifies compatibility issues, and provides solutions with direct download links.

### ✨ Key Features

- 🔍 **Crash Analysis**: Parse crash logs to identify mod conflicts
- 📦 **Dependency Resolution**: Detect and fix missing dependencies
- 🎮 **Multi-Loader Support**: Compatible with Fabric, Forge, and Quilt
- ⚡ **Performance**: Efficiently process large mod collections

## 🚀 Quick Start (Users)

1. **Installation**
```bash
pip install mod2fix
```

2. **Basic Usage**
```bash
# Analyze a crash report
mod2fix analyze crash-report.txt

# Check mod compatibility
mod2fix check /path/to/mods/folder

# Auto-fix dependencies
mod2fix fix /path/to/mods/folder
```

3. **Web Interface**
```bash
mod2fix web
# Open http://localhost:8000 in your browser
```

## 🔧 Troubleshooting

### Common Issues

1. **ModNotFoundError**
```bash
# Error
ModNotFoundError: No mod file found at path

# Solution
Ensure the path to your mods folder is correct and contains .jar files
```

2. **Invalid Crash Log**
```bash
# Error
ValueError: Invalid crash log format

# Solution
Make sure you're using the latest crash log from .minecraft/crash-reports/
```

3. **Dependency Conflicts**
```bash
# Error
DependencyError: Mod X requires Y version Z

# Solution
Run `mod2fix fix` to automatically resolve dependencies
```

### Debug Mode

Enable debug logging for more detailed output:
```bash
mod2fix --debug analyze crash-report.txt
```

## 🚀 Development Setup

### Prerequisites

- Python 3.11+
- Git
- Linux/WSL2 recommended (tested on Ubuntu 24.04.2 LTS)

### Installation

```bash
# Clone repository
git clone https://github.com/ArliT1-F/mod2fix.git
cd mod2fix

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### Development Commands

```bash
# Run tests
pytest

# Check code style
black .
ruff check .

# Type checking
mypy .

# Run with debug logging
python -m mod2fix --debug crash-report.txt
```

## 📖 Documentation

### Module Structure

```
mod2fix/
├── src/
│   ├── analyzers/       # Crash analysis implementations
│   ├── loaders/        # Mod loader specific code
│   ├── utils/          # Shared utilities
│   └── web/           # Web interface
├── tests/             # Test suite
└── examples/          # Example crash logs
```

### Key Classes

#### CrashAnalyzer

```python
class CrashAnalyzer:
    """
    Analyzes Minecraft crash logs to identify mod issues.
    
    Args:
        log_path (Path): Path to crash log file
        mod_folder (Optional[Path]): Path to mods directory
        
    Examples:
        >>> analyzer = CrashAnalyzer("crash.log")
        >>> results = analyzer.analyze()
        >>> print(results.issues)
    """
```

#### ModLoader

```python
class ModLoader:
    """
    Base class for mod loader implementations.
    
    Attributes:
        name (str): Loader name (e.g. "Forge", "Fabric")
        version (str): Minecraft version
        
    Methods:
        scan_mods(): Scans mod folder for compatibility issues
        resolve_dependencies(): Checks and resolves missing dependencies
    """
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting
4. Commit changes (`git commit -m 'Add some amazing feature'`)
5. Push to branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- Add type hints to all new code
- Include docstrings with examples
- Write unit tests for new features
- Follow black code style
- Use ruff for linting
- Keep functions focused and small

## 📝 License

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 Acknowledgments

- Thanks to the Minecraft modding community
- Built with Python and modern development tools
- Inspired by various mod management tools

## 📦 Dependencies Overview

**Core Dependencies** (`requirements.txt`):
```
fastapi>=0.103.0      # Web API framework
pydantic>=2.3.0       # Data validation
aiohttp>=3.8.5        # Async HTTP client
rich>=13.5.2          # Terminal formatting
typer>=0.9.0          # CLI interface
```

**Development Dependencies** (`requirements-dev.txt`):
```
pytest>=7.4.0         # Testing framework
black>=23.7.0         # Code formatter
ruff>=0.0.287         # Fast linter
mypy>=1.5.1          # Type checker
```