from typing import Dict, List, Tuple, Optional
import datetime

# ── Master schedule ────────────────────────────────────────────────
# Keys are ISO dates (YYYY-MM-DD). Values are time strings in 12‑hour
# format. Each date offers five slots.
# -------------------------------------------------------------------
schedule: Dict[str, List[str]] = {
    "2025-06-11": ["9:00 AM", "10:30 AM", "12:00 PM", "2:00 PM", "3:30 PM"],
    "2025-06-12": ["9:00 AM", "10:30 AM", "12:00 PM", "1:30 PM", "3:00 PM"],
    "2025-06-13": ["9:30 AM", "11:00 AM", "12:30 PM", "2:00 PM", "3:30 PM"],
    "2025-06-14": ["9:00 AM", "10:30 AM", "12:00 PM", "2:00 PM", "3:30 PM"],
    "2025-06-15": ["9:00 AM", "10:30 AM", "12:00 PM", "2:00 PM", "3:30 PM"],
}

# Track confirmed appointments:  date → time → caller name
booked: Dict[str, Dict[str, str]] = {}

# ── Helpers ────────────────────────────────────────────────────────

def _time_key(time_str: str) -> datetime.time:
    """Convert a 12‑hour clock string (e.g. "2:30 PM") into a time object."""
    return datetime.datetime.strptime(time_str, "%I:%M %p").time()


def _parse_time_any(raw: str) -> Optional[datetime.time]:
    """Parse user‑supplied time in several common formats (2 PM, 14:00, 2:00 p.m.)."""
    cleaned = raw.strip().replace(".", "").upper()
    # Normalise "2 PM" → "2:00 PM"
    if cleaned.endswith(" AM") or cleaned.endswith(" PM"):
        if ":" not in cleaned:
            cleaned = cleaned.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
    for fmt in ("%I:%M %p", "%H:%M", "%I %p"):
        try:
            return datetime.datetime.strptime(cleaned, fmt).time()
        except ValueError:
            continue
    return None  # un‑parsable


def _canonical_str(t: datetime.time) -> str:
    """Return time as scheduler‑canonical string (no leading zero, AM/PM)."""
    return t.strftime("%I:%M %p").lstrip("0")

# ── Public API ─────────────────────────────────────────────────────

def get_available_slots(date_str: str) -> List[str]:
    return schedule.get(date_str, [])


def book_appointment(date: str, time: str, name: str) -> str:
    target = _parse_time_any(time)
    if target is None:
        return f"I couldn't understand the time '{time}'."

    slots = schedule.get(date, [])
    for slot in list(slots):  # iterate over a snapshot
        if _time_key(slot) == target:
            slots.remove(slot)
            booked.setdefault(date, {})[slot] = name
            return f"Appointment confirmed for {name} on {date} at {slot}."

    return f"{_canonical_str(target)} on {date} is no longer available."


def cancel_appointment(date: str, time: str, name: str) -> str:
    target = _parse_time_any(time)
    if target is None:
        return "I couldn't understand the time you gave me."

    # locate exact stored slot string (might differ in formatting)
    for slot in booked.get(date, {}):
        if _time_key(slot) == target and booked[date][slot] == name:
            booked[date].pop(slot)
            schedule.setdefault(date, []).append(slot)
            schedule[date].sort(key=_time_key)
            return f"Your appointment on {date} at {slot} has been cancelled."

    return "I couldn’t find that appointment in our system."


def next_available() -> Tuple[Optional[str], Optional[str]]:
    for d, slots in sorted(schedule.items()):
        if slots:
            slots.sort(key=_time_key)
            return d, slots[0]
    return None, None


def human_readable_slots(date: str) -> str:
    slots = get_available_slots(date)
    return ", ".join(slots) if slots else "no remaining times"
