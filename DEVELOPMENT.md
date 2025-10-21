# Development Guide

This guide covers how to set up a development environment and run tests for the review-heatmap add-on.

## Prerequisites

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## Setting Up Development Environment

### Using uv (Recommended)

#### 1. Install Test Dependencies

```bash
# Install the project with test dependencies
uv pip install --system -e ".[test]"
```

#### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=review_heatmap --cov-report=html

# Run specific test file
pytest tests/test_activity_reporter.py

# Run specific test
pytest tests/test_activity_reporter.py::TestActivityReporterBasic::test_get_report_empty_collection
```

#### 3. Install Build Dependencies (for building the add-on)

```bash
uv pip install --system -e ".[build]"
```

#### 4. Install All Dependencies (build + test)

```bash
uv pip install --system -e ".[dev]"
```

### Using pip (Traditional)

```bash
# Install test dependencies
pip install -e ".[test]"

# Or using the requirements file
pip install -r tests/requirements.txt
```

## Running Tests

### Basic Usage

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run tests with coverage
pytest --cov=review_heatmap --cov-report=term-missing
pytest --cov=review_heatmap --cov-report=html  # Generate HTML report
```

### Test Markers

The test suite uses markers to categorize tests:

```bash
# Run only timezone tests
pytest -m timezone

# Run all except slow tests
pytest -m "not slow"

# Run integration tests only
pytest -m integration
```

### Test Collection Builder Script

Generate test Anki collections with hourly review data:

```bash
python tests/test_helpers/collection_builder.py --output test_collection.anki2
```

This creates a collection with:
- 1 test card
- 10,273 reviews (one per hour from Dec 1, 2023 to Feb 1, 2025 UTC)

## Project Structure

```
review-heatmap/
├── src/
│   └── review_heatmap/        # Main add-on code
│       ├── __init__.py
│       ├── activity.py        # ActivityReporter and core logic
│       ├── controller.py
│       ├── renderer.py
│       └── ...
├── tests/
│   ├── conftest.py            # Pytest fixtures
│   ├── test_activity_reporter.py
│   ├── test_helpers/
│   │   ├── collection_builder.py  # Test data generator script
│   │   └── timezone_utils.py      # Timezone testing utilities
│   └── ...
├── pyproject.toml             # Project configuration and dependencies
└── pytest.ini                 # Pytest configuration (legacy, use pyproject.toml)
```

## Configuration Files

### pyproject.toml

The main project configuration file that includes:
- Project metadata
- Dependencies (build, test, dev)
- Pytest configuration
- Coverage configuration
- Ruff (linter) configuration

### Dependency Groups

- `test` - Dependencies for running tests (anki, aqt, pytest, etc.)
- `build` - Dependencies for building the add-on (aab)
- `dev` - All dependencies (test + build)

## Common Development Tasks

### Install for Development

```bash
# Install in editable mode with test dependencies
uv pip install --system -e ".[dev]"
```

### Run Tests with Coverage

```bash
pytest --cov=review_heatmap --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Generate Test Data

```bash
python tests/test_helpers/collection_builder.py --output my_test.anki2
```

### Run Specific Tests

```bash
# Run tests in a specific file
pytest tests/test_activity_reporter.py

# Run a specific test class
pytest tests/test_activity_reporter.py::TestActivityReporterBasic

# Run a specific test method
pytest tests/test_activity_reporter.py::TestActivityReporterBasic::test_get_report_with_reviews
```

### Run Tests with Different Python Versions

```bash
# Using uv (automatically handles Python versions)
uv pip install --system -e ".[test]"
pytest

# Or manually with different Python interpreters
python3.9 -m pytest
python3.10 -m pytest
python3.11 -m pytest
```

## Troubleshooting

### ModuleNotFoundError: No module named 'review_heatmap'

Install the package in editable mode:
```bash
uv pip install --system -e ".[test]"
```

### PyQt6 GUI Errors

The tests require PyQt6 for Anki. If you encounter GUI-related errors in headless environments:

1. Install xvfb (Linux):
   ```bash
   sudo apt-get install xvfb
   xvfb-run pytest
   ```

2. Or use the demo framework instead:
   ```bash
   python tests/demo_framework.py
   ```

### Import Errors for Anki/AQT

Make sure you have the test dependencies installed:
```bash
uv pip install --system -e ".[test]"
```

## Linting and Formatting

The project uses Ruff for linting. Configuration is in `pyproject.toml`.

```bash
# Install ruff
uv pip install --system ruff

# Run linting
ruff check src/ tests/

# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

## Building the Add-on

```bash
# Install build dependencies
uv pip install --system -e ".[build]"

# Build the add-on (if aab is configured)
# Follow aab documentation for building
```

## Additional Resources

- [Project README](README.md)
- [Test Framework Documentation](tests/README.md)
- [Test Helpers Documentation](tests/test_helpers/README.md)
- [Anki Add-on Development](https://addon-docs.ankiweb.net/)
- [uv Documentation](https://github.com/astral-sh/uv)

## Contributing

When contributing:

1. Install dev dependencies: `uv pip install --system -e ".[dev]"`
2. Run tests before committing: `pytest`
3. Ensure tests pass and coverage is maintained
4. Follow the existing code style (enforced by Ruff)
5. Update tests for new functionality

## License

GNU Affero General Public License v3.0 or later (AGPL-3.0-or-later)
