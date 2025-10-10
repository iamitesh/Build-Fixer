# Contributing to Build-Fixer

Thank you for your interest in contributing to Build-Fixer! This document provides guidelines and instructions for contributing.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- AWS account (for testing S3 and Bedrock features)
- Azure DevOps account (for testing work item creation)

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/Build-Fixer.git
   cd Build-Fixer
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables (see [SETUP.md](SETUP.md))

## Development Guidelines

### Code Style

- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings to all functions and classes
- Keep functions focused and single-purpose

### Code Organization

```
build_fixer/
├── __init__.py              # Package initialization
├── config_manager.py        # Configuration management
├── s3_manager.py           # S3 operations
├── bedrock_analyzer.py     # AI analysis
├── azure_devops_manager.py # Azure DevOps integration
└── main.py                 # Main orchestrator
```

### Adding New Features

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Test your changes thoroughly

4. Commit with descriptive messages:
   ```bash
   git commit -m "Add feature: description of your feature"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request

### Testing

Before submitting a PR, ensure:

1. **Import Test**: All modules can be imported without errors
   ```bash
   python -c "from build_fixer.main import BuildFixer; print('OK')"
   ```

2. **Syntax Check**: No Python syntax errors
   ```bash
   python -m py_compile build_fixer/*.py
   ```

3. **CLI Test**: The command-line interface works
   ```bash
   python -m build_fixer.main --help
   ```

4. **Integration Test** (if you have credentials configured):
   ```bash
   python -m build_fixer.main examples/sample_build_failure.log --verbose
   ```

## What to Contribute

### High-Priority Items

- Unit tests for all modules
- Integration tests
- Additional AI model support
- Support for other CI/CD platforms (GitHub Actions, Jenkins, etc.)
- Enhanced error handling and retry logic
- Metrics and monitoring integration
- Cost optimization features

### Documentation Improvements

- Additional examples
- Tutorial videos
- Troubleshooting guides
- Best practices documentation

### Bug Fixes

- Check the [Issues](https://github.com/iamitesh/Build-Fixer/issues) page
- Fix bugs and submit PRs with test cases

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the SETUP.md if you add new dependencies or configuration
3. Add your changes to the CHANGELOG.md (if it exists)
4. Ensure your PR description clearly describes the problem and solution
5. Reference any related issues in your PR description

## Code Review Process

- PRs require at least one approval from a maintainer
- Address all review comments
- Keep PRs focused on a single feature or fix
- Squash commits before merging if requested

## Reporting Bugs

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**:
   - OS and version
   - Python version
   - Relevant dependency versions
6. **Logs**: Include relevant error messages or logs

## Feature Requests

When requesting features:

1. **Use Case**: Describe your use case
2. **Proposed Solution**: How you envision the feature working
3. **Alternatives**: Alternative solutions you've considered
4. **Impact**: Who would benefit from this feature

## Community Guidelines

- Be respectful and inclusive
- Help others in discussions
- Provide constructive feedback
- Credit others for their work

## Questions?

- Open an [Issue](https://github.com/iamitesh/Build-Fixer/issues) for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Build-Fixer! 🚀
