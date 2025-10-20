"""
Timezone utilities for testing review-heatmap with different timezone configurations.

This module provides helpers for:
- Creating collections with specific timezone offsets
- Converting between timezones for test verification
- Testing DST transitions
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from anki.collection import Collection


class TimezoneHelper:
    """
    Helper class for timezone-aware testing.

    This class provides utilities to test the review-heatmap add-on
    with different timezone configurations.
    """

    # Common timezone offsets (in hours from UTC)
    TIMEZONES = {
        "UTC": 0,
        "US_PACIFIC": -8,
        "US_EASTERN": -5,
        "UK": 0,
        "EUROPE_CENTRAL": 1,
        "JAPAN": 9,
        "AUSTRALIA_SYDNEY": 10,
    }

    def __init__(self, rollover_hour: int = 4):
        """
        Initialize timezone helper.

        Args:
            rollover_hour: Hour when Anki considers a new day to start (0-23)
        """
        self.rollover_hour = rollover_hour

    def configure_collection_timezone(
        self,
        col: Collection,
        rollover_hour: Optional[int] = None
    ):
        """
        Configure a collection's timezone settings.

        Args:
            col: The Anki collection to configure
            rollover_hour: Hour when new day starts (uses instance default if None)
        """
        if rollover_hour is None:
            rollover_hour = self.rollover_hour

        col.conf["rollover"] = rollover_hour
        col.save()

    @staticmethod
    def datetime_to_timestamp_ms(dt: datetime) -> int:
        """
        Convert datetime to Anki timestamp (milliseconds since epoch).

        Args:
            dt: DateTime object (should be timezone-aware)

        Returns:
            Timestamp in milliseconds
        """
        return int(dt.timestamp() * 1000)

    @staticmethod
    def timestamp_ms_to_datetime(ts_ms: int) -> datetime:
        """
        Convert Anki timestamp to datetime.

        Args:
            ts_ms: Timestamp in milliseconds

        Returns:
            DateTime object in UTC
        """
        return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)

    def get_day_start(
        self,
        date: datetime,
        rollover_hour: Optional[int] = None
    ) -> datetime:
        """
        Get the start of a day according to Anki's rollover hour.

        Args:
            date: The date to get the start of
            rollover_hour: Hour when day starts (uses instance default if None)

        Returns:
            DateTime representing the start of the Anki day
        """
        if rollover_hour is None:
            rollover_hour = self.rollover_hour

        # Get midnight of the date
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)

        # Add rollover hours
        return day_start + timedelta(hours=rollover_hour)

    def create_review_timestamp(
        self,
        date_str: str,
        hour: Optional[int] = None,
        minute: int = 0
    ) -> int:
        """
        Create a review timestamp for a specific date.

        Args:
            date_str: Date string in YYYY-MM-DD format
            hour: Hour of the review (uses rollover_hour + 2 if None)
            minute: Minute of the review

        Returns:
            Timestamp in milliseconds suitable for Anki's revlog
        """
        date = datetime.strptime(date_str, "%Y-%m-%d")

        if hour is None:
            hour = self.rollover_hour + 2

        review_time = date.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0,
            tzinfo=timezone.utc
        )

        return self.datetime_to_timestamp_ms(review_time)

    @staticmethod
    def get_timezone_offset_name(offset_hours: int) -> str:
        """
        Get a human-readable name for a timezone offset.

        Args:
            offset_hours: Offset in hours from UTC

        Returns:
            String representation (e.g., "UTC+9", "UTC-5")
        """
        if offset_hours == 0:
            return "UTC"
        elif offset_hours > 0:
            return f"UTC+{offset_hours}"
        else:
            return f"UTC{offset_hours}"

    def generate_review_dates(
        self,
        start_date: str,
        num_days: int,
        skip_weekends: bool = False
    ) -> list[str]:
        """
        Generate a list of review dates.

        Args:
            start_date: Starting date in YYYY-MM-DD format
            num_days: Number of days to generate
            skip_weekends: If True, skip Saturday and Sunday

        Returns:
            List of date strings in YYYY-MM-DD format
        """
        dates = []
        current = datetime.strptime(start_date, "%Y-%m-%d")

        while len(dates) < num_days:
            # Skip weekends if requested
            if skip_weekends and current.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                current += timedelta(days=1)
                continue

            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    @staticmethod
    def create_dst_transition_dates() -> dict[str, list[str]]:
        """
        Get common DST transition dates for testing.

        Returns:
            Dictionary with DST transition scenarios and dates to test
        """
        return {
            "spring_forward_2024": [
                "2024-03-09",  # Day before DST
                "2024-03-10",  # DST transition day (US)
                "2024-03-11",  # Day after DST
            ],
            "fall_back_2024": [
                "2024-11-02",  # Day before DST
                "2024-11-03",  # DST transition day (US)
                "2024-11-04",  # Day after DST
            ],
            "year_boundary_2024": [
                "2023-12-30",
                "2023-12-31",
                "2024-01-01",
                "2024-01-02",
            ],
        }


def create_timezone_test_scenarios() -> list[dict]:
    """
    Create common timezone test scenarios.

    Returns:
        List of test scenario dictionaries with timezone configurations
    """
    return [
        {
            "name": "UTC with 4am rollover",
            "rollover_hour": 4,
            "description": "Default Anki configuration",
        },
        {
            "name": "UTC with midnight rollover",
            "rollover_hour": 0,
            "description": "Rollover at midnight",
        },
        {
            "name": "Japan timezone (UTC+9) with 4am rollover",
            "rollover_hour": 4,
            "description": "Eastern timezone",
        },
        {
            "name": "US Pacific with 4am rollover",
            "rollover_hour": 4,
            "description": "Western timezone",
        },
        {
            "name": "Late night learner (6am rollover)",
            "rollover_hour": 6,
            "description": "Custom late rollover",
        },
    ]
