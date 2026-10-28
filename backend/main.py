"""Calendar API — lightweight FastAPI backend."""

import asyncio
import calendar
import contextlib
import csv
import datetime
import functools
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time

import requests
from dateutil.parser import parse as dateutil_parse

# Add root and src to sys.path to allow importing from src and internal imports within src
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check if src is a subdirectory (Docker mount) or sibling (Local)
if os.path.exists(os.path.join(current_dir, "src", "calendar_utils.py")):
    sys.path.append(current_dir)
    sys.path.append(os.path.join(current_dir, "src"))
else:
    sys.path.append(os.path.dirname(current_dir))
    sys.path.append(os.path.join(os.path.dirname(current_dir), 'src'))

from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import from mounted src
from src.calendar_utils import HolidayProvider
from src.calendar_generator import generate_calendar_table

UPLOAD_DIR = os.path.join(current_dir, "uploads")
SETTINGS_FILE = os.path.join(current_dir, "settings.json")
TAGS_FILE = os.path.join(current_dir, "tags_config.json")
SPECIAL_DAYS_FILE = os.path.join(current_dir, "special_days.json")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Local CSVs may only be read from these directories (extend with CSV_ALLOWED_DIRS, os.pathsep-separated)
CSV_ALLOWED_DIRS = [
    os.path.realpath(d)
    for d in [UPLOAD_DIR, os.path.join(os.path.dirname(current_dir), "data"), "/data",
              *filter(None, os.environ.get("CSV_ALLOWED_DIRS", "").split(os.pathsep))]
]

# Browser origins allowed to call the API directly (the UI itself goes through the same-origin proxy)
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]


# ── Models ────────────────────────────────────────────────
class Settings(BaseModel):
    csv_path: str = ""
    external_url: str = ""
    col_start_date: str = "start_date"
    col_end_date: str = "end_date"
    col_event_name: str = "event_name"
    col_category: str = "category"
    col_status: str = ""
    col_type: str = ""
    date_format: str = "%Y-%m-%d"
    color_map: dict[str, str] = {} # { category_value: hex_color }
    reload_interval: int = 0 # in minutes, 0 = manual
    enable_advanced_calendar: bool = False
    advanced_countries: list[str] = ["IT", "US", "MX", "CZ"] # Default supported
    show_special_days: bool = True
    enabled_cultural_calendars: list[str] = ["holidays_it", "holidays_us", "holidays_mx", "holidays_cz", "lunar", "hebrew", "islamic", "catholic"]
    # Markdown template for per-event detail card. Use {{field_name}} to inject CSV columns or event properties.
    # Example: "**{{title}}**\nCategory: {{category}}\nLocation: {{place}}"
    event_card_template: str = "**{{title}}**\nCategory: {{category}}\nFrom: {{start_date}}\nTo: {{end_date}}"


class SpecialDay(BaseModel):
    date: str = "" # YYYY-MM-DD
    month: int | None = None
    day: int | None = None
    is_recurring: bool = False
    tags: list[str] = []
    where: list[str] = []


class AssignRequest(BaseModel):
    dates: list[str]
    tags: list[str] = []
    where: list[str] = []
    is_recurring: bool = False


class TagConfigItem(BaseModel):
    id: str
    label: str
    color: str


class TagsConfig(BaseModel):
    primary: list[TagConfigItem] = []
    where: list[TagConfigItem] = []


# ── Settings persistence ──────────────────────────────────
def load_settings() -> Settings:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            raw = json.load(f)
        s = Settings(**raw)
        # Auto-heal: if disk file is missing any fields, rewrite with full model
        if set(raw.keys()) != set(s.model_dump().keys()):
            save_settings_to_disk(s)
        return s
    return Settings()


def save_settings_to_disk(settings: Settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)


def load_tags_config() -> TagsConfig:
    if os.path.exists(TAGS_FILE):
        with open(TAGS_FILE, "r") as f:
            return TagsConfig(**json.load(f))
    return TagsConfig()


def save_tags_config(config: TagsConfig):
    with open(TAGS_FILE, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def load_special_days() -> list[SpecialDay]:
    if os.path.exists(SPECIAL_DAYS_FILE):
        with open(SPECIAL_DAYS_FILE, "r") as f:
            data = json.load(f)
            return [SpecialDay(**d) for d in data]
    return []


def save_special_days(days: list[SpecialDay]):
    with open(SPECIAL_DAYS_FILE, "w") as f:
        json.dump([d.model_dump() for d in days], f, indent=2)


# ── CSV event loader ──────────────────────────────────────
DATE_FALLBACKS = [
    "%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d",
    "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%m/%d/%Y",
    "%d-%m-%y", "%d/%m/%y", "%d.%m.%y", "%m/%d/%y",
    "%y-%m-%d", "%y/%m/%d", "%y.%m.%d",
]


def try_parse_date(val: str, primary_fmt: str) -> datetime.date:
    """Try parsing a date string using the configured primary format first, then a set of common fallbacks.
    Returns a datetime.date on success or raises ValueError on failure.
    """
    if not val:
        raise ValueError("Empty date")
    for fmt in [primary_fmt, *DATE_FALLBACKS]:
        try:
            return datetime.datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    # Last resort: use dateutil's parse which handles many human formats
    try:
        return dateutil_parse(val, dayfirst=True).date()
    except Exception:
        raise ValueError(f"Unrecognized date format: {val}")


def is_url(path: str) -> bool:
    return path.lower().startswith(("http://", "https://"))


def resolve_local_csv(path: str) -> str:
    """Resolve a local CSV path (relative paths resolve against the backend dir) and make sure it
    lives inside CSV_ALLOWED_DIRS. Raises PermissionError otherwise."""
    if not os.path.isabs(path):
        path = os.path.join(current_dir, path)
    real = os.path.realpath(path)
    if not real.lower().endswith(".csv"):
        raise PermissionError("Only .csv files can be read")
    for root in CSV_ALLOWED_DIRS:
        try:
            if os.path.commonpath([real, root]) == root:
                return real
        except ValueError:  # different drives on Windows
            continue
    raise PermissionError(f"Path is outside the allowed CSV directories: {path}")


def read_csv_text(path: str) -> str:
    """Return the CSV content of an http(s) URL or an allowed local path.
    Raises FileNotFoundError when a local file does not exist and PermissionError when it is not allowed."""
    if is_url(path):
        r = requests.get(path, timeout=15, allow_redirects=False)
        r.raise_for_status()
        return r.text
    if "://" in path:
        raise PermissionError("Only http(s) URLs are supported")
    path = resolve_local_csv(path)
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    # Try a few times in case the file is still being written by an uploader
    for attempt in range(3):
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                return f.read()
        except OSError:
            if attempt == 2:
                raise
            time.sleep(0.2)


def parse_events(text: str, settings: Settings) -> list:
    events = []
    for row in csv.DictReader(io.StringIO(text)):
        try:
            start_val = (row.get(settings.col_start_date) or "").strip()
            if not start_val:
                continue
            start = try_parse_date(start_val, settings.date_format)
            end_raw = (row.get(settings.col_end_date) or "").strip()
            end = try_parse_date(end_raw, settings.date_format) if end_raw else start
            events.append(
                {
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "title": (row.get(settings.col_event_name) or "Untitled").strip(),
                    "category": (row.get(settings.col_category) or "default").strip(),
                    "status": (row.get(settings.col_status) or "").strip() if settings.col_status else "",
                    "type": (row.get(settings.col_type) or "").strip() if settings.col_type else "",
                    "data": {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                }
            )
        except ValueError:
            continue
    return events


def index_events_by_date(events: list) -> dict[str, list]:
    """Map ISO date -> list of event slices covering that date."""
    by_date: dict[str, list] = {}
    for ev in events:
        start = datetime.date.fromisoformat(ev["start_date"])
        end = datetime.date.fromisoformat(ev["end_date"])
        cur = start
        while cur <= end:
            by_date.setdefault(cur.isoformat(), []).append(
                {**ev, "is_start": cur == start, "is_end": cur == end}
            )
            cur += datetime.timedelta(days=1)
    return by_date


def load_events_from_csv(settings: Settings) -> list:
    path = settings.external_url.strip() if settings.external_url else settings.csv_path
    if not path:
        return []
    try:
        return parse_events(read_csv_text(path), settings)
    except Exception as e:
        print(f"ERROR: Failed to read CSV {path}: {e}")
        return []


# ── Event store (cached data + scheduled refresh) ─────────
class EventStore:
    """Caches parsed events and refreshes them every `reload_interval` minutes.

    Every refresh that changes the data bumps `version` and is pushed to SSE subscribers,
    so all connected UIs reload at the same moment the backend does.
    """

    def __init__(self):
        self.events: list = []
        self.by_date: dict[str, list] = {}
        self.version = ""
        self.last_refresh: float | None = None
        self.next_refresh: float | None = None
        self._revision = 0  # bumped by local edits (special days, tags) that don't touch the CSV
        self._data_hash = ""
        self._lock = asyncio.Lock()
        self._wake = asyncio.Event()
        self._subscribers: set[asyncio.Queue] = set()

    def snapshot(self) -> dict:
        settings = load_settings()
        return {
            "version": self.version,
            "last_refresh": self.last_refresh,
            "next_refresh": self.next_refresh,
            "interval": settings.reload_interval,
        }

    def _set_version(self):
        new_version = hashlib.sha1(f"{self._data_hash}:{self._revision}".encode()).hexdigest()[:12]
        changed = new_version != self.version
        self.version = new_version
        return changed

    async def refresh(self) -> bool:
        """Reload events from the configured source. Returns True when the data changed."""
        async with self._lock:
            settings = load_settings()
            events = await asyncio.to_thread(load_events_from_csv, settings)
            payload = json.dumps([events, settings.model_dump()], sort_keys=True, default=str)
            self._data_hash = hashlib.sha1(payload.encode()).hexdigest()
            self.events = events
            self.by_date = index_events_by_date(events)
            self.last_refresh = time.time()
            interval = settings.reload_interval
            self.next_refresh = self.last_refresh + interval * 60 if interval > 0 else None
            changed = self._set_version()
        self._notify()
        return changed

    def bump(self):
        """Signal a local data change (special days/tags) so other open UIs reload."""
        self._revision += 1
        self._set_version()
        self._notify()

    def reschedule(self):
        """Wake the scheduler so a new interval takes effect immediately."""
        self._wake.set()

    def _notify(self):
        message = self.snapshot()
        for q in list(self._subscribers):
            q.put_nowait(message)

    async def run_scheduler(self):
        while True:
            timeout = self.next_refresh - time.time() if self.next_refresh else None
            self._wake.clear()
            try:
                await asyncio.wait_for(self._wake.wait(), timeout=max(timeout, 0) if timeout is not None else None)
            except asyncio.TimeoutError:
                try:
                    await self.refresh()
                except Exception as e:
                    print(f"Scheduled refresh failed: {e}")

    @contextlib.contextmanager
    def subscribe(self):
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        try:
            yield q
        finally:
            self._subscribers.discard(q)


store = EventStore()


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI):
    await store.refresh()
    task = asyncio.create_task(store.run_scheduler())
    yield
    task.cancel()


app = FastAPI(title="Calendar API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ── Calendar generation (stdlib only) ─────────────────────
def generate_calendar_data(start_month: int, start_year: int, num_months: int):
    cal = calendar.Calendar(firstweekday=0)  # Monday start
    months_data = []
    cur_m, cur_y = start_month, start_year

    for _ in range(num_months):
        weeks = []
        for week_dates in cal.monthdatescalendar(cur_y, cur_m):
            cw = week_dates[3].isocalendar()[1]
            days = []
            for d in week_dates:
                days.append({
                    "date": d.isoformat(),
                    "day": d.day,
                    "day_of_week": d.weekday(),
                    "is_current_month": d.month == cur_m,
                })
            weeks.append({"cw": cw, "days": days})

        months_data.append({
            "year": cur_y,
            "month": cur_m,
            "month_name": calendar.month_name[cur_m],
            "weeks": weeks,
        })
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_y += 1
    return months_data


@functools.lru_cache(maxsize=32)
def _advanced_data_cached(start_iso: str, end_iso: str, countries: tuple[str, ...]) -> dict:
    import pandas as pd
    advanced_map = {}
    df = generate_calendar_table(start_iso, end_iso, freq="D", countries=list(countries), n_workers=1)
    if df is None:
        return advanced_map

    def flag(rec, key, default=False):
        return bool(rec.get(key)) if rec.get(key) is not None else default

    df = df.where(pd.notnull(df), None)
    for rec in df.to_dict("records"):
        d_key = rec.get('date_utc')
        if hasattr(d_key, 'strftime'):
            d_key = d_key.strftime('%Y-%m-%d')
        if not d_key:
            continue
        advanced_map[d_key] = {
            "fiscal_month": rec.get("ITTFiscalMonth"),
            "fiscal_week": rec.get("ITTFiscalWeek"),
            "is_fiscal_start": flag(rec, "is_first_day_of_fiscal_period"),
            "is_fiscal_end": flag(rec, "is_last_day_of_fiscal_period"),
            "week_of_month": rec.get("WeekOfMonth"),
            "is_last_week_month": flag(rec, "IsLastWeekOfMonth"),
            "season": rec.get("season_astronomical"),
            "holidays": {c: rec.get(f"HolidayName_{c}") for c in countries if rec.get(f"HolidayName_{c}")},
            "is_business": {c: flag(rec, f"IsBusinessDay_{c}", True) for c in countries},
        }
    return advanced_map


def get_advanced_data(start_date: datetime.date, end_date: datetime.date, settings: Settings):
    if not settings.enable_advanced_calendar:
        return {}
    try:
        return _advanced_data_cached(start_date.isoformat(), end_date.isoformat(), tuple(settings.advanced_countries))
    except Exception as e:
        print(f"Advanced calendar generation failed: {e}")
        return {}


def get_multicultural_map(start_date: datetime.date, end_date: datetime.date, settings: Settings):
    return HolidayProvider.get_holidays(
        start_date,
        end_date,
        settings.advanced_countries,
        settings.enabled_cultural_calendars
    )


class DayEnricher:
    """Attaches tier1 (CSV events), tier2 (special days) and tier3 (cultural/advanced) data to day dicts."""

    def __init__(self, start_date: datetime.date, end_date: datetime.date, settings: Settings, special_days: list[SpecialDay]):
        self.abs_special = {d.date: d for d in special_days if not d.is_recurring and d.date}
        self.rec_special = {(d.month, d.day): d for d in special_days if d.is_recurring and d.month and d.day}
        self.advanced_map = get_advanced_data(start_date, end_date, settings)
        self.multi_map = get_multicultural_map(start_date, end_date, settings)

    def enrich(self, day: dict):
        d_str = day["date"]
        dt_obj = datetime.date.fromisoformat(d_str)

        # Tier 1: CSV Events
        day["tier1"] = store.by_date.get(d_str, [])
        day["events"] = day["tier1"]  # legacy

        # Tier 2: Special Days
        sd = self.abs_special.get(d_str) or self.rec_special.get((dt_obj.month, dt_obj.day))
        day["tier2"] = {
            "tags": sd.tags if sd else [],
            "where": sd.where if sd else [],
            "is_recurring": sd.is_recurring if sd else False
        }
        day["special_tags"] = day["tier2"]["tags"]  # legacy
        day["where"] = day["tier2"]["where"]  # legacy

        # Tier 3: Unified Metadata
        adv = self.advanced_map.get(d_str)
        day["tier3"] = {"cultural": self.multi_map.get(d_str, []), "advanced": adv}
        day["advanced"] = adv  # legacy


# ── Endpoints ─────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file and return its local path. Writes atomically to avoid race conditions."""
    # Keep only the base name so "../../x.csv" can't escape UPLOAD_DIR
    filename = os.path.basename((file.filename or "").replace("\\", "/"))
    if not filename.lower().endswith(".csv") or filename.startswith("."):
        raise HTTPException(400, detail="Only CSV files are allowed.")
    tmp_path = None
    try:
        fd, tmp_path = tempfile.mkstemp(dir=UPLOAD_DIR, prefix="upload-", suffix=".tmp")
        os.close(fd)
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            buffer.flush()
            with contextlib.suppress(OSError):
                os.fsync(buffer.fileno())
        final_path = os.path.join(UPLOAD_DIR, filename)
        os.replace(tmp_path, final_path)
        # Update settings to point to the uploaded CSV so UI shows it in Settings
        try:
            s = load_settings()
            s.csv_path = os.path.abspath(final_path)
            save_settings_to_disk(s)
        except Exception as e:
            print(f"Warning: failed to persist csv_path to settings: {e}")
        await store.refresh()
        return {"status": "ok", "path": os.path.abspath(final_path), "filename": filename}
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            with contextlib.suppress(OSError):
                os.remove(tmp_path)
        raise HTTPException(500, detail=str(e))


@app.get("/api/csv/preview")
def preview_csv(path: str):
    """Read first few rows of a CSV to help with mapping.

    Supports local CSVs inside CSV_ALLOWED_DIRS and http(s) URLs. Remote files are streamed and not persisted.
    """
    try:
        text = read_csv_text(path)
    except PermissionError as e:
        raise HTTPException(403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, detail=f"File not found: {e}")
    except Exception as e:
        raise HTTPException(500, detail=str(e))
    reader = csv.DictReader(io.StringIO(text))
    headers = reader.fieldnames or []
    preview_rows = []
    for i, row in enumerate(reader):
        if i >= 5:
            break
        preview_rows.append(row)
    return {"headers": headers, "preview_rows": preview_rows}


@app.get("/api/version")
def get_version():
    """Current data version and refresh schedule (epoch seconds)."""
    return store.snapshot()


@app.post("/api/refresh")
async def force_refresh():
    """Reload events now and restart the refresh timer."""
    changed = await store.refresh()
    store.reschedule()
    return {**store.snapshot(), "changed": changed}


@app.get("/api/events/stream")
async def stream_events():
    """Server-Sent Events: emits the store snapshot on connect and after every refresh."""
    async def gen():
        with store.subscribe() as q:
            yield f"data: {json.dumps(store.snapshot())}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=25)
                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/calendar")
def get_calendar(
    start_month: int = Query(default=1, ge=1, le=12),
    start_year: int = Query(default=2026, ge=1900, le=2100),
    num_months: int = Query(default=4, ge=1, le=12),
):
    data = generate_calendar_data(start_month, start_year, num_months)
    settings = load_settings()
    special_days = load_special_days()

    start_date = datetime.date(start_year, start_month, 1)
    last = data[-1]
    end_date = datetime.date(last["year"], last["month"], calendar.monthrange(last["year"], last["month"])[1])

    enricher = DayEnricher(start_date, end_date, settings, special_days)
    for month in data:
        for week in month["weeks"]:
            for day in week["days"]:
                enricher.enrich(day)

    return {
        "months": data,
        "events": store.events,
        "settings": settings,
        "special_days": special_days,
        "tags_config": load_tags_config(),
        "version": store.version,
    }


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.post("/api/settings")
async def update_settings(settings: Settings):
    save_settings_to_disk(settings)
    await store.refresh()
    store.reschedule()
    return {"status": "ok", "events_loaded": len(store.events), "settings": settings}


@app.get("/api/stats")
def get_stats():
    """Return summary stats for all loaded events."""
    events = store.events
    categories = {}
    today = datetime.date.today().isoformat()
    next_event = None

    for ev in events:
        cat = ev.get("category", "default")
        categories[cat] = categories.get(cat, 0) + 1
        if ev["start_date"] >= today and (next_event is None or ev["start_date"] < next_event["start_date"]):
            next_event = ev

    return {
        "total_events": len(events),
        "categories": categories,
        "next_event": next_event,
    }


@app.get("/api/week")
def get_week(
    year: int = Query(default=None),
    month: int = Query(default=None),
    day: int = Query(default=None),
):
    """Return a week's days and events. Defaults to current week if no date given."""
    today = datetime.date.today()
    anchor = today
    if year and month and day:
        with contextlib.suppress(ValueError):
            anchor = datetime.date(year, month, day)
    # Find Monday of the anchor week
    start_of_week = anchor - datetime.timedelta(days=anchor.weekday())

    week_days = []
    for i in range(7):
        d = start_of_week + datetime.timedelta(days=i)
        week_days.append({
            "date": d.isoformat(),
            "day": d.day,
            "month_name": calendar.month_name[d.month],
            "day_name": calendar.day_name[d.weekday()],
            "is_today": d == today
        })

    enricher = DayEnricher(start_of_week, start_of_week + datetime.timedelta(days=6), load_settings(), load_special_days())
    for d in week_days:
        enricher.enrich(d)
    return {"days": week_days}


@app.get("/api/events/all")
def get_all_events():
    """Return all events sorted by start date."""
    return {"events": sorted(store.events, key=lambda x: x["start_date"])}


@app.get("/api/tags")
def get_tags():
    return load_tags_config()


@app.post("/api/tags")
def update_tags(config: TagsConfig):
    save_tags_config(config)
    store.bump()
    return {"status": "ok", "config": config}


@app.get("/api/special-days")
def get_all_special_days():
    return load_special_days()


@app.post("/api/special-days/assign")
def assign_special_days(req: AssignRequest):
    current_days = load_special_days()

    for date_str in req.dates:
        dt = datetime.date.fromisoformat(date_str)
        if req.is_recurring:
            match = next((d for d in current_days if d.is_recurring and d.month == dt.month and d.day == dt.day), None)
            new_day = SpecialDay(month=dt.month, day=dt.day, is_recurring=True)
        else:
            match = next((d for d in current_days if not d.is_recurring and d.date == date_str), None)
            new_day = SpecialDay(date=date_str, is_recurring=False)
        if match is None:
            match = new_day
            current_days.append(match)
        match.tags = req.tags
        match.where = req.where

    # Clean up: remove entries with no tags and no where
    save_special_days([d for d in current_days if d.tags or d.where])
    store.bump()
    return {"status": "ok", "count": len(req.dates)}
