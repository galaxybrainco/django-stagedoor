# Pre-commit Configuration for Django Stagedoor

This project uses pre-commit hooks to maintain code quality and consistency.

## Setup

1. Install pre-commit (already included in dev dependencies):

   ```bash
   uv sync
   ```

2. Install the pre-commit hooks:

   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

3. (Optional) Run against all files:
   ```bash
   pre-commit run --all-files
   ```

## Included Hooks

### Code Quality

- **Ruff**: Fast Python linter and formatter (replaces Black, isort, and many flake8 plugins)
- **MyPy**: Static type checking with Django stubs support
- **Bandit**: Security vulnerability scanning

### General Checks

- File size limits (1MB max)
- Python syntax validation
- JSON/YAML/TOML validation
- Merge conflict detection
- Private key detection
- Debug statement detection
- Branch protection (prevents direct commits to main/master)

### Documentation

- **Pydocstyle**: Enforces Google-style docstrings
- **Prettier**: Formats Markdown, YAML, and JSON files

### Commit Standards

- **Commitizen**: Enforces conventional commit messages for semantic versioning

## Commit Message Format

This project follows [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or modifying tests
- `chore`: Maintenance tasks
- `ci`: CI/CD changes

Example:

```
feat(auth): add two-factor authentication

Implements TOTP-based 2FA for user accounts with QR code generation
and backup codes.

Closes #123
```

## Bypassing Hooks

If you need to bypass pre-commit hooks (not recommended):

```bash
git commit --no-verify
```

## Updating Hooks

Pre-commit hooks are automatically updated weekly via CI. To manually update:

```bash
pre-commit autoupdate
```

## Troubleshooting

### MyPy Issues

MyPy is configured to not fail the pre-commit check (only warn) since it requires all dependencies to be installed. Run it manually for full type checking:

```bash
mypy src/
```

### Large Files

If you need to commit a large file, either:

1. Add it to `.gitattributes` with `filter=lfs`
2. Increase the limit in `.pre-commit-config.yaml`
3. Use `--no-verify` for that specific commit

### License Headers

The license header hook is set to manual mode. Run it explicitly if needed:

```bash
pre-commit run insert-license --all-files
```
