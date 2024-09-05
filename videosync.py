from datetime import datetime, timedelta


def intersection(start1: datetime, start2: datetime, duration1: int, duration2: int):
    'Find time interval present in both videos'
    end1 = start1 + timedelta(milliseconds=duration1)
    end2 = start2 + timedelta(milliseconds=duration2)
    start = max(start1, start2)
    end = min(end1, end2)
    return start, end