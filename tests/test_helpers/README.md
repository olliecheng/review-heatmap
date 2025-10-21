# Test Helpers

## collection_builder.py

This is a standalone script for generating test Anki collections with hourly review data.

### Usage

```bash
python tests/test_helpers/collection_builder.py --output test_collection.anki2
```

### What it does

Creates an Anki collection with:
- 1 test card
- Reviews for every single hour between Dec 1, 2023 00:00:00 UTC and Feb 1, 2025 00:00:00 UTC
- Total of 10,273 hourly reviews

### Example output

```
Creating collection at: test_collection.anki2
Using note type: Basic
Created deck: Test Deck (ID: 1761012798248)
Created note with ID: 1761012798252
Created card with ID: 1761012798252
Generating reviews from 2023-12-01 00:00:00+00:00 to 2025-02-01 00:00:00+00:00...
  Added 1000 reviews...
  Added 2000 reviews...
  Added 3000 reviews...
  Added 4000 reviews...
  Added 5000 reviews...
  Added 6000 reviews...
  Added 7000 reviews...
  Added 8000 reviews...
  Added 9000 reviews...
  Added 10000 reviews...
Total reviews added: 10273

============================================================
Collection created successfully!
============================================================
Output file: test_collection.anki2
Total cards: 1
Total reviews: 10273
Review period: 2023-12-01 00:00:00+00:00 to 2025-02-01 00:00:00+00:00
Review frequency: Every hour
============================================================
```

### Verifying the collection

You can verify the generated collection using Python:

```python
from anki.collection import Collection
from datetime import datetime, timezone

col = Collection('test_collection.anki2')

# Check review count
review_count = col.db.scalar('SELECT COUNT(*) FROM revlog')
print(f'Total reviews: {review_count}')

# Check first and last review
first_review = col.db.scalar('SELECT MIN(id) FROM revlog')
last_review = col.db.scalar('SELECT MAX(id) FROM revlog')

first_dt = datetime.fromtimestamp(first_review / 1000, tz=timezone.utc)
last_dt = datetime.fromtimestamp(last_review / 1000, tz=timezone.utc)

print(f'First review: {first_dt}')
print(f'Last review: {last_dt}')

col.close()
```

## timezone_utils.py

Provides timezone utilities for testing (unchanged).

See `tests/README.md` for more information.

---

**Note:** The previous class-based CollectionBuilder API has been replaced with this
standalone script. The test files (test_activity_reporter.py, example_usage.py, demo_framework.py)
that referenced the old API are now deprecated. Use this script to generate test collections
and then load them directly with the Anki Collection API.
