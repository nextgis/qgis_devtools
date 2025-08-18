# Contributing to QGIS DevTools

Thank you for your interest in contributing to QGIS DevTools! This guide will help you get started with development and explain how to contribute effectively to the project.

## Table of Contents

- [About the Project](#about-the-project)
- [Development Environment Setup](#development-environment-setup)
- [Building and Testing](#building-and-testing)
- [Code Style and Standards](#code-style-and-standards)
- [Making Contributions](#making-contributions)
- [Issue Reporting](#issue-reporting)
- [Pull Request Process](#pull-request-process)
- [Community and Support](#community-and-support)

## About the Project

QGIS DevTools is a toolkit for QGIS plugin developers that provides advanced debugging capabilities, including remote debugging support via debugpy. The plugin allows developers to connect VS Code debugger directly to QGIS processes.

- **License**: GNU GPL v.2 or later
- **Language**: Python 3.7+
- **Target Platform**: QGIS 3.22+
- **Maintained by**: [NextGIS](https://nextgis.com)

## Development Environment Setup

### Prerequisites

- Python 3.7 or later
- QGIS 3.22 or later
- Git
- A text editor or IDE (VS Code recommended)
- Qt Linguist tools (optional, for translation compilation)
  - On Ubuntu/Debian: `sudo apt install qttools5-dev-tools`
  - On macOS: `brew install qt5`
  - On Windows: Install Qt Creator or Qt tools

### Setting Up the Development Environment

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nextgis/qgis_devtools.git
   cd qgis_devtools
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Set up pre-commit hooks** (recommended):
   ```bash
   pre-commit install
   ```

4. **Configure the development environment**:
   ```bash
   python setup.py config vscode
   ```

## Building and Testing

### Building the Plugin

1. **Bootstrap the plugin** (compile UI files, resources, and translations):
   ```bash
   python setup.py bootstrap
   ```
   
   **Note**: If you don't have Qt Linguist tools installed, you can skip translation compilation:
   ```bash
   python setup.py bootstrap --ui --qrc
   ```

2. **Build the plugin package**:
   ```bash
   python setup.py build
   ```
   This creates a distributable ZIP file in the `build/` directory.

### Installing for Development

**Install in development mode** (creates symlinks, changes reflect immediately):
```bash
python setup.py install --editable
```

**Install normally**:
```bash
python setup.py install
```

**Force reinstall**:
```bash
python setup.py install --force
```

### Testing the Plugin

1. Start QGIS with your development profile
2. Enable the DevTools plugin in the Plugin Manager
3. Test the debugging functionality by:
   - Opening the DevTools menu
   - Starting a debugpy server
   - Connecting from VS Code

### Uninstalling

```bash
python setup.py uninstall
```

### Available Build Commands

- `bootstrap` - Compile UI files, resources, and translations
  - `--ui` - Compile only forms
  - `--qrc` - Compile only resources  
  - `--ts` - Compile only translations
- `build` - Create distributable plugin package
- `install` - Install plugin to QGIS
- `uninstall` - Remove plugin from QGIS
- `clean` - Remove compiled files
- `update_ts` - Update translation files
- `config` - Configure development environment

## Code Style and Standards

### Linting and Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Run linter
ruff check .

# Run formatter
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

### Pre-commit Hooks

The project uses pre-commit hooks that automatically:
- Run Ruff linting and formatting
- Add license headers to Python files
- Validate TOML files

Install and run pre-commit:
```bash
pre-commit install
pre-commit run --all-files
```

### Code Standards

- **Python Version**: Support Python 3.7+
- **Line Length**: 79 characters maximum
- **Code Style**: Follow PEP8 conventions. When overriding Qt base class methods that use camelCase, suppress linting with `# noqa: N802`
- **Docstrings**: Follow PEP 257 conventions
- **Type Hints**: Use type annotations where appropriate
- **License Headers**: All Python files must include the GPL license header
- **Import Organization**: Use isort-compatible import ordering
- **PyQt Imports**: Import PyQt classes from the qgis module for better compatibility (e.g., `from qgis.PyQt.QtCore import QTimer`)

### Project Structure

The main source code is organized as follows:

- `src/devtools/` - Main plugin source code
- `src/devtools/core/` - Common code (utilities, settings, constants, compatibility)
- `src/devtools/shared/` - Base classes and shared components
- `src/devtools/debug/` - Feature directory for debug-related classes and interface
- `src/devtools/ui/` - Common widgets and helper functions
- `src/devtools/i18n/` - Translation files
- `src/devtools/resources/` - Icons and other resources
- `tests/` - Test files (if any)

## Making Contributions

### Types of Contributions

We welcome various types of contributions:

- **Bug fixes** - Fix issues in existing functionality
- **Feature enhancements** - Improve existing features
- **New features** - Add new debugging tools or capabilities
- **Documentation** - Improve docs, comments, or examples
  - For user documentation updates and corrections, use: https://github.com/nextgis/docs_ngqgis/edit/en/source/devtools.rst
- **Translations** - Add or update language translations
- **Testing** - Add tests or improve test coverage

### Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code standards

3. **Test your changes**:
   - Build and install the plugin
   - Test in QGIS manually
   - Run linting checks

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Descriptive commit message"
   ```

5. **Push and create a pull request**

### Translation Updates

To update translations:

1. **Update translation files**:
   ```bash
   python setup.py update_ts
   ```

2. **Edit translation files** in `src/devtools/i18n/`

3. **Test the translations** by building and installing the plugin

## Issue Reporting

### Before Reporting

- Check existing [issues](https://github.com/nextgis/qgis_devtools/issues) to avoid duplicates
- Ensure you're using the [latest plugin version](https://plugins.qgis.org/plugins/devtools/#plugin-versions)
- Gather relevant information (QGIS version, OS, plugin version, logs)

### Bug Reports

Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- QGIS version information (Help → About → copy table)
- Relevant log messages from QGIS Log Messages panel
- Screenshots or recordings if applicable

### Feature Requests

Include:

- Clear description of the proposed feature
- Use case and motivation
- Possible implementation approach
- Any relevant examples or mockups

## Pull Request Process

### Before Submitting

1. **Ensure your changes work**:
   - Build and test the plugin thoroughly
   - Check that existing functionality isn't broken
   - Verify code follows style guidelines

2. **Update documentation** if needed:
   - Update docstrings for new/changed functions
   - Update README.md if adding major features
   - Add or update comments for complex code

3. **Check dependencies**:
   - Avoid adding new dependencies unless absolutely necessary
   - Ensure compatibility with QGIS 3.22+

### Pull Request Guidelines

1. **Provide clear description** of changes and motivation
2. **Include verification steps** for reviewers
3. **Keep changes focused** - one feature/fix per PR
4. **When the original repository changes, perform a rebase to keep your branch up to date**

### Review Process

- Maintainers will review your PR and may request changes
- Address feedback by pushing new commits to your branch
- Once approved, maintainers will merge your PR
- Consider your PR a learning opportunity - feedback helps improve code quality

## Community and Support

### Getting Help

- **Documentation**: [User Guide](https://docs.nextgis.com/docs_ngqgis/source/devtools.html)
- **Issues**: [GitHub Issues](https://github.com/nextgis/qgis_devtools/issues)
- **Discord**: [NextGIS Discord](https://discord.gg/V3G9snXGy5)
- **Forum**: [NextGIS Community](https://community.nextgis.com/)
- **Telegram**: [NextGIS Talks](https://t.me/nextgis_talks)
- **Commercial Support**: [Contact NextGIS](https://nextgis.com/contact/?utm_source=github&utm_medium=contributing&utm_campaign=devtools)

### Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow GitHub's community guidelines

### Recognition

Contributors are recognized in:
- Git commit history
- Plugin credits (for significant contributions)
- Community acknowledgments

## Development Tips

### Troubleshooting Common Issues

**Translation compilation errors (`lrelease` not found)**:
- Install Qt Linguist tools (see Prerequisites section)
- Or skip translation compilation: `python setup.py bootstrap --ui --qrc`
- For distribution builds, translations should be compiled

### Debugging the Plugin

1. **Enable plugin debug messages**:
   - Settings → Options → QGIS DevTools → Enable plugin debug messages

2. **Remote Debugging**:
   - Use the plugin's own debugging capabilities
   - Set up VS Code with Python debugger
   - Connect to the debugpy server started by the plugin

### Working with QGIS APIs

- Refer to [QGIS API Documentation](https://qgis.org/pyqgis/)
- [QGIS Developer Guide](https://docs.qgis.org/latest/en/docs/developers_guide/index.html)
- [PyQGIS Developer Cookbook](https://docs.qgis.org/latest/en/docs/pyqgis_developer_cookbook/index.html)
- Use QGIS Python Console for API exploration
- Follow QGIS plugin development best practices

### Testing in Different Environments

- Test with different QGIS versions (3.22+)
- Test on different operating systems if possible
- Test with different plugin combinations

---

Thank you for contributing to QGIS DevTools! Your contributions help make QGIS plugin development easier for everyone.