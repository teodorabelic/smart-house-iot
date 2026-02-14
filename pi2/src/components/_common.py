from datetime import datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Belgrade")

def iso_now():
    return datetime.now(TZ).isoformat()
