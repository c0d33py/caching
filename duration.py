# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# Convert duration from ISO 8601 format to a more readable format


from timedelta_isoformat import timedelta


def parse_iso8601_duration(duration: str):
    if duration is None:
        return None

    try:
        duration_components = timedelta.fromisoformat(duration)
    except (ValueError, TypeError):
        duration_components = duration

    print(duration_components)


# P3Y6M4DT12H30M5S
parse_iso8601_duration('P3D2H30M5S')
