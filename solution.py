## Student Name: Seyedreza Rezazadehtehrani
## Student ID: 216217481

from dataclasses import dataclass
from datetime import date, datetime, timedelta, time
from typing import List, Optional, Tuple

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

    # ----------------------------
    # Helper functions
    # ----------------------------

    def to_dt(t: time) -> datetime:
        """Combine date + time into datetime."""
        return datetime.combine(day, t)

    def merge_intervals(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """Merge overlapping or adjacent intervals."""
        if not intervals:
            return []

        intervals.sort(key=lambda x: x[0])
        merged = [intervals[0]]

        for curr_start, curr_end in intervals[1:]:
            last_start, last_end = merged[-1]

            if curr_start <= last_end:  # overlap or adjacent
                merged[-1] = (last_start, max(last_end, curr_end))
            else:
                merged.append((curr_start, curr_end))

        return merged

    def apply_buffer(intervals: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """Expand each interval by buffer before and after."""
        if buffer <= timedelta(0):
            return intervals[:]

        return [(start - buffer, end + buffer) for start, end in intervals]

    def clip_to_window(
        intervals: List[Tuple[datetime, datetime]],
        window: Tuple[datetime, datetime]
    ) -> List[Tuple[datetime, datetime]]:
        """Clip intervals to the effective window."""
        w_start, w_end = window
        clipped = []

        for start, end in intervals:
            if end <= w_start or start >= w_end:
                continue
            clipped.append((max(start, w_start), min(end, w_end)))

        return clipped

    def find_free_gaps(
        busy: List[Tuple[datetime, datetime]],
        window: Tuple[datetime, datetime]
    ) -> List[Tuple[datetime, datetime]]:
        """Find free gaps within window given merged busy intervals."""
        free = []
        w_start, w_end = window

        prev_end = w_start

        for start, end in busy:
            if start > prev_end:
                free.append((prev_end, start))
            prev_end = max(prev_end, end)

        if prev_end < w_end:
            free.append((prev_end, w_end))

        return free

    def generate_slots(
        gaps: List[Tuple[datetime, datetime]]
    ) -> List[datetime]:
        """Generate discrete slot start times."""
        starts = []

        for start, end in gaps:
            current = start
            while current + duration <= end:
                starts.append(current)
                current += duration  # discrete, non-overlapping

        return starts

    # ----------------------------
    # Input validation
    # ----------------------------

    if duration <= timedelta(0) or n <= 0:
        return []

    w_start = to_dt(working_hours.start)
    w_end = to_dt(working_hours.end)

    if w_start >= w_end:
        return []

    # Apply candidate window (intersection)
    if candidate_window:
        c_start = to_dt(candidate_window.start)
        c_end = to_dt(candidate_window.end)

        w_start = max(w_start, c_start)
        w_end = min(w_end, c_end)

        if w_start >= w_end:
            return []

    effective_window = (w_start, w_end)

    # ----------------------------
    # Process busy intervals
    # ----------------------------

    busy_dt = [(to_dt(b.start), to_dt(b.end)) for b in busy_intervals]

    # Apply buffer ONLY to busy intervals
    busy_buffered = apply_buffer(busy_dt)

    # Clip to effective window
    busy_clipped = clip_to_window(busy_buffered, effective_window)

    # Merge overlaps
    busy_merged = merge_intervals(busy_clipped)

    # ----------------------------
    # Compute free gaps
    # ----------------------------

    free_gaps = find_free_gaps(busy_merged, effective_window)

    # ----------------------------
    # Generate slots
    # ----------------------------

    slot_starts = generate_slots(free_gaps)

    if not slot_starts:
        return []

    # Limit to N
    slot_starts = slot_starts[:n]

    # Convert to Slot objects
    return [Slot(start_time=dt.time()) for dt in slot_starts]
