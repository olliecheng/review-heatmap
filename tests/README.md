# Review Heatmap Testing Framework

This testing framework provides comprehensive utilities for testing the review-heatmap Anki add-on with custom collections and timezone configurations.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Testing Framework Components](#testing-framework-components)
- [Writing Tests](#writing-tests)
- [Fixtures](#fixtures)
- [Helpers](#helpers)
- [Running Tests](#running-tests)
- [Examples](#examples)

## Overview

The testing framework provides:

- **Anki Collection Management**: Create and configure test collections
- **Timezone Support**: Test with different timezone/rollover configurations
- **Test Data Generation**: Build collections with custom review history
- **ActivityReporter Testing**: Test the core `get_report()` functionality
- **Pytest Integration**: Full pytest support with fixtures and markers

## Installation

### 1. Install Dependencies

```bash
pip install -r tests/requirements.txt
```

This installs:
- `anki` - Core Anki functionality
- `aqt` - Anki Qt UI components
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- Additional testing utilities

### 2. Verify Installation

```bash
pytest --version
```

## Quick Start

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_activity_reporter.py
```

### Run Specific Test Class

```bash
pytest tests/test_activity_reporter.py::TestActivityReporterBasic
```

### Run Specific Test

```bash
pytest tests/test_activity_reporter.py::TestActivityReporterBasic::test_get_report_with_reviews
```

### Run with Coverage

```bash
pytest --cov=review_heatmap --cov-report=html
```

View coverage report by opening `htmlcov/index.html` in your browser.

## Testing Framework Components

### Directory Structure

```
tests/
├── __init__.py                          # Package initialization
├── conftest.py                          # Pytest fixtures and configuration
├── requirements.txt                     # Testing dependencies
├── README.md                            # This file
├── test_activity_reporter.py            # Example tests
└── test_helpers/                        # Testing utilities
    ├── __init__.py
    ├── collection_builder.py            # Build test collections
    └── timezone_utils.py                # Timezone testing helpers
```

### Key Files

- **conftest.py**: Pytest fixtures for collections, config, and reporters
- **collection_builder.py**: Fluent API for building test collections
- **timezone_utils.py**: Helpers for timezone-aware testing
- **test_activity_reporter.py**: Example test suite

## Writing Tests

### Basic Test Structure

```python
def test_example(anki_collection, config_manager):
    """Test example using fixtures."""
    # Create test data
    builder = CollectionBuilder(anki_collection)
    builder.add_deck("Test Deck")
    builder.add_cards_with_reviews(
        deck_name="Test Deck",
        num_cards=5,
        review_dates=["2024-01-01", "2024-01-02"],
        reviews_per_card=1
    )

    # Create reporter and get report
    reporter = ActivityReporter(anki_collection, config_manager)
    report = reporter.get_report()

    # Assertions
    assert report is not None
    assert len(report.activity) > 0
```

### Testing with Different Timezones

```python
def test_timezone_example(anki_collection_with_timezone, config_manager):
    """Test with specific timezone."""
    # Create collection with 6am rollover
    col = anki_collection_with_timezone(rollover_hour=6)

    builder = CollectionBuilder(col)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=1,
        review_dates=["2024-01-01"],
        reviews_per_card=1,
        rollover_hour=6
    )

    reporter = ActivityReporter(col, config_manager)
    report = reporter.get_report()

    assert report.offset == 6
    col.close()
```

### Using TimezoneHelper

```python
def test_with_timezone_helper(anki_collection, config_manager):
    """Test using TimezoneHelper utilities."""
    tz_helper = TimezoneHelper(rollover_hour=4)
    tz_helper.configure_collection_timezone(anki_collection)

    # Generate review dates
    dates = tz_helper.generate_review_dates(
        start_date="2024-01-01",
        num_days=10,
        skip_weekends=True
    )

    builder = CollectionBuilder(anki_collection)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=1,
        review_dates=dates,
        reviews_per_card=1,
        rollover_hour=4
    )

    reporter = ActivityReporter(anki_collection, config_manager)
    report = reporter.get_report()

    assert report is not None
```

## Fixtures

### Collection Fixtures

#### `anki_collection`

Creates a fresh Anki collection for testing.

```python
def test_example(anki_collection):
    assert anki_collection is not None
```

#### `anki_collection_with_timezone`

Factory fixture for creating collections with specific rollover hours.

```python
def test_example(anki_collection_with_timezone):
    col = anki_collection_with_timezone(rollover_hour=6)
    assert col.conf["rollover"] == 6
    col.close()
```

### Configuration Fixtures

#### `config_manager`

Creates a ConfigManager with default settings.

```python
def test_example(config_manager):
    assert config_manager is not None
```

### Reporter Fixtures

#### `activity_reporter`

Creates an ActivityReporter with default configuration.

```python
def test_example(activity_reporter):
    report = activity_reporter.get_report()
    assert report is not None
```

#### `activity_reporter_with_timezone`

Factory fixture for creating reporters with specific timezones.

```python
def test_example(activity_reporter_with_timezone):
    reporter = activity_reporter_with_timezone(rollover_hour=6)
    report = reporter.get_report()
    assert report.offset == 6
```

### Utility Fixtures

#### `temp_dir`

Provides a temporary directory for test files.

```python
def test_example(temp_dir):
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")
```

#### `fixed_timestamp`

Returns a fixed timestamp for reproducible tests.

```python
def test_example(fixed_timestamp):
    # Always returns timestamp for 2024-01-15 12:00:00 UTC
    assert fixed_timestamp == 1705320000
```

## Helpers

### CollectionBuilder

Fluent API for building test collections.

#### Methods

##### `add_deck(name, parent=None)`

Add a deck to the collection.

```python
builder = CollectionBuilder(col)
builder.add_deck("Main Deck")
builder.add_deck("Sub Deck", parent="Main Deck")
```

##### `add_note(deck_name, front, back)`

Add a single note/card.

```python
note = builder.add_note(
    deck_name="Test",
    front="Question",
    back="Answer"
)
```

##### `add_cards_with_reviews(deck_name, num_cards, review_dates, reviews_per_card=1, rollover_hour=4)`

Add multiple cards with review history.

```python
builder.add_cards_with_reviews(
    deck_name="Test",
    num_cards=10,
    review_dates=["2024-01-01", "2024-01-02", "2024-01-03"],
    reviews_per_card=2,
    rollover_hour=4
)
```

##### `add_due_cards(deck_name, num_cards, due_in_days)`

Add cards due in the future.

```python
builder.add_due_cards(
    deck_name="Test",
    num_cards=5,
    due_in_days=7
)
```

##### `set_rollover_hour(hour)`

Set the collection's rollover hour.

```python
builder.set_rollover_hour(6)
```

#### Helper Function

##### `create_sample_collection(col, timezone_offset=4, num_decks=2, cards_per_deck=10, review_days=30)`

Create a realistic test collection.

```python
builder = create_sample_collection(
    col=anki_collection,
    timezone_offset=4,
    num_decks=3,
    cards_per_deck=20,
    review_days=30
)
```

### TimezoneHelper

Helper for timezone-aware testing.

#### Methods

##### `configure_collection_timezone(col, rollover_hour)`

Configure a collection's timezone.

```python
tz_helper = TimezoneHelper(rollover_hour=4)
tz_helper.configure_collection_timezone(col, rollover_hour=6)
```

##### `get_day_start(date, rollover_hour=None)`

Get the start of a day according to Anki's rollover.

```python
day_start = tz_helper.get_day_start(datetime(2024, 1, 1))
```

##### `generate_review_dates(start_date, num_days, skip_weekends=False)`

Generate a list of review dates.

```python
dates = tz_helper.generate_review_dates(
    start_date="2024-01-01",
    num_days=30,
    skip_weekends=True
)
```

##### `create_dst_transition_dates()`

Get DST transition dates for testing.

```python
dst_dates = tz_helper.create_dst_transition_dates()
# Returns dict with "spring_forward_2024", "fall_back_2024", etc.
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Specific Markers

```bash
# Run only timezone tests
pytest -m timezone

# Run all except slow tests
pytest -m "not slow"
```

### Run with Coverage

```bash
pytest --cov=review_heatmap --cov-report=term-missing
```

### Run in Parallel (with pytest-xdist)

```bash
pip install pytest-xdist
pytest -n auto
```

## Examples

### Example 1: Basic Test

```python
def test_basic_report(anki_collection, config_manager):
    """Test basic report generation."""
    builder = CollectionBuilder(anki_collection)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=5,
        review_dates=["2024-01-01"],
        reviews_per_card=1
    )

    reporter = ActivityReporter(anki_collection, config_manager)
    report = reporter.get_report()

    assert report is not None
    assert sum(abs(v) for v in report.activity.values()) == 5
```

### Example 2: Timezone Test

```python
def test_multiple_timezones(anki_collection_with_timezone, config_manager):
    """Test with multiple timezone configurations."""
    rollover_hours = [0, 4, 6, 12]

    for hour in rollover_hours:
        col = anki_collection_with_timezone(rollover_hour=hour)

        builder = CollectionBuilder(col)
        builder.add_deck("Test")
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=1,
            review_dates=["2024-01-01"],
            reviews_per_card=1,
            rollover_hour=hour
        )

        reporter = ActivityReporter(col, config_manager)
        report = reporter.get_report()

        assert report.offset == hour
        col.close()
```

### Example 3: DST Transition Test

```python
def test_dst_transition(anki_collection, config_manager):
    """Test handling of DST transitions."""
    tz_helper = TimezoneHelper()
    dst_dates = tz_helper.create_dst_transition_dates()

    builder = CollectionBuilder(anki_collection)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=1,
        review_dates=dst_dates["spring_forward_2024"],
        reviews_per_card=1
    )

    reporter = ActivityReporter(anki_collection, config_manager)
    report = reporter.get_report()

    assert len(report.activity) >= 3
```

### Example 4: Using Sample Collection

```python
def test_sample_collection(anki_collection, config_manager):
    """Test using pre-built sample collection."""
    builder = create_sample_collection(
        col=anki_collection,
        timezone_offset=4,
        num_decks=2,
        cards_per_deck=15,
        review_days=30
    )

    reporter = ActivityReporter(anki_collection, config_manager)
    report = reporter.get_report()

    # Should have both historical reviews and forecast
    assert report is not None
    assert len(report.activity) > 0

    historical = [v for v in report.activity.values() if v > 0]
    forecast = [v for v in report.activity.values() if v < 0]

    assert len(historical) > 0
    assert len(forecast) > 0
```

### Example 5: Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("rollover_hour,num_cards", [
    (0, 5),
    (4, 10),
    (6, 15),
    (12, 20),
])
def test_parametrized(anki_collection_with_timezone, config_manager, rollover_hour, num_cards):
    """Test with various parameter combinations."""
    col = anki_collection_with_timezone(rollover_hour=rollover_hour)

    builder = CollectionBuilder(col)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=num_cards,
        review_dates=["2024-01-01"],
        reviews_per_card=1,
        rollover_hour=rollover_hour
    )

    reporter = ActivityReporter(col, config_manager)
    report = reporter.get_report()

    assert report is not None
    assert report.offset == rollover_hour

    col.close()
```

## Best Practices

1. **Always close collections**: When using `anki_collection_with_timezone`, remember to call `col.close()` after use
2. **Use fixtures**: Leverage the provided fixtures instead of creating collections manually
3. **Isolate tests**: Each test should be independent and not rely on state from other tests
4. **Clear test names**: Use descriptive test names that explain what is being tested
5. **Test edge cases**: Include tests for DST transitions, timezone boundaries, empty collections, etc.
6. **Use parametrized tests**: For testing multiple configurations, use `@pytest.mark.parametrize`

## Troubleshooting

### Collection Not Found Error

Make sure you've called `add_deck()` before trying to add cards:

```python
builder.add_deck("Test Deck")
builder.add_cards_with_reviews(deck_name="Test Deck", ...)
```

### Timezone Issues

Ensure you're using the same `rollover_hour` when creating reviews and configuring the collection:

```python
builder.add_cards_with_reviews(
    rollover_hour=6  # Must match collection rollover
)
```

### Import Errors

Make sure all dependencies are installed:

```bash
pip install -r tests/requirements.txt
```

## Contributing

When adding new tests:

1. Follow the existing test structure
2. Add docstrings to test functions
3. Use appropriate fixtures
4. Add markers if needed (`@pytest.mark.slow`, etc.)
5. Update this README with new examples if applicable

## License

This testing framework is part of review-heatmap and follows the same license (GNU AGPLv3).
