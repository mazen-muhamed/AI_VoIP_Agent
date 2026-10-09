from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")

PERIOD_DAYS = {"today": 1, "7d": 7, "30d": 30,}


def get_period_utc_range(period: str) -> tuple[datetime, datetime]:
    if period not in PERIOD_DAYS:
        raise ValueError("Invalid period")

    now_cairo = datetime.now(CAIRO_TZ)
    today = now_cairo.date()

    if period == "today":
        start_date = today
        end_date = today + timedelta(days=1)
    else:
        start_date = today - timedelta(days=PERIOD_DAYS[period] - 1)
        end_date = today + timedelta(days=1)

    start_cairo = datetime.combine(
        start_date,
        time.min,
        tzinfo=CAIRO_TZ,
    )

    end_cairo = datetime.combine(
        end_date,
        time.min,
        tzinfo=CAIRO_TZ,
    )

    return (
        start_cairo.astimezone(timezone.utc),
        end_cairo.astimezone(timezone.utc),
    )


def get_previous_period_utc_range(period: str,) -> tuple[datetime, datetime]:
    if period not in PERIOD_DAYS:
        raise ValueError("Invalid period")

    now_cairo = datetime.now(CAIRO_TZ)
    today = now_cairo.date()

    days = PERIOD_DAYS[period]

    if period == "today":
        current_start = today
    else:
        current_start = today - timedelta(days=days - 1)

    previous_end = current_start
    previous_start = previous_end - timedelta(days=days)

    start_cairo = datetime.combine(
        previous_start,
        time.min,
        tzinfo=CAIRO_TZ,
    )

    end_cairo = datetime.combine(
        previous_end,
        time.min,
        tzinfo=CAIRO_TZ,
    )

    return (
        start_cairo.astimezone(timezone.utc),
        end_cairo.astimezone(timezone.utc),
    )