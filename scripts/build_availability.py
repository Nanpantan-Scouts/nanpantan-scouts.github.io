#!/usr/bin/env python3
"""Build data/availability.json for the venue hire page's availability calendar.

Reads the hut's published Outlook calendar feed (an .ics file), works out which
times are booked and free on each day within the hall's hire hours, and writes
the result for Hugo to show. Settings live in hugo.toml under
[params.venue_availability].

The deploy workflow runs this every hour. To run it yourself:

    pip install -r scripts/requirements.txt
    python3 scripts/build_availability.py            # fetches the live feed
    python3 scripts/build_availability.py --ics FILE # uses a saved .ics file
"""

import argparse
import json
import sys
import tomllib
import urllib.request
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import icalendar
import recurring_ical_events

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "availability.json"


def load_settings():
    with open(ROOT / "hugo.toml", "rb") as f:
        return tomllib.load(f)["params"]["venue_availability"]


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "nanpantanscouts.org.uk availability"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def parse_hhmm(value):
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


def is_booking(event):
    """Outlook publishes "Free" entries too; only busy or tentative time counts as booked."""
    if str(event.get("TRANSP", "OPAQUE")).upper() == "TRANSPARENT":
        return False
    return str(event.get("X-MICROSOFT-CDO-BUSYSTATUS", "BUSY")).upper() != "FREE"


def to_local(value, tz):
    """Convert an event start/end to a datetime in the venue's timezone."""
    if isinstance(value, datetime):
        if value.tzinfo is None:  # "floating" time: already local
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)
    return datetime.combine(value, time.min, tz)  # all-day event: a date


def merge(intervals):
    merged = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def format_time(t):
    """9:30am, 12pm, 4:30pm."""
    hour = t.hour % 12 or 12
    suffix = "am" if t.hour < 12 else "pm"
    return f"{hour}{suffix}" if t.minute == 0 else f"{hour}:{t.minute:02d}{suffix}"


def format_range(start, end):
    return f"{format_time(start)}–{format_time(end)}"


def week_label(first, last):
    if first.year != last.year:
        return f"{first.day} {first:%B %Y} – {last.day} {last:%B %Y}"
    if first.month != last.month:
        return f"{first.day} {first:%B} – {last.day} {last:%B %Y}"
    return f"{first.day}–{last.day} {last:%B %Y}"


def build(calendar, settings, today):
    tz = ZoneInfo(settings["timezone"])
    weeks = int(settings["weeks"])
    min_free = timedelta(minutes=int(settings["min_free_minutes"]))
    hours = {
        "weekday": tuple(parse_hhmm(v) for v in settings["weekday_hours"]),
        "weekend": tuple(parse_hhmm(v) for v in settings["weekend_hours"]),
    }

    first_day = today - timedelta(days=today.weekday())  # Monday of this week
    last_day = first_day + timedelta(weeks=weeks)
    window_start = datetime.combine(first_day, time.min, tz)
    window_end = datetime.combine(last_day, time.min, tz)

    # Every booked interval in the period, recurring bookings expanded
    booked = []
    for event in recurring_ical_events.of(calendar).between(window_start, window_end):
        if not is_booking(event):
            continue
        start = to_local(event["DTSTART"].dt, tz)
        end = to_local(event["DTEND"].dt, tz) if "DTEND" in event else start + timedelta(days=1)
        if end > start:
            booked.append((start, end))

    result_weeks = []
    for w in range(weeks):
        monday = first_day + timedelta(weeks=w)
        days = []
        for d in range(7):
            day = monday + timedelta(days=d)
            open_time, close_time = hours["weekend" if day.weekday() >= 5 else "weekday"]
            day_open = datetime.combine(day, open_time, tz)
            day_close = datetime.combine(day, close_time, tz)

            # Bookings clipped to hire hours
            busy = merge(
                (max(start, day_open), min(end, day_close))
                for start, end in booked
                if start < day_close and end > day_open
            )
            free, cursor = [], day_open
            for start, end in busy:
                if start - cursor >= min_free:
                    free.append((cursor, start))
                cursor = max(cursor, end)
            if day_close - cursor >= min_free:
                free.append((cursor, day_close))

            status = "free" if not busy else ("full" if not free else "part")
            slots = sorted([(s, e, "booked") for s, e in busy] + [(s, e, "free") for s, e in free])
            days.append({
                "date": day.isoformat(),
                "label": f"{day:%a} {day.day} {day:%b}",
                "status": status,
                "slots": [{"kind": kind, "time": format_range(s.timetz(), e.timetz())} for s, e, kind in slots],
            })
        result_weeks.append({
            "start": monday.isoformat(),
            "label": week_label(monday, monday + timedelta(days=6)),
            "days": days,
        })

    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hours": {name: format_range(*span) for name, span in hours.items()},
        "weeks": result_weeks,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ics", type=Path, help="read this .ics file instead of fetching the feed")
    parser.add_argument("--today", type=date.fromisoformat, help="pretend today is this date (YYYY-MM-DD), for testing")
    args = parser.parse_args()

    settings = load_settings()
    raw = args.ics.read_bytes() if args.ics else fetch(settings["feed_url"])
    calendar = icalendar.Calendar.from_ical(raw)
    today = args.today or datetime.now(ZoneInfo(settings["timezone"])).date()

    data = build(calendar, settings, today)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    booked_days = sum(1 for week in data["weeks"] for day in week["days"] if day["status"] != "free")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}: {len(data['weeks'])} weeks, {booked_days} days with bookings")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # the deploy carries on without the calendar
        print(f"Could not build availability: {error}", file=sys.stderr)
        sys.exit(1)
