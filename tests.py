import pytest
from datetime import date, datetime, time, timedelta
from solution import TimeWindow, BusyInterval, Slot, suggest_slots

# ---------- Helpers ----------

def combine(d: date, t: time) -> datetime:
    return datetime.combine(d, t)

def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end

def in_window(win: TimeWindow, t: time) -> bool:
    return win.start <= t < win.end

def assert_slots_basic_constraints(slots, n):
    assert isinstance(slots, list)
    assert len(slots) <= n
    assert slots == sorted(slots, key=lambda s: s.start_time)


TEST_DAY = date(2026, 1, 1)


# Covers C1, AC1 (automatic merging of overlapping + unsorted intervals)
def test_merging_overlapping_intervals():
    working_hours = TimeWindow(start=time(9, 0), end=time(17, 0))

    busy = [
        BusyInterval(time(13, 0), time(14, 0)),
        BusyInterval(time(9, 30), time(11, 0)),
        BusyInterval(time(10, 30), time(12, 0)),  # overlaps with above
    ]

    slots = suggest_slots(
        day=TEST_DAY,
        working_hours=working_hours,
        busy_intervals=busy,
        duration=timedelta(hours=1),
        n=5
    )

    assert_slots_basic_constraints(slots, 5)

    # Merged block: 9:30–12:00 and 13:00–14:00
    # 9:00–9:30 gap is only 30 min, too small for 1-hour meeting
    # Valid slots: 12:00, 14:00, 15:00, 16:00
    expected_times = [time(12, 0), time(14, 0), time(15, 0), time(16, 0)]
    assert [s.start_time for s in slots] == expected_times[:len(slots)]


# Covers C4, AC4 (fully booked → explicit empty list, no failure)
def test_fully_booked_returns_empty():
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))

    busy = [
        BusyInterval(time(9, 0), time(12, 0))
    ]

    slots = suggest_slots(
        day=TEST_DAY,
        working_hours=working_hours,
        busy_intervals=busy,
        duration=timedelta(minutes=30),
        n=3
    )

    assert slots == []


# Covers C3, AC3 (determinism: identical inputs → identical outputs)
def test_deterministic_output():
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))

    busy = [
        BusyInterval(time(9, 30), time(10, 0))
    ]

    result1 = suggest_slots(
        TEST_DAY,
        working_hours,
        busy,
        timedelta(minutes=30),
        3
    )

    result2 = suggest_slots(
        TEST_DAY,
        working_hours,
        busy,
        timedelta(minutes=30),
        3
    )

    assert result1 == result2


# Covers C5, AC5 (buffer applied strictly; exact-fit gap rejected if buffer breaks fit)
def test_buffer_blocks_exact_fit():
    working_hours = TimeWindow(start=time(9, 0), end=time(11, 0))

    busy = [
        BusyInterval(time(10, 0), time(10, 30))
    ]

    # Gap from 9:00–10:00 = 60 min
    # Buffer = 15 min → busy expands to 9:45–10:45
    # New gap = 9:00–9:45 (45 min) → cannot fit 60 min meeting

    slots = suggest_slots(
        TEST_DAY,
        working_hours,
        busy,
        duration=timedelta(hours=1),
        n=2,
        buffer=timedelta(minutes=15)
    )

    assert slots == []


# Covers C6, AC6 (candidate window clipped to working hours)
def test_candidate_window_clipping():
    working_hours = TimeWindow(start=time(9, 0), end=time(17, 0))

    candidate_window = TimeWindow(start=time(16, 0), end=time(18, 0))  # exceeds working hours

    slots = suggest_slots(
        day=TEST_DAY,
        working_hours=working_hours,
        busy_intervals=[],
        duration=timedelta(hours=1),
        n=3,
        candidate_window=candidate_window
    )

    assert_slots_basic_constraints(slots, 3)

    # Only 16:00–17:00 is valid after clipping
    assert [s.start_time for s in slots] == [time(16, 0)]


# Covers C2, AC2 (strict chronological ordering + max N slots)
def test_strict_order_and_limit():
    working_hours = TimeWindow(start=time(9, 0), end=time(12, 0))

    slots = suggest_slots(
        TEST_DAY,
        working_hours,
        busy_intervals=[],
        duration=timedelta(minutes=30),
        n=2
    )

    assert_slots_basic_constraints(slots, 2)

    assert len(slots) == 2
    assert slots[0].start_time < slots[1].start_time
