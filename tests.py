import pytest
from datetime import date, datetime, time, timedelta

# Update import path to match your project structure:
from solution import TimeWindow, BusyInterval, Slot, suggest_slots

# ---------- Helpers ----------

def combine(d: date, t: time) -> datetime:
    return datetime.combine(d, t)

def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end

def in_window(win: TimeWindow, t: time) -> bool:
    return win.start <= t < win.end

def assert_slots_basic_constraints(
    slots,
    day,
    working_hours,
    busy_intervals,
    duration,
    n,
    buffer,
    candidate_window,
):
    # Return type / length
    assert isinstance(slots, list)
    assert len(slots) <= n

    # Deterministic ordering: start_time ascending
    assert slots == sorted(slots, key=lambda s: s.start_time)

    # Each slot start must be within working_hours and candidate_window (if any)
    for s in slots:
        assert in_window(working_hours, s.start_time)
        if candidate_window is not None:
            assert in_window(candidate_window, s.start_time)

    # Each slot must fit fully inside working_hours and candidate_window
    for s in slots:
        start_dt = combine(day, s.start_time)
        end_dt = start_dt + duration

        wh_end = combine(day, working_hours.end)
        assert end_dt <= wh_end

        if candidate_window is not None:
            cw_end = combine(day, candidate_window.end)
            assert end_dt <= cw_end

    # No overlap with busy intervals, considering buffer:
    for s in slots:
        slot_start = combine(day, s.start_time)
        slot_end = slot_start + duration

        for b in busy_intervals:
            b_start = combine(day, b.start) - buffer
            b_end = combine(day, b.end) + buffer
            assert not overlaps(slot_start, slot_end, b_start, b_end)

# ---------- Tests ----------

def test_a1_no_busy_simple_slots():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(
        day=day,
        working_hours=working,
        busy_intervals=busy,
        duration=duration,
        n=3,
        buffer=timedelta(0),
        candidate_window=None
    )

    assert_slots_basic_constraints(out, day, working, busy, duration, 3, timedelta(0), None)
    assert len(out) > 0
    assert out[0].start_time >= time(9, 0)

def test_a2_deterministic_same_inputs_same_outputs():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    busy = [
        BusyInterval(time(10, 0), time(10, 30)),
        BusyInterval(time(13, 0), time(14, 0)),
    ]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=0)

    out1 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)
    out2 = suggest_slots(day, working, busy, duration, n=10, buffer=buffer, candidate_window=None)

    assert [s.start_time for s in out1] == [s.start_time for s in out2]
    assert_slots_basic_constraints(out1, day, working, busy, duration, 10, buffer, None)

def test_a3_overlapping_and_unsorted_busy_intervals_handled():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [
        BusyInterval(time(10, 30), time(11, 0)),
        BusyInterval(time(10, 0), time(10, 45)),
        BusyInterval(time(9, 30), time(9, 45)),
    ]
    duration = timedelta(minutes=15)

    out = suggest_slots(day, working, busy, duration, n=8, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out, day, working, busy, duration, 8, timedelta(0), None)

def test_a4_candidate_window_respected():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(17, 0))
    candidate = TimeWindow(time(13, 0), time(15, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5, buffer=timedelta(0), candidate_window=candidate)
    assert_slots_basic_constraints(out, day, working, busy, duration, 5, timedelta(0), candidate)
    assert all(candidate.start <= s.start_time < candidate.end for s in out)

def test_a5_buffer_eliminates_small_gaps():
    day = date(2026, 2, 24)
    working = TimeWindow(time(9, 0), time(11, 0))
    busy = [
        BusyInterval(time(9, 30), time(9, 50)),
        BusyInterval(time(10, 10), time(10, 30)),
    ]
    duration = timedelta(minutes=20)

    out_no_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=timedelta(0), candidate_window=None)
    assert_slots_basic_constraints(out_no_buffer, day, working, busy, duration, 10, timedelta(0), None)

    buf = timedelta(minutes=5)
    out_with_buffer = suggest_slots(day, working, busy, duration, n=10, buffer=buf, candidate_window=None)
    assert_slots_basic_constraints(out_with_buffer, day, working, busy, duration, 10, buf, None)
    assert len(out_with_buffer) <= len(out_no_buffer)

#################################################################################
# Add your own additional tests here to cover more cases and edge cases as needed.
#################################################################################

def test_b1_no_busy_exact_slots_and_order():
    """
    Validates:
    - AC1, AC6: correct slot generation and duration
    - C1: within working hours
    """
    day = date(2026, 1, 1)
    working = TimeWindow(time(9, 0), time(11, 0))
    busy = []
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=3)

    assert_slots_basic_constraints(out, day, working, busy, duration, 3, timedelta(0), None)
    assert out == [
        Slot(time(9, 0)),
        Slot(time(9, 30)),
        Slot(time(10, 0)),
    ]


def test_b2_buffer_blocks_slots_correctly():
    """
    Validates:
    - AC2: buffer respected
    - C2: no violation of buffered intervals
    """
    day = date(2026, 1, 1)
    working = TimeWindow(time(9, 0), time(12, 0))
    busy = [BusyInterval(time(10, 0), time(11, 0))]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=15)

    out = suggest_slots(day, working, busy, duration, n=10, buffer=buffer)

    assert_slots_basic_constraints(out, day, working, busy, duration, 10, buffer, None)
    assert out == [
        Slot(time(9, 0)),
        Slot(time(9, 30)),
    ]


def test_b3_unsorted_overlapping_intervals_merge():
    """
    Validates:
    - AC4: merging logic
    - EC2: unsorted + overlapping intervals
    """
    day = date(2026, 1, 1)
    working = TimeWindow(time(9, 0), time(13, 0))
    busy = [
        BusyInterval(time(11, 0), time(12, 0)),
        BusyInterval(time(10, 0), time(11, 30)),
    ]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=10)

    assert_slots_basic_constraints(out, day, working, busy, duration, 10, timedelta(0), None)
    assert out == [
        Slot(time(9, 0)),
        Slot(time(9, 30)),
        Slot(time(12, 0)),
        Slot(time(12, 30)),
    ]


def test_b4_fully_booked_returns_empty():
    """
    Validates:
    - EC1: no availability
    - exception rule: returns []
    """
    day = date(2026, 1, 1)
    working = TimeWindow(time(9, 0), time(10, 0))
    busy = [BusyInterval(time(9, 0), time(10, 0))]
    duration = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5)

    assert out == []


def test_b5_exact_fit_gap_with_buffer():
    """
    Validates:
    - EC3: exact fit gap
    - C2: buffer correctness
    """
    day = date(2026, 1, 1)
    working = TimeWindow(time(9, 0), time(11, 0))
    busy = [BusyInterval(time(10, 0), time(11, 0))]
    duration = timedelta(minutes=30)
    buffer = timedelta(minutes=30)

    out = suggest_slots(day, working, busy, duration, n=5, buffer=buffer)

    assert_slots_basic_constraints(out, day, working, busy, duration, 5, buffer, None)
    assert out == [
        Slot(time(9, 0)),
    ]
