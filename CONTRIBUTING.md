# Contributing to LAQ RAG

We welcome contributions from the community! This document outlines the process for contributing to the LAQ RAG project.

## Development Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama with Mistral and nomic-embed-text models
- Git

### Local Development
1. Fork and clone the repository
2. Set up backend:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   cp ../.env.example .env
   ```
3. Set up frontend:
   ```bash
   cd ../frontend
   npm install
   cp .env.example .env
   ```
4. Start Ollama and pull models:
   ```bash
   ollama pull mistral
   ollama pull nomic-embed-text
   ```
5. Run the application:
   ```bash
   # Terminal 1 - Backend
   cd backend && uvicorn app.main:app --reload

   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

## Code Standards

### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Write comprehensive docstrings
- Maximum line length: 88 characters (Black formatter)
- Use meaningful variable and function names

### JavaScript/React (Frontend)
- Use ESLint and Prettier for code formatting
- Follow React best practices
- Use functional components with hooks
- Implement proper error boundaries

### General
- Write clear, concise commit messages
- Use conventional commit format: `type(scope): description`
- Keep pull requests focused on single features/bugs

## Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Test Coverage Requirements
- Backend: Minimum 80% coverage
- Frontend: Minimum 70% coverage
- All new features must include corresponding tests

## Pull Request Process

1. **Create Feature Branch**: `git checkout -b feature/your-feature-name`
2. **Make Changes**: Implement your feature or fix
3. **Run Tests**: Ensure all tests pass and coverage meets requirements
4. **Update Documentation**: Add/update docs for any new features
5. **Commit Changes**: Use clear, descriptive commit messages
6. **Push Branch**: Push your branch to your fork
7. **Create PR**: Open a pull request with:
   - Clear description of changes
   - Reference to any related issues
   - Screenshots/videos for UI changes
   - Test results

## Code Review Guidelines

### For Reviewers
- Check for security vulnerabilities
- Verify test coverage and quality
- Ensure code follows project standards
- Test the changes locally when possible
- Provide constructive feedback

### For Contributors
- Address all review comments
- Don't take feedback personally
- Ask for clarification if needed
- Keep discussions focused and professional

## Issue Reporting

### Bug Reports
- Use the bug report template
- Include detailed steps to reproduce
- Provide system information (OS, Python/Node versions)
- Attach relevant logs or error messages

### Feature Requests
- Use the feature request template
- Describe the problem you're trying to solve
- Explain why the feature would be valuable
- Consider alternative solutions

## Security

- Never commit sensitive information
- Report security vulnerabilities privately via email
- See SECURITY.md for details

## Documentation

- Update README.md for significant changes
- Add API documentation for new endpoints
- Update architecture docs for structural changes
- Maintain CHANGELOG.md with version updates

## Commit Message Guidelines

```
type(scope): description

[optional body]

[optional footer]
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples
```
feat(auth): add OAuth2 authentication support
fix(api): handle empty search queries gracefully
docs(readme): update installation instructions
test(pdf): add tests for PDF processing pipeline
```

## Release Process

1. Update version in relevant files
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Tag release
6. Deploy to production
7. Announce release

## Community Guidelines

- Be respectful and inclusive
- Help newcomers learn and contribute
- Keep discussions constructive
- Follow the code of conduct

## Getting Help

- Check existing issues and documentation first
- Use discussions for questions
- Join our community chat for real-time help
- Contact maintainers for urgent matters

Thank you for contributing to LAQ RAG! 🎉
