from collections.abc import Sequence
from datetime import datetime, timedelta


def intersection(starts: Sequence[datetime], durations: Sequence[timedelta]):
    """Find time interval present in all videos"""
    ends = [start + duration for start, duration in zip(starts, durations)]

    start = max(starts)
    end = min(ends)

    if start > end:
        raise AssertionError('Intervals do not intersect')
    
    return start, end
