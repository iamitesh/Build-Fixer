# Contributing to Build-Fixer

Thank you for your interest in contributing to Build-Fixer! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the community
- Show empathy towards others

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check existing issues to avoid duplicates
2. Collect information about the bug
3. Include steps to reproduce

When creating a bug report, include:
- Clear, descriptive title
- Detailed steps to reproduce
- Expected vs actual behavior
- Environment details (Node.js version, OS, etc.)
- Build logs or error messages
- Screenshots if applicable

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion:
- Use a clear, descriptive title
- Provide detailed description of the proposed functionality
- Explain why this enhancement would be useful
- List any alternatives you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run syntax checks: `node --check src/**/*.js`
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

#### Pull Request Guidelines

- Follow existing code style
- Write clear commit messages
- Update README.md if needed
- Add examples for new features
- Test your changes thoroughly

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/Build-Fixer.git
cd Build-Fixer

# Install dependencies
npm install

# Copy environment example
cp .env.example .env
# Edit .env with your credentials

# Test the CLI
node src/index.js --help
```

## Project Structure

```
Build-Fixer/
├── src/
│   ├── index.js              # CLI entry point
│   ├── buildFixer.js         # Main orchestrator
│   ├── services/             # Service integrations
│   │   ├── s3Service.js
│   │   ├── bedrockService.js
│   │   └── azureDevOpsService.js
│   └── utils/                # Utilities
│       └── helpers.js
├── examples/                 # Usage examples
├── docs/                     # Documentation
└── tests/                    # Tests (future)
```

## Coding Standards

### JavaScript Style Guide

- Use `const` and `let`, avoid `var`
- Use meaningful variable names
- Add JSDoc comments for functions
- Handle errors appropriately
- Use async/await for asynchronous code
- Keep functions focused and small

### Example Function Documentation

```javascript
/**
 * Upload build log file to S3
 * @param {string} logContent - The build log content
 * @param {string} buildId - The build ID for naming the file
 * @returns {Promise<string>} - The S3 key of the uploaded file
 * @throws {Error} - If upload fails
 */
async uploadLog(logContent, buildId) {
  // Implementation
}
```

## Testing

Currently, the project doesn't have automated tests. If you'd like to add tests:

1. Use a testing framework (Jest, Mocha, etc.)
2. Test individual services with mocked dependencies
3. Add integration tests for the full workflow
4. Update package.json with test scripts

Example test structure:
```
tests/
├── unit/
│   ├── s3Service.test.js
│   ├── bedrockService.test.js
│   └── azureDevOpsService.test.js
└── integration/
    └── buildFixer.test.js
```

## Documentation

When adding features:
- Update README.md
- Add examples to examples/ directory
- Update ARCHITECTURE.md if adding new components
- Add inline code comments for complex logic

## Release Process

(For maintainers)

1. Update version in package.json
2. Update CHANGELOG.md
3. Create a git tag: `git tag -a v1.0.0 -m "Version 1.0.0"`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release

## Areas for Contribution

### High Priority
- [ ] Add automated tests
- [ ] Add support for GitHub Actions
- [ ] Create web dashboard
- [ ] Add more AI providers (OpenAI, Azure OpenAI)
- [ ] Implement caching for common errors

### Medium Priority
- [ ] Add Slack/Teams notifications
- [ ] Create Docker image
- [ ] Add metrics and monitoring
- [ ] Support more log formats
- [ ] Add batch processing

### Low Priority
- [ ] Add web UI for configuration
- [ ] Create VS Code extension
- [ ] Add auto-fix capabilities
- [ ] Machine learning for pattern detection

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Reach out to maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Build-Fixer! 🎉
