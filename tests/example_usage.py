#!/usr/bin/env python3
"""
Example script demonstrating the review-heatmap testing framework.

This script shows how to:
1. Create a custom Anki collection
2. Configure timezone settings
3. Add review data
4. Call ActivityReporter.get_report()
5. Inspect the results

Run with: python tests/example_usage.py
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path to import review_heatmap
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from anki.collection import Collection

from review_heatmap.activity import ActivityReporter, ActivityType
from review_heatmap.config import ConfigManager, config_defaults
from tests.test_helpers.collection_builder import CollectionBuilder, create_sample_collection
from tests.test_helpers.timezone_utils import TimezoneHelper


def example_basic_usage():
    """Example: Basic usage of the testing framework."""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)

    # Create a temporary directory for the collection
    with tempfile.TemporaryDirectory(prefix="anki_test_") as tmpdir:
        collection_path = Path(tmpdir) / "collection.anki2"

        # Create collection
        col = Collection(str(collection_path))

        # Create config manager
        config = ConfigManager(
            mw=None,  # type: ignore
            local=config_defaults["profile"].copy(),
            synced=config_defaults["synced"].copy()
        )

        # Build test data
        builder = CollectionBuilder(col)
        builder.add_deck("Japanese")
        builder.add_cards_with_reviews(
            deck_name="Japanese",
            num_cards=10,
            review_dates=["2024-01-01", "2024-01-02", "2024-01-03"],
            reviews_per_card=2
        )

        # Create reporter and get report
        reporter = ActivityReporter(col, config)
        report = reporter.get_report()

        # Display results
        print(f"Report generated: {report is not None}")
        print(f"Today's timestamp: {report.today}")
        print(f"Rollover offset: {report.offset} hours")
        print(f"Activity days: {len(report.activity)}")
        print(f"Total reviews: {sum(abs(v) for v in report.activity.values())}")
        print(f"Stats available: {report.stats is not None}")

        if report.stats:
            print(f"Max streak: {report.stats.streak_max}")
            print(f"Current streak: {report.stats.streak_cur}")
            print(f"Days active: {report.stats.pct_days_active}")
            print(f"Daily average: {report.stats.activity_daily_avg}")

        col.close()
    print()


def example_custom_timezone():
    """Example: Using a custom timezone configuration."""
    print("=" * 60)
    print("Example 2: Custom Timezone (6am rollover)")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="anki_test_") as tmpdir:
        collection_path = Path(tmpdir) / "collection.anki2"
        col = Collection(str(collection_path))

        # Configure timezone with 6am rollover
        tz_helper = TimezoneHelper(rollover_hour=6)
        tz_helper.configure_collection_timezone(col, rollover_hour=6)

        config = ConfigManager(
            mw=None,  # type: ignore
            local=config_defaults["profile"].copy(),
            synced=config_defaults["synced"].copy()
        )

        # Build test data
        builder = CollectionBuilder(col)
        builder.add_deck("Spanish")

        # Generate weekday review dates
        review_dates = tz_helper.generate_review_dates(
            start_date="2024-01-01",
            num_days=14,
            skip_weekends=True  # Only weekdays
        )

        builder.add_cards_with_reviews(
            deck_name="Spanish",
            num_cards=5,
            review_dates=review_dates,
            reviews_per_card=3,
            rollover_hour=6
        )

        # Get report
        reporter = ActivityReporter(col, config)
        report = reporter.get_report()

        print(f"Rollover hour: {report.offset}")
        print(f"Review dates (first 5): {review_dates[:5]}")
        print(f"Total activity days: {len(report.activity)}")
        print(f"Total reviews: {sum(abs(v) for v in report.activity.values())}")

        col.close()
    print()


def example_with_forecast():
    """Example: Testing with forecast (due cards)."""
    print("=" * 60)
    print("Example 3: With Forecast Data")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="anki_test_") as tmpdir:
        collection_path = Path(tmpdir) / "collection.anki2"
        col = Collection(str(collection_path))

        config = ConfigManager(
            mw=None,  # type: ignore
            local=config_defaults["profile"].copy(),
            synced=config_defaults["synced"].copy()
        )

        # Build test data with both history and forecast
        builder = CollectionBuilder(col)
        builder.add_deck("German")

        # Add historical reviews
        builder.add_cards_with_reviews(
            deck_name="German",
            num_cards=10,
            review_dates=["2024-01-01", "2024-01-02"],
            reviews_per_card=1
        )

        # Add future due cards
        builder.add_due_cards(
            deck_name="German",
            num_cards=15,
            due_in_days=7
        )

        # Get report with forecast
        reporter = ActivityReporter(col, config)
        report = reporter.get_report(limhist=30, limfcst=30)

        # Separate historical and forecast data
        historical = {k: v for k, v in report.activity.items() if v > 0}
        forecast = {k: v for k, v in report.activity.items() if v < 0}

        print(f"Historical days: {len(historical)}")
        print(f"Historical reviews: {sum(historical.values())}")
        print(f"Forecast days: {len(forecast)}")
        print(f"Forecast cards: {abs(sum(forecast.values()))}")

        col.close()
    print()


def example_sample_collection():
    """Example: Using the sample collection helper."""
    print("=" * 60)
    print("Example 4: Using Sample Collection Helper")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="anki_test_") as tmpdir:
        collection_path = Path(tmpdir) / "collection.anki2"
        col = Collection(str(collection_path))

        config = ConfigManager(
            mw=None,  # type: ignore
            local=config_defaults["profile"].copy(),
            synced=config_defaults["synced"].copy()
        )

        # Create a realistic sample collection
        builder = create_sample_collection(
            col=col,
            timezone_offset=4,
            num_decks=3,
            cards_per_deck=20,
            review_days=30
        )

        # Get report
        reporter = ActivityReporter(col, config)
        report = reporter.get_report()

        print(f"Sample collection created with 3 decks")
        print(f"Total activity days: {len(report.activity)}")
        print(f"Total reviews: {sum(abs(v) for v in report.activity.values() if v > 0)}")
        print(f"Total forecast: {abs(sum(v for v in report.activity.values() if v < 0))}")

        if report.stats:
            print(f"\nStatistics:")
            print(f"  Max streak: {report.stats.streak_max}")
            print(f"  Current streak: {report.stats.streak_cur}")
            print(f"  % Days active: {report.stats.pct_days_active}")

        col.close()
    print()


def example_activity_types():
    """Example: Testing different activity types."""
    print("=" * 60)
    print("Example 5: Different Activity Types")
    print("=" * 60)

    with tempfile.TemporaryDirectory(prefix="anki_test_") as tmpdir:
        collection_path = Path(tmpdir) / "collection.anki2"
        col = Collection(str(collection_path))

        config = ConfigManager(
            mw=None,  # type: ignore
            local=config_defaults["profile"].copy(),
            synced=config_defaults["synced"].copy()
        )

        builder = CollectionBuilder(col)
        builder.add_deck("Test")
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=10,
            review_dates=["2024-01-01", "2024-01-02"],
            reviews_per_card=5
        )

        reporter = ActivityReporter(col, config)

        # Test with reviews activity type
        report_reviews = reporter.get_report(activity_type=ActivityType.reviews)
        total_reviews = sum(abs(v) for v in report_reviews.activity.values())

        # Test with time activity type
        report_time = reporter.get_report(activity_type=ActivityType.time)
        total_time = sum(abs(v) for v in report_time.activity.values())

        print(f"Activity type: reviews")
        print(f"  Total count: {total_reviews}")
        print()
        print(f"Activity type: time")
        print(f"  Total time: {total_time} ms")

        col.close()
    print()


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 58 + "║")
    print("║" + "  Review-Heatmap Testing Framework Examples".center(58) + "║")
    print("║" + " " * 58 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    example_basic_usage()
    example_custom_timezone()
    example_with_forecast()
    example_sample_collection()
    example_activity_types()

    print("=" * 60)
    print("All examples completed successfully!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Run the test suite: pytest")
    print("  2. See tests/README.md for more information")
    print("  3. Check tests/test_activity_reporter.py for test examples")
    print()


if __name__ == "__main__":
    main()
