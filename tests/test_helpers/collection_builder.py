#!/usr/bin/env python3
"""
Generate an Anki collection with hourly review data for testing review-heatmap.

This script creates an Anki collection with a single card that has been reviewed
every hour between Dec 1, 2023 00:00:00 UTC and Feb 1, 2025 00:00:00 UTC.

Usage:
    python collection_builder.py --output test_collection.anki2
"""

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from anki.collection import Collection
from anki.consts import CARD_TYPE_REV, QUEUE_TYPE_REV


def generate_hourly_reviews(col: Collection, card_id: int, start_date: datetime, end_date: datetime):
    """
    Generate hourly reviews for a card between start and end dates.

    Args:
        col: Anki collection
        card_id: ID of the card to add reviews for
        start_date: Start datetime (inclusive)
        end_date: End datetime (inclusive)
    """
    current_time = start_date
    review_counter = 0

    print(f"Generating reviews from {start_date} to {end_date}...")

    reviews_added = 0
    while current_time <= end_date:
        # Create timestamp in milliseconds (Anki format)
        timestamp_ms = int(current_time.timestamp() * 1000)

        # Create unique ID by adding counter
        unique_id = timestamp_ms + review_counter
        review_counter += 1

        # Insert review into revlog
        # Schema: id, cid, usn, ease, ivl, lastIvl, factor, time, type
        col.db.execute(
            """
            INSERT INTO revlog (id, cid, usn, ease, ivl, lastIvl, factor, time, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            unique_id,      # id (unique timestamp in ms)
            card_id,        # cid (card ID)
            -1,             # usn (update sequence number)
            3,              # ease (3 = Good)
            10,             # ivl (interval in days)
            1,              # lastIvl (last interval)
            2500,           # factor (ease factor)
            5000,           # time (5 seconds review time)
            1,              # type (1 = review)
        )

        reviews_added += 1
        if reviews_added % 1000 == 0:
            print(f"  Added {reviews_added} reviews...")

        # Move to next hour
        current_time += timedelta(hours=1)

    print(f"Total reviews added: {reviews_added}")
    return reviews_added


def create_test_collection(output_path: str):
    """
    Create a test Anki collection with hourly reviews.

    Args:
        output_path: Path where the collection should be saved
    """
    print(f"Creating collection at: {output_path}")

    # Create collection
    col = Collection(output_path)

    # Get or create a basic note type
    models = col.models.all()
    if models:
        note_type = models[0]
    else:
        # Create basic note type
        mm = col.models
        basic = mm.new("Basic")
        mm.add_field(basic, mm.new_field("Front"))
        mm.add_field(basic, mm.new_field("Back"))

        template = mm.new_template("Card 1")
        template["qfmt"] = "{{Front}}"
        template["afmt"] = "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"
        mm.add_template(basic, template)

        mm.add(basic)
        note_type = basic

    print(f"Using note type: {note_type['name']}")

    # Create default deck
    deck_id = col.decks.id("Test Deck")
    print(f"Created deck: Test Deck (ID: {deck_id})")

    # Create a note and card
    from anki.notes import Note
    note = Note(col, note_type)
    note["Front"] = "Test Card - Hourly Reviews"
    note["Back"] = "This card has reviews every hour from Dec 1 2023 to Feb 1 2025"

    col.add_note(note, deck_id)
    print(f"Created note with ID: {note.id}")

    # Get the card
    cards = note.cards()
    if not cards:
        print("ERROR: No card was created from the note!")
        col.close()
        sys.exit(1)

    card = cards[0]
    print(f"Created card with ID: {card.id}")

    # Set card as review type (not new)
    card.type = CARD_TYPE_REV
    card.queue = QUEUE_TYPE_REV
    card.due = col.sched.today
    col.update_card(card)

    # Generate hourly reviews from Dec 1 2023 to Feb 1 2025 (UTC)
    start_date = datetime(2023, 12, 1, 0, 0, 0, tzinfo=timezone.utc)
    end_date = datetime(2025, 2, 1, 0, 0, 0, tzinfo=timezone.utc)

    num_reviews = generate_hourly_reviews(col, card.id, start_date, end_date)

    # Close and save the collection
    col.close()

    print("\n" + "=" * 60)
    print("Collection created successfully!")
    print("=" * 60)
    print(f"Output file: {output_path}")
    print(f"Total cards: 1")
    print(f"Total reviews: {num_reviews}")
    print(f"Review period: {start_date} to {end_date}")
    print(f"Review frequency: Every hour")
    print("=" * 60)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Generate an Anki collection with hourly review data for testing"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path for the Anki collection file (e.g., test.anki2)"
    )

    args = parser.parse_args()

    # Validate output path
    output_path = Path(args.output)

    # Check if file already exists
    if output_path.exists():
        response = input(f"File {output_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)
        # Remove existing file
        output_path.unlink()

    # Create the collection
    create_test_collection(str(output_path))


if __name__ == "__main__":
    main()
