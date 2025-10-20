"""
Tests for ActivityReporter.get_report() functionality.

This module demonstrates how to use the testing framework to test
the ActivityReporter with custom collections and timezone configurations.
"""

from datetime import datetime, timezone

import pytest
from anki.collection import Collection

from review_heatmap.activity import ActivityReporter, ActivityType
from review_heatmap.config import ConfigManager
from tests.test_helpers.collection_builder import CollectionBuilder, create_sample_collection
from tests.test_helpers.timezone_utils import TimezoneHelper, create_timezone_test_scenarios


class TestActivityReporterBasic:
    """Basic tests for ActivityReporter.get_report()."""

    def test_get_report_empty_collection(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() on an empty collection."""
        reporter = ActivityReporter(anki_collection, config_manager)

        report = reporter.get_report()

        assert report is not None
        assert report.activity == {}  # No activity in empty collection
        assert report.today > 0  # Should have a valid timestamp
        assert report.offset >= 0  # Should have a valid offset

    def test_get_report_with_reviews(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() with review history."""
        # Create test data
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test Deck")
        builder.add_cards_with_reviews(
            deck_name="Test Deck",
            num_cards=5,
            review_dates=["2024-01-01", "2024-01-02", "2024-01-03"],
            reviews_per_card=3
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        assert len(report.activity) > 0  # Should have activity data
        assert report.start is not None
        assert report.stop is not None

        # Verify we have the expected number of reviews
        total_reviews = sum(abs(count) for count in report.activity.values())
        assert total_reviews == 15  # 5 cards * 3 dates * 1 review per card

    def test_get_report_with_forecast(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() includes forecast for due cards."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test Deck")

        # Add cards due in the future
        builder.add_due_cards(
            deck_name="Test Deck",
            num_cards=10,
            due_in_days=7
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report(limfcst=30)

        assert report is not None
        # Should have negative counts for future due cards
        future_counts = [count for count in report.activity.values() if count < 0]
        assert len(future_counts) > 0

    def test_get_report_limit_history(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() with limited history."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test Deck")

        # Create 30 days of review history
        review_dates = [
            f"2024-01-{day:02d}" for day in range(1, 31)
        ]
        builder.add_cards_with_reviews(
            deck_name="Test Deck",
            num_cards=1,
            review_dates=review_dates,
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)

        # Get only last 7 days
        report = reporter.get_report(limhist=7)

        assert report is not None
        # Should have limited data (implementation dependent)

    def test_get_report_current_deck_only(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() filtered to current deck only."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Deck A")
        builder.add_deck("Deck B")

        builder.add_cards_with_reviews(
            deck_name="Deck A",
            num_cards=5,
            review_dates=["2024-01-01"],
            reviews_per_card=1
        )

        builder.add_cards_with_reviews(
            deck_name="Deck B",
            num_cards=3,
            review_dates=["2024-01-01"],
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)

        # Get report for all decks
        report_all = reporter.get_report(current_deck_only=False)

        # Note: current_deck_only filtering requires setting the current deck
        # This is typically done through the Anki UI
        # For now, we just verify the parameter is accepted
        assert report_all is not None


class TestActivityReporterTimezone:
    """Tests for timezone handling in ActivityReporter."""

    def test_different_rollover_hours(
        self,
        anki_collection_with_timezone,
        config_manager: ConfigManager
    ):
        """Test get_report() with different rollover hours."""
        scenarios = [0, 4, 6, 12]  # Different rollover hours

        for rollover_hour in scenarios:
            col = anki_collection_with_timezone(rollover_hour)

            builder = CollectionBuilder(col)
            builder.add_deck("Test")
            builder.add_cards_with_reviews(
                deck_name="Test",
                num_cards=1,
                review_dates=["2024-01-01"],
                reviews_per_card=1,
                rollover_hour=rollover_hour
            )

            reporter = ActivityReporter(col, config_manager)
            report = reporter.get_report()

            assert report is not None
            assert report.offset == rollover_hour

            col.close()

    def test_timezone_helper_integration(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test integration with TimezoneHelper."""
        tz_helper = TimezoneHelper(rollover_hour=6)
        tz_helper.configure_collection_timezone(anki_collection, rollover_hour=6)

        # Verify configuration
        assert anki_collection.conf["rollover"] == 6

        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=1,
            review_dates=["2024-01-01"],
            reviews_per_card=1,
            rollover_hour=6
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        assert report.offset == 6

    def test_dst_transition_dates(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() around DST transition dates."""
        tz_helper = TimezoneHelper(rollover_hour=4)
        dst_dates = tz_helper.create_dst_transition_dates()

        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")

        # Add reviews around spring DST transition
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=1,
            review_dates=dst_dates["spring_forward_2024"],
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        # Should handle DST transition correctly
        assert len(report.activity) >= 3


class TestActivityReporterStatistics:
    """Tests for statistics in ActivityReport."""

    def test_streak_calculation(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test streak statistics calculation."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")

        # Create a streak of 5 consecutive days
        review_dates = [f"2024-01-{day:02d}" for day in range(1, 6)]
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=1,
            review_dates=review_dates,
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        assert report.stats is not None
        # Streaks should be calculated based on review history

    def test_daily_average(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test daily average calculation."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")

        # Create consistent daily reviews
        review_dates = [f"2024-01-{day:02d}" for day in range(1, 11)]
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=1,
            review_dates=review_dates,
            reviews_per_card=5  # 5 reviews per day
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        assert report.stats is not None
        assert report.stats.activity_daily_avg is not None


class TestActivityReporterSampleCollection:
    """Tests using the sample collection helper."""

    def test_sample_collection_creation(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test creating and using a sample collection."""
        builder = create_sample_collection(
            col=anki_collection,
            timezone_offset=4,
            num_decks=3,
            cards_per_deck=10,
            review_days=30
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report()

        assert report is not None
        assert len(report.activity) > 0
        assert report.stats is not None

        # Should have both historical and forecast data
        historical = [count for count in report.activity.values() if count > 0]
        forecast = [count for count in report.activity.values() if count < 0]

        assert len(historical) > 0
        assert len(forecast) > 0


@pytest.mark.parametrize("scenario", create_timezone_test_scenarios())
def test_timezone_scenarios(
    scenario: dict,
    anki_collection_with_timezone,
    config_manager: ConfigManager
):
    """Test various timezone scenarios."""
    rollover_hour = scenario["rollover_hour"]

    col = anki_collection_with_timezone(rollover_hour)

    builder = CollectionBuilder(col)
    builder.add_deck("Test")
    builder.add_cards_with_reviews(
        deck_name="Test",
        num_cards=1,
        review_dates=["2024-01-01"],
        reviews_per_card=1,
        rollover_hour=rollover_hour
    )

    reporter = ActivityReporter(col, config_manager)
    report = reporter.get_report()

    assert report is not None, f"Failed for scenario: {scenario['name']}"
    assert report.offset == rollover_hour

    col.close()


class TestActivityReporterActivityTypes:
    """Tests for different activity types."""

    def test_reviews_activity_type(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() with reviews activity type."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=5,
            review_dates=["2024-01-01"],
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report(activity_type=ActivityType.reviews)

        assert report is not None
        assert len(report.activity) > 0

    def test_time_activity_type(
        self,
        anki_collection: Collection,
        config_manager: ConfigManager
    ):
        """Test get_report() with time activity type."""
        builder = CollectionBuilder(anki_collection)
        builder.add_deck("Test")
        builder.add_cards_with_reviews(
            deck_name="Test",
            num_cards=5,
            review_dates=["2024-01-01"],
            reviews_per_card=1
        )

        reporter = ActivityReporter(anki_collection, config_manager)
        report = reporter.get_report(activity_type=ActivityType.time)

        assert report is not None
        # Time-based activity should aggregate time spent, not review counts
