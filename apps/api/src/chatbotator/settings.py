"""Settings shared across the app: where the data lives and the demo's date."""

from datetime import date
from pathlib import Path

# settings.py -> chatbotator -> src -> api -> apps -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
DATA_DIR = REPO_ROOT / "data"

# The demo runs on a fixed date, the fixtures' referenceDate (in
# data/fixtures/orders.json), so answers about deadlines don't change from day
# to day.
TODAY = date(2026, 10, 26)
