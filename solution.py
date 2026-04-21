## Student Name: Seyedreza Rezazadehtehrani
## Student ID: 216217481

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional

@dataclass(frozen=True)
class TimeWindow:
    start: time
    end: time

@dataclass(frozen=True)
class BusyInterval:
    start: time
    end: time

@dataclass(frozen=True)
class Slot:
    start_time: time

class InfeasibleSchedule(Exception):
    pass


def suggest_slots(
    day: date,
    working_hours: TimeWindow,
    busy_intervals: List[BusyInterval],
    duration: timedelta,
    n: int,
    buffer: timedelta = timedelta(0),
    candidate_window: Optional[TimeWindow] = None
) -> List[Slot]:

    # -----------------------------
    # 1. Validate deterministic early exits
    # -----------------------------
    if n <= 0 or duration <= timedelta(0):
        return []

    def to_dt(t: time) -> datetime:
        return datetime.combine(day, t)

    def to_time(dt: datetime) -> time:
        return dt.time()

    work_start = to_dt(working_hours.start)
    work_end = to_dt(working_hours.end)

    if work_start >= work_end:
        return []

    # -----------------------------
    # 2. Apply candidate window (with clipping)
    # -----------------------------
    if candidate_window:
        cand_start = to_dt(candidate_window.start)
        cand_end = to_dt(candidate_window.end)

        # Clip to working hours
        window_start = max(work_start, cand_start)
        window_end = min(work_end, cand_end)

        if window_start >= window_end:
            return []
    else:
        window_start = work_start
        window_end = work_end

    # -----------------------------
    # 3. Normalize + merge busy intervals
    # -----------------------------
    normalized = []

    for b in busy_intervals:
        start = to_dt(b.start)
        end = to_dt(b.end)

        # Ignore invalid or zero-length intervals deterministically
        if start >= end:
            continue

        # Apply buffer ONLY around busy intervals
        start -= buffer
        end += buffer

        # Clip to working window (important for determinism)
        start = max(start, work_start)
        end = min(end, work_end)

        if start < end:
            normalized.append((start, end))

    # Sort deterministically
    normalized.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged = []
    for interval in normalized:
        if not merged:
            merged.append(interval)
        else:
            prev_start, prev_end = merged[-1]
            curr_start, curr_end = interval

            if curr_start <= prev_end:  # overlap (half-open safe)
                merged[-1] = (prev_start, max(prev_end, curr_end))
            else:
                merged.append(interval)

    # -----------------------------
    # 4. Find free gaps
    # -----------------------------
    free_gaps = []
    current = window_start

    for start, end in merged:
        if end <= window_start or start >= window_end:
            continue

        gap_start = current
        gap_end = min(start, window_end)

        if gap_start < gap_end:
            free_gaps.append((gap_start, gap_end))

        current = max(current, end)

    # Final trailing gap
    if current < window_end:
        free_gaps.append((current, window_end))

    # -----------------------------
    # 5. Generate slots (deterministic, earliest-first)
    # -----------------------------
    slots: List[Slot] = []

    for gap_start, gap_end in free_gaps:
        cursor = gap_start

        while cursor + duration <= gap_end:
            slots.append(Slot(start_time=to_time(cursor)))

            if len(slots) >= n:
                return slots

            # No buffer between slots per spec
            cursor += duration

    return slots
