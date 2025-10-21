"""
Utilities for building test Anki collections with custom review data.

This module provides a fluent API for creating Anki collections populated
with cards and review history for testing purposes.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from anki.collection import Collection
from anki.consts import CARD_TYPE_NEW, CARD_TYPE_REV, QUEUE_TYPE_REV
from anki.notes import Note


class CollectionBuilder:
    """
    Builder for creating test Anki collections with review history.

    Usage:
        builder = CollectionBuilder(col)
        builder.add_deck("Test Deck")
        builder.add_cards_with_reviews(
            deck_name="Test Deck",
            num_cards=10,
            review_dates=["2024-01-01", "2024-01-02"]
        )
    """

    def __init__(self, col: Collection):
        """
        Initialize the collection builder.

        Args:
            col: The Anki collection to populate
        """
        self.col = col
        self._decks = {}
        self._note_type = None
        self._review_counter = 0  # Counter to ensure unique review IDs

    def add_deck(self, name: str, parent: Optional[str] = None) -> "CollectionBuilder":
        """
        Add a deck to the collection.

        Args:
            name: Name of the deck
            parent: Optional parent deck name for nested decks

        Returns:
            Self for method chaining
        """
        if parent:
            full_name = f"{parent}::{name}"
        else:
            full_name = name

        deck_id = self.col.decks.id(full_name)
        self._decks[full_name] = deck_id

        return self

    def _ensure_note_type(self):
        """Ensure a basic note type exists for creating cards."""
        if self._note_type is None:
            # Use the default "Basic" note type that comes with new collections
            models = self.col.models.all()
            if models:
                self._note_type = models[0]
            else:
                # Create a basic note type if none exists
                mm = self.col.models
                basic = mm.new("Basic")
                mm.add_field(basic, mm.new_field("Front"))
                mm.add_field(basic, mm.new_field("Back"))

                template = mm.new_template("Card 1")
                template["qfmt"] = "{{Front}}"
                template["afmt"] = "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"
                mm.add_template(basic, template)

                mm.add(basic)
                self._note_type = basic

    def add_note(
        self,
        deck_name: str,
        front: str = "Test Front",
        back: str = "Test Back"
    ) -> Note:
        """
        Add a note (card) to the collection.

        Args:
            deck_name: Name of the deck to add the note to
            front: Front of the card
            back: Back of the card

        Returns:
            The created Note object
        """
        self._ensure_note_type()

        deck_id = self._decks.get(deck_name)
        if deck_id is None:
            raise ValueError(f"Deck '{deck_name}' not found. Call add_deck() first.")

        note = Note(self.col, self._note_type)
        note["Front"] = front
        note["Back"] = back

        self.col.add_note(note, deck_id)

        return note

    def add_cards_with_reviews(
        self,
        deck_name: str,
        num_cards: int,
        review_dates: List[str],
        reviews_per_card: int = 1,
        rollover_hour: int = 4
    ) -> List[int]:
        """
        Add cards with simulated review history.

        Args:
            deck_name: Name of the deck
            num_cards: Number of cards to create
            review_dates: List of date strings (YYYY-MM-DD) when reviews occurred
            reviews_per_card: Number of reviews per card per date
            rollover_hour: Hour when new day starts (for timezone adjustment)

        Returns:
            List of card IDs created
        """
        card_ids = []

        for i in range(num_cards):
            note = self.add_note(
                deck_name=deck_name,
                front=f"Front {i+1}",
                back=f"Back {i+1}"
            )

            # Get the card created from this note
            cards = note.cards()
            if not cards:
                continue

            card = cards[0]
            card_ids.append(card.id)

            # Add review history
            for date_str in review_dates:
                for _ in range(reviews_per_card):
                    self._add_review(card.id, date_str, rollover_hour)

            # Mark card as review card (not new)
            card.type = CARD_TYPE_REV
            card.queue = QUEUE_TYPE_REV
            self.col.update_card(card)

        self.col.save()
        return card_ids

    def _add_review(self, card_id: int, date_str: str, rollover_hour: int = 4):
        """
        Add a review entry to the revlog for a specific date.

        Args:
            card_id: ID of the card being reviewed
            date_str: Date string in YYYY-MM-DD format
            rollover_hour: Hour when new day starts
        """
        # Parse the date and add the rollover hour
        date = datetime.strptime(date_str, "%Y-%m-%d")
        review_time = date.replace(
            hour=rollover_hour + 2,  # Review a couple hours after day start
            minute=0,
            second=0,
            tzinfo=timezone.utc
        )

        review_timestamp_ms = int(review_time.timestamp() * 1000)

        # Add counter to ensure unique ID for each review
        # (multiple reviews can occur at the same millisecond)
        unique_id = review_timestamp_ms + self._review_counter
        self._review_counter += 1

        # Insert into revlog
        # Schema: id, cid, usn, ease, ivl, lastIvl, factor, time, type
        self.col.db.execute(
            """
            INSERT INTO revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            unique_id,            # id (unique timestamp in ms)
            card_id,              # cid
            -1,                   # usn
            3,                    # ease (Good)
            10,                   # ivl (interval in days)
            1,                    # lastIvl
            2500,                 # factor
            5000,                 # time (5 seconds)
            1,                    # type (review)
        )

    def add_due_cards(
        self,
        deck_name: str,
        num_cards: int,
        due_in_days: int
    ) -> List[int]:
        """
        Add cards that are due in the future.

        Args:
            deck_name: Name of the deck
            num_cards: Number of cards to create
            due_in_days: Number of days from now when cards are due

        Returns:
            List of card IDs created
        """
        card_ids = []

        for i in range(num_cards):
            note = self.add_note(
                deck_name=deck_name,
                front=f"Due Card {i+1}",
                back=f"Due Back {i+1}"
            )

            cards = note.cards()
            if not cards:
                continue

            card = cards[0]

            # Set card as review type and due in future
            card.type = CARD_TYPE_REV
            card.queue = QUEUE_TYPE_REV
            card.due = self.col.sched.today + due_in_days

            self.col.update_card(card)
            card_ids.append(card.id)

        self.col.save()
        return card_ids

    def set_rollover_hour(self, hour: int) -> "CollectionBuilder":
        """
        Set the rollover hour for the collection.

        Args:
            hour: Hour when new day starts (0-23)

        Returns:
            Self for method chaining
        """
        self.col.conf["rollover"] = hour
        self.col.save()
        return self


def create_sample_collection(
    col: Collection,
    timezone_offset: int = 4,
    num_decks: int = 2,
    cards_per_deck: int = 10,
    review_days: int = 30
) -> CollectionBuilder:
    """
    Create a sample collection with review history.

    This is a convenience function that creates a realistic test collection
    with multiple decks and review history over a period of days.

    Args:
        col: The collection to populate
        timezone_offset: Rollover hour (default: 4)
        num_decks: Number of decks to create
        cards_per_deck: Number of cards per deck
        review_days: Number of days of review history

    Returns:
        CollectionBuilder instance for further customization
    """
    builder = CollectionBuilder(col)
    builder.set_rollover_hour(timezone_offset)

    # Create decks
    for i in range(num_decks):
        deck_name = f"Deck {i+1}"
        builder.add_deck(deck_name)

        # Generate review dates for the past N days
        review_dates = []
        today = datetime.now(timezone.utc).date()

        for day_offset in range(review_days):
            review_date = today - timedelta(days=day_offset)
            review_dates.append(review_date.strftime("%Y-%m-%d"))

        # Add cards with review history
        builder.add_cards_with_reviews(
            deck_name=deck_name,
            num_cards=cards_per_deck,
            review_dates=review_dates[:review_days // 2],  # Not every day
            reviews_per_card=2,
            rollover_hour=timezone_offset
        )

        # Add some due cards
        builder.add_due_cards(
            deck_name=deck_name,
            num_cards=cards_per_deck // 2,
            due_in_days=7
        )

    return builder
