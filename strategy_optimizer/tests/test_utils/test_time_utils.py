# tests/test_utils/test_time_utils.py
import pytest
from datetime import datetime, timezone, timedelta
from src.utils.time_utils import TimeUtils

@pytest.fixture
def time_utils():
    return TimeUtils()

def test_now_utc(time_utils):
    now = time_utils.now_utc()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc

def test_parse_iso8601(time_utils):
    iso_string_utc = "2023-01-01T10:30:00Z"
    dt_utc = time_utils.parse_iso8601(iso_string_utc)
    assert dt_utc.year == 2023
    assert dt_utc.month == 1
    assert dt_utc.hour == 10
    assert dt_utc.tzinfo == timezone.utc

    iso_string_no_tz = "2023-01-01T10:30:00"
    dt_no_tz = time_utils.parse_iso8601(iso_string_no_tz)
    assert dt_no_tz.tzinfo == timezone.utc # Should default to UTC

    iso_string_offset = "2023-01-01T10:30:00+02:00"
    dt_offset = time_utils.parse_iso8601(iso_string_offset)
    assert dt_offset.tzinfo is not None
    assert dt_offset.hour == 10 # Original hour
    assert dt_offset.astimezone(timezone.utc).hour == 8 # Convert to UTC for comparison

def test_parse_iso8601_invalid(time_utils):
    with pytest.raises(ValueError):
        time_utils.parse_iso8601("invalid-date-string")

def test_to_iso8601(time_utils):
    dt_utc = datetime(2023, 1, 1, 10, 30, 0, tzinfo=timezone.utc)
    iso_string = time_utils.to_iso8601(dt_utc)
    assert iso_string == "2023-01-01T10:30:00.000Z"

    dt_no_tz = datetime(2023, 1, 1, 10, 30, 0)
    iso_string_no_tz = time_utils.to_iso8601(dt_no_tz)
    assert iso_string_no_tz == "2023-01-01T10:30:00.000Z" # Assumed UTC

def test_ensure_causal(time_utils):
    ref_time = datetime(2023, 1, 1, 10, tzinfo=timezone.utc)
    
    past_time = datetime(2023, 1, 1, 9, tzinfo=timezone.utc)
    assert time_utils.ensure_causal(past_time, ref_time) is True

    current_time = datetime(2023, 1, 1, 10, tzinfo=timezone.utc)
    assert time_utils.ensure_causal(current_time, ref_time) is True

    future_time = datetime(2023, 1, 1, 11, tzinfo=timezone.utc)
    assert time_utils.ensure_causal(future_time, ref_time) is False
