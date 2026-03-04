# Contributing to Timehash

Thank you for your interest in contributing to Timehash! This document provides guidelines for contributing to the project.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/naver/timehash/issues)
2. If not, create a new issue with:
   - Clear description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment (language, version, OS)

### Suggesting Features

1. Check if the feature has already been suggested
2. Create an issue describing:
   - The use case
   - Why it would be useful
   - How it might be implemented

### Submitting Code

1. **Fork the repository**
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**:
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed
4. **Test your changes**: Run tests for the language you're modifying
5. **Commit your changes**: Use clear, descriptive commit messages
6. **Push to your fork**: `git push origin feature/your-feature-name`
7. **Create a Pull Request**

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Add docstrings for public functions

### Java
- Follow Google Java Style Guide
- Add Javadoc comments
- Use meaningful variable names

### Go
- Follow [Effective Go](https://golang.org/doc/effective_go.html)
- Run `gofmt` before committing
- Add comments for exported functions

### JavaScript
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use ES6+ features
- Add JSDoc comments

### C++
- Follow Google C++ Style Guide
- Use meaningful variable names
- Add comments for complex logic

## Testing

- All new features must include tests
- Tests should cover edge cases
- Ensure all existing tests pass

## Documentation

- Update README.md if adding new features
- Add examples for new functionality
- Keep code comments up to date

## Language-Specific Guidelines

### Adding Support for a New Language

1. Create a new directory for the language
2. Implement the core Timehash class/struct
3. Add tests
4. Add README with usage examples
5. Update main README.md

### Maintaining Consistency

- All language implementations should produce the same keys for the same inputs
- API should be consistent across languages (naming conventions may differ)
- Tests should verify cross-language compatibility

## Questions?

Feel free to open an issue for questions or discussions!
