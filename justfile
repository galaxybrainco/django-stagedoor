# Django-stagedoor development commands

# Show available commands
default:
    @just --list

# Install dependencies
install:
    uv sync --group dev

# Run tests with coverage (pass additional args to pytest)
test *args="":
    pytest --cov=stagedoor --cov-report=term-missing --cov-report=html {{ args }}

htmlcov:
    open htmlcov/index.html

# Run linting
lint:
    ruff check src/

# Format code
format:
    ruff format src/

# Run type checking
typecheck:
    mypy src/

# Run all code quality checks
check: lint typecheck

# Clean up build artifacts
clean:
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf .pytest_cache/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
