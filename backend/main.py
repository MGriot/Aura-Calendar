"""Calendar API — lightweight FastAPI backend."""

import calendar
import csv
import datetime
import json
import os
import sys
import shutil
import io
import requests
import time
import tempfile
from dateutil.parser import parse as dateutil_parse

# Add root and src to sys.path to allow importing from src and internal imports within src
current_dir = os.path.dirname(os.path.abspath(__file__))
# Check if src is a subdirectory (Docker mount) or sibling (Local)
if os.path.exists(os.path.join(current_dir, "src")):
    sys.path.append(current_dir)
    sys.path.append(os.path.join(current_dir, "src"))
else:
    sys.path.append(os.path.dirname(current_dir))
    sys.path.append(os.path.join(os.path.dirname(current_dir), 'src'))

from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import holidays
from convertdate import hebrew, islamic
from lunarcalendar import Converter, Solar

# Import from mounted src
from src.calendar_utils import HolidayProvider
from src.calendar_generator import generate_calendar_table

app = FastAPI(title="Calendar API", version="1.0.0")
# ... (rest of imports and app setup)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ... (models and helper functions)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file and return its local path. Writes atomically to avoid race conditions."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, detail="Only CSV files are allowed.")
    tmp_path = None
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=UPLOAD_DIR, prefix="upload-", suffix=".tmp")
        os.close(fd)
        with open(tmp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            buffer.flush()
            try:
                os.fsync(buffer.fileno())
            except Exception:
                pass
        final_path = os.path.join(UPLOAD_DIR, file.filename)
        os.replace(tmp_path, final_path)
        # Update settings to point to the uploaded CSV so UI shows it in Settings
        try:
            s = load_settings()
            s.csv_path = os.path.abspath(final_path)
            save_settings_to_disk(s)
        except Exception as e:
            print(f"Warning: failed to persist csv_path to settings: {e}")
        return {"status": "ok", "path": os.path.abspath(final_path), "filename": file.filename}
    except Exception as e:
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        raise HTTPException(500, detail=str(e))

# ... (other endpoints)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")


# ── Models ────────────────────────────────────────────────
class Settings(BaseModel):
    csv_path: str = ""
    external_url: str = ""
    col_start_date: str = "start_date"
    col_end_date: str = "end_date"
    col_event_name: str = "event_name"
    col_category: str = "category"
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


TAGS_FILE = os.path.join(os.path.dirname(__file__), "tags_config.json")
SPECIAL_DAYS_FILE = os.path.join(os.path.dirname(__file__), "special_days.json")


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

def try_parse_date(val: str, primary_fmt: str) -> datetime.date:
    """Try parsing a date string using the configured primary format first, then a set of common fallbacks.
    Returns a datetime.date on success or raises ValueError on failure.
    """
    if not val:
        raise ValueError("Empty date")

    # Try primary format first (keeps existing behavior when user specifies a specific format)
    try:
        return datetime.datetime.strptime(val, primary_fmt).date()
    except Exception:
        pass

    # Common fallbacks (two/ four digit years, different separators)
    fallbacks = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%d-%m-%y",
        "%d/%m/%y",
        "%m/%d/%y",
        "%y-%m-%d",
    ]
    for fmt in fallbacks:
        try:
            return datetime.datetime.strptime(val, fmt).date()
        except Exception:
            continue

    # Last resort: use dateutil's parse which handles many human formats
    try:
        dt = dateutil_parse(val, dayfirst=True)
        return dt.date()
    except Exception as e:
        raise ValueError(f"Unrecognized date format: {val}")

def load_events_from_csv(settings: Settings) -> list:
    path = settings.csv_path
    if not path:
        return []
    
    # If path is a remote URL, we'll stream it; otherwise resolve local paths relative to backend dir
    if path.lower().startswith("http://") or path.lower().startswith("https://"):
        # remote URL — skip local existence check
        pass
    else:
        # Resolve relative paths relative to current dir (where main.py is)
        if not os.path.isabs(path):
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
        if not os.path.exists(path):
            print(f"ERROR: CSV path not found: {path}")
            return []

    events = []
    try:
        # Load CSV content into memory (avoids 'I/O operation on closed file' when using DictReader on file objects)
        if path.lower().startswith("http://") or path.lower().startswith("https://"):
            r = requests.get(path, timeout=15)
            r.raise_for_status()
            text = r.text
        else:
            # Try a few times in case the file is still being written by an uploader
            attempts = 3
            text = None
            for attempt in range(attempts):
                try:
                    with open(path, "r", encoding="utf-8-sig") as f:
                        text = f.read()
                    break
                except Exception as e:
                    if attempt < attempts - 1:
                        time.sleep(0.2)
                        continue
                    else:
                        raise
        reader = csv.DictReader(io.StringIO(text))
        for row in reader:
                try:
                    start_val = row.get(settings.col_start_date, "").strip()
                    if not start_val: continue
                    
                    start = try_parse_date(start_val, settings.date_format)
                    
                    end_raw = row.get(settings.col_end_date, "").strip()
                    end = (try_parse_date(end_raw, settings.date_format) if end_raw else start)
                    events.append(
                        {
                            "start_date": start.isoformat(),
                            "end_date": end.isoformat(),
                            "title": row.get(settings.col_event_name, "Untitled").strip(),
                            "category": row.get(settings.col_category, "default").strip(),
                            "data": {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                        }
                    )
                except (KeyError, ValueError) as e:
                    # print(f"DEBUG: skip row due to {e}")
                    continue
    except Exception as e:
        print(f"ERROR: Failed to read CSV {path}: {e}")
        return []
    return events


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


# ── CSV Preview ───────────────────────────────────────────
@app.get("/api/csv/preview")
def preview_csv(path: str):
    """Read first few rows of a CSV to help with mapping.

    Supports local file paths and remote URLs. Remote files are streamed and not persisted.
    """
    try:
        if path.lower().startswith("http://") or path.lower().startswith("https://"):
            # Stream remote CSV without saving to disk
            r = requests.get(path, timeout=15)
            r.raise_for_status()
            text = r.text
        else:
            if not os.path.exists(path):
                # Try resolving relative to backend dir
                if not os.path.isabs(path):
                    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), path)
                if not os.path.exists(path):
                    raise HTTPException(404, detail=f"File not found: {path}")
            # load into memory to avoid file-handle races
            with open(path, "r", encoding="utf-8-sig") as f:
                text = f.read()

        reader = csv.DictReader(io.StringIO(text))
        headers = reader.fieldnames or []
        preview_rows = []
        for i, row in enumerate(reader):
            if i >= 5: break
            preview_rows.append(row)
        return {"headers": headers, "preview_rows": preview_rows}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))


def get_advanced_data(start_date: datetime.date, end_date: datetime.date, settings: Settings):
    advanced_map = {}
    if settings.enable_advanced_calendar:
        try:
            df = generate_calendar_table(
                start_date.isoformat(), 
                end_date.isoformat(), 
                freq="D",
                countries=settings.advanced_countries,
                n_workers=1
            )
            
            if df is not None:
                import pandas as pd
                df = df.where(pd.notnull(df), None)
                records = df.to_dict("records")
                for rec in records:
                    d_key = rec.get('date_utc')
                    if hasattr(d_key, 'strftime'):
                        d_key = d_key.strftime('%Y-%m-%d')
                    elif isinstance(d_key, datetime.date):
                        d_key = d_key.isoformat()
                    
                    if d_key:
                        adv = {
                            "fiscal_month": rec.get("ITTFiscalMonth"),
                            "fiscal_week": rec.get("ITTFiscalWeek"),
                            "is_fiscal_start": bool(rec.get("is_first_day_of_fiscal_period")) if rec.get("is_first_day_of_fiscal_period") is not None else False,
                            "is_fiscal_end": bool(rec.get("is_last_day_of_fiscal_period")) if rec.get("is_last_day_of_fiscal_period") is not None else False,
                            "week_of_month": rec.get("WeekOfMonth"),
                            "is_last_week_month": bool(rec.get("IsLastWeekOfMonth")) if rec.get("IsLastWeekOfMonth") is not None else False,
                            "season": rec.get("season_astronomical"),
                            "holidays": {
                                c: rec.get(f"HolidayName_{c}") 
                                for c in settings.advanced_countries 
                                if rec.get(f"HolidayName_{c}")
                            },
                            "is_business": {
                                c: bool(rec.get(f"IsBusinessDay_{c}")) if rec.get(f"IsBusinessDay_{c}") is not None else True
                                for c in settings.advanced_countries
                            }
                        }
                        advanced_map[d_key] = adv
        except Exception as e:
            print(f"Advanced calendar generation failed: {e}")
    return advanced_map


def get_multicultural_map(start_date: datetime.date, end_date: datetime.date, settings: Settings):
    return HolidayProvider.get_holidays(
        start_date, 
        end_date, 
        settings.advanced_countries, 
        settings.enabled_cultural_calendars
    )


# ── Endpoints ─────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/calendar")
def get_calendar(
    start_month: int = Query(default=1, ge=1, le=12),
    start_year: int = Query(default=2026, ge=1900, le=2100),
    num_months: int = Query(default=4, ge=1, le=12),
):
    data = generate_calendar_data(start_month, start_year, num_months)

    settings = load_settings()
    events = load_events_from_csv(settings)
    
    special_days = load_special_days()
    tags_config = load_tags_config()

    # Index events by date for O(1) lookup
    by_date: dict[str, list] = {}
    for ev in events:
        cur = datetime.date.fromisoformat(ev["start_date"])
        end = datetime.date.fromisoformat(ev["end_date"])
        while cur <= end:
            by_date.setdefault(cur.isoformat(), []).append(
                {
                    "title": ev["title"],
                    "category": ev["category"],
                    "is_start": cur == datetime.date.fromisoformat(ev["start_date"]),
                    "is_end": cur == end,
                }
            )
            cur += datetime.timedelta(days=1)
            
    # Index special days (both absolute and recurring)
    special_days = load_special_days()
    abs_special = {d.date: d for d in special_days if not d.is_recurring and d.date}
    rec_special = {(d.month, d.day): d for d in special_days if d.is_recurring and d.month and d.day}

    # Advanced calendar data
    start_date = datetime.date(start_year, start_month, 1)
    # End date calculation
    y, m = start_year, start_month
    for _ in range(num_months):
        m += 1
        if m > 12:
            m = 1
            y += 1
    end_date = datetime.date(y, m, 1) - datetime.timedelta(days=1)
    
    advanced_map = get_advanced_data(start_date, end_date, settings)
    multi_map = get_multicultural_map(start_date, end_date, settings)
    
    for month in data:
        for week in month["weeks"]:
            for day in week["days"]:
                d_str = day["date"]
                dt_obj = datetime.date.fromisoformat(d_str)
                
                # Tier 1: CSV Events
                day["tier1"] = by_date.get(d_str, [])
                day["events"] = day["tier1"]
                
                # Tier 2: Special Days
                sd = abs_special.get(d_str) or rec_special.get((dt_obj.month, dt_obj.day))
                day["tier2"] = {
                    "tags": sd.tags if sd else [],
                    "where": sd.where if sd else [],
                    "is_recurring": sd.is_recurring if sd else False
                }
                day["special_tags"] = day["tier2"]["tags"]
                day["where"] = day["tier2"]["where"]
                
                # Tier 3: Unified Metadata
                tier3_items = multi_map.get(d_str, [])
                adv = advanced_map.get(d_str)
                
                day["tier3"] = {
                    "cultural": tier3_items,
                    "advanced": adv
                }
                day["advanced"] = adv

    return {
        "months": data, 
        "events": events, 
        "settings": settings, 
        "special_days": special_days,
        "tags_config": tags_config
    }


@app.get("/api/settings")
def get_settings():
    return load_settings()


@app.post("/api/settings")
def update_settings(settings: Settings):
    save_settings_to_disk(settings)
    count = len(load_events_from_csv(settings)) if settings.csv_path else 0
    return {"status": "ok", "events_loaded": count, "settings": settings}


@app.get("/api/stats")
def get_stats():
    """Return summary stats for all loaded events."""
    settings = load_settings()
    events = load_events_from_csv(settings)
    
    total = len(events)
    categories = {}
    
    now = datetime.date.today()
    next_event = None
    min_delta = datetime.timedelta(days=99999)

    for ev in events:
        cat = ev.get("category", "default")
        categories[cat] = categories.get(cat, 0) + 1
        
        # Find next event
        start = datetime.date.fromisoformat(ev["start_date"])
        if start >= now:
            delta = start - now
            if delta < min_delta:
                min_delta = delta
                next_event = ev

    return {
        "total_events": total,
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
    if year and month and day:
        try:
            anchor = datetime.date(year, month, day)
        except ValueError:
            anchor = today
    else:
        anchor = today
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
        
    settings = load_settings()
    events = load_events_from_csv(settings)
    special_days = load_special_days()
    abs_special = {d.date: d for d in special_days if not d.is_recurring and d.date}
    rec_special = {(d.month, d.day): d for d in special_days if d.is_recurring and d.month and d.day}
    
    # Advanced data for the week — convert to datetime.date objects
    week_start_date = datetime.date.fromisoformat(week_days[0]["date"])
    week_end_date   = datetime.date.fromisoformat(week_days[-1]["date"])
    advanced_map = get_advanced_data(week_start_date, week_end_date, settings)
    multi_map = get_multicultural_map(week_start_date, week_end_date, settings)
    
    # Filter and attach events
    for day in week_days:
        d_iso = day["date"]
        dt_obj = datetime.date.fromisoformat(d_iso)
        
        # Tier 1: CSV Events
        day_events = []
        for ev in events:
            if ev["start_date"] <= d_iso <= ev["end_date"]:
                day_events.append(ev)
        day["tier1"] = day_events
        day["events"] = day_events # legacy
        
        # Tier 2: Special Days
        sd = abs_special.get(d_iso) or rec_special.get((dt_obj.month, dt_obj.day))
        day["tier2"] = {
            "tags": sd.tags if sd else [],
            "where": sd.where if sd else [],
            "is_recurring": sd.is_recurring if sd else False
        }
        # legacy
        day["special_tags"] = day["tier2"]["tags"]
        day["where"] = day["tier2"]["where"]
            
        # Tier 3: Cultural Calendars
        tier3_items = multi_map.get(d_iso, [])
        adv = advanced_map.get(d_iso)
        day["tier3"] = {
            "cultural": tier3_items,
            "advanced": adv
        }
        day["advanced"] = adv # legacy
            
    return {"days": week_days}


@app.get("/api/events/all")
def get_all_events():
    """Return all events sorted by start date."""
    settings = load_settings()
    events = load_events_from_csv(settings)
    
    # Sort by start_date
    events.sort(key=lambda x: x["start_date"])
    return {"events": events}


@app.get("/api/tags")
def get_tags():
    return load_tags_config()


@app.post("/api/tags")
def update_tags(config: TagsConfig):
    save_tags_config(config)
    return {"status": "ok", "config": config}


@app.get("/api/special-days")
def get_all_special_days():
    return load_special_days()


@app.post("/api/special-days/assign")
def assign_special_days(req: AssignRequest):
    current_days = load_special_days()
    # We use a composite key: (date if not recurring else None, month if recurring else None, day if recurring else None)
    # But simpler: just key by date for absolute, and a separate logic for recurring.
    # To keep it simple for now, we'll store them all in one list and update by match.
    
    for date_str in req.dates:
        dt = datetime.date.fromisoformat(date_str)
        found = False
        
        if req.is_recurring:
            # Look for existing recurring entry for this month/day
            for d in current_days:
                if d.is_recurring and d.month == dt.month and d.day == dt.day:
                    d.tags = req.tags
                    d.where = req.where
                    found = True
                    break
            if not found:
                current_days.append(SpecialDay(
                    month=dt.month, 
                    day=dt.day, 
                    is_recurring=True, 
                    tags=req.tags, 
                    where=req.where
                ))
        else:
            # Look for existing absolute entry for this date
            for d in current_days:
                if not d.is_recurring and d.date == date_str:
                    d.tags = req.tags
                    d.where = req.where
                    found = True
                    break
            if not found:
                current_days.append(SpecialDay(
                    date=date_str, 
                    is_recurring=False, 
                    tags=req.tags, 
                    where=req.where
                ))
            
    # Clean up: remove entries with no tags and no where
    final_days = [d for d in current_days if d.tags or d.where]
    save_special_days(final_days)
    return {"status": "ok", "count": len(req.dates)}
