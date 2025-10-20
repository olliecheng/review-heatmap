"""
Pytest configuration and shared fixtures for review-heatmap tests.

This module provides:
- Anki collection initialization fixtures
- Timezone configuration fixtures
- ActivityReporter test fixtures
- Temporary profile/collection management
"""

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

import pytest
from anki.collection import Collection
from anki.utils import int_time

from review_heatmap.activity import ActivityReporter
from review_heatmap.config import ConfigManager


@pytest.fixture
def temp_dir() -> Iterator[Path]:
    """Create a temporary directory for test collections."""
    tmpdir = tempfile.mkdtemp(prefix="anki_test_")
    try:
        yield Path(tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


@pytest.fixture
def anki_collection(temp_dir: Path) -> Iterator[Collection]:
    """
    Create a fresh Anki collection for testing.

    The collection is created with default settings and cleaned up after the test.

    Yields:
        Collection: An initialized Anki collection
    """
    collection_path = temp_dir / "collection.anki2"

    # Create collection
    col = Collection(str(collection_path))

    try:
        yield col
    finally:
        col.close()


@pytest.fixture
def anki_collection_with_timezone(temp_dir: Path):
    """
    Factory fixture to create Anki collections with specific timezone offsets.

    Returns a function that creates a collection with a given rollover hour.

    Usage:
        col = anki_collection_with_timezone(rollover_hour=4)

    Args:
        rollover_hour: Hour of day when new day starts (0-23)
    """
    def _create_collection(rollover_hour: int = 4) -> Collection:
        collection_path = temp_dir / f"collection_tz{rollover_hour}.anki2"
        col = Collection(str(collection_path))

        # Set the rollover hour (scheduler v2+)
        col.conf["rollover"] = rollover_hour
        col.save()

        return col

    return _create_collection


@pytest.fixture
def config_manager(temp_dir: Path) -> ConfigManager:
    """
    Create a ConfigManager instance for testing.

    Returns:
        ConfigManager: Initialized config manager with default settings
    """
    # Create a minimal config manager
    # Note: In real usage, this would be initialized by the add-on
    from review_heatmap.config import config_defaults

    config = ConfigManager(
        mw=None,  # type: ignore
        local=config_defaults["profile"].copy(),
        synced=config_defaults["synced"].copy()
    )

    return config


@pytest.fixture
def activity_reporter(anki_collection: Collection, config_manager: ConfigManager) -> ActivityReporter:
    """
    Create an ActivityReporter instance for testing.

    Args:
        anki_collection: The collection fixture
        config_manager: The config manager fixture

    Returns:
        ActivityReporter: Initialized activity reporter
    """
    return ActivityReporter(anki_collection, config_manager)


@pytest.fixture
def activity_reporter_with_timezone(anki_collection_with_timezone, config_manager: ConfigManager):
    """
    Factory fixture to create ActivityReporter with specific timezone.

    Usage:
        reporter = activity_reporter_with_timezone(rollover_hour=2)

    Args:
        rollover_hour: Hour when new day starts (0-23)
    """
    def _create_reporter(rollover_hour: int = 4) -> ActivityReporter:
        col = anki_collection_with_timezone(rollover_hour)
        return ActivityReporter(col, config_manager)

    return _create_reporter


@pytest.fixture
def utc_timestamp() -> int:
    """Get current UTC timestamp in seconds."""
    return int_time()


@pytest.fixture
def fixed_timestamp() -> int:
    """
    Get a fixed timestamp for reproducible tests.

    Returns:
        int: Unix timestamp for 2024-01-15 12:00:00 UTC
    """
    dt = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    return int(dt.timestamp())
