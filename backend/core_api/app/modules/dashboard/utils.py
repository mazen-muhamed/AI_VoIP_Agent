from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

CAIRO_TZ = ZoneInfo("Africa/Cairo")


def get_today_utc_range():
    now_cairo = datetime.now(CAIRO_TZ)
    today = now_cairo.date()

    start_cairo = datetime.combine(
        today,
        time.min,
        tzinfo=CAIRO_TZ,
    )

    end_cairo = datetime.combine(
        today + timedelta(days=1),
        time.min,
        tzinfo=CAIRO_TZ,
    )

    return (
        start_cairo.astimezone(timezone.utc),
        end_cairo.astimezone(timezone.utc),
    )