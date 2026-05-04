"""Calendar API — lightweight FastAPI backend."""

import calendar
import csv
import datetime
import json
import os

from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shutil

app = FastAPI(title="Calendar API", version="1.0.0")
# ... (rest of imports and app setup)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# ... (models and helper functions)

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a CSV file and return its local path."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, detail="Only CSV files are allowed.")
    
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"status": "ok", "path": os.path.abspath(file_path), "filename": file.filename}
    except Exception as e:
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


class TagConfigItem(BaseModel):
    id: str
    label: str
    color: str


class TagsConfig(BaseModel):
    primary: list[TagConfigItem] = []
    where: list[TagConfigItem] = []


class SpecialDay(BaseModel):
    date: str
    tags: list[str] = []
    where: str = ""


class AssignRequest(BaseModel):
    dates: list[str]
    tags: list[str] = []
    where: str = ""


# ── Settings persistence ──────────────────────────────────
def load_settings() -> Settings:
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return Settings(**json.load(f))
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
def load_events_from_csv(settings: Settings) -> list:
    if not settings.csv_path or not os.path.exists(settings.csv_path):
        return []
    events = []
    try:
        with open(settings.csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    start = datetime.datetime.strptime(
                        row[settings.col_start_date].strip(),
                        settings.date_format,
                    ).date()
                    end_raw = row.get(settings.col_end_date, "").strip()
                    end = (
                        datetime.datetime.strptime(end_raw, settings.date_format).date()
                        if end_raw
                        else start
                    )
                    events.append(
                        {
                            "start_date": start.isoformat(),
                            "end_date": end.isoformat(),
                            "title": row.get(settings.col_event_name, "Untitled").strip(),
                            "category": row.get(settings.col_category, "default").strip(),
                        }
                    )
                except (KeyError, ValueError):
                    continue
    except Exception:
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
            cw = week_dates[3].isocalendar()[1]  # ISO CW from Thursday
            days = [
                {
                    "date": d.isoformat(),
                    "day": d.day,
                    "day_of_week": d.weekday(),
                    "is_current_month": d.month == cur_m,
                }
                for d in week_dates
            ]
            weeks.append({"cw": cw, "days": days})

        months_data.append(
            {
                "year": cur_y,
                "month": cur_m,
                "month_name": calendar.month_name[cur_m],
                "weeks": weeks,
            }
        )
        cur_m += 1
        if cur_m > 12:
            cur_m = 1
            cur_y += 1

    return months_data


# ── CSV Preview ───────────────────────────────────────────
@app.get("/api/csv/preview")
def preview_csv(path: str):
    """Read first few rows of a CSV to help with mapping."""
    if not os.path.exists(path):
        raise HTTPException(404, detail=f"File not found: {path}")
    
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            preview_rows = []
            for i, row in enumerate(reader):
                if i >= 5: break
                preview_rows.append(row)
            return {"headers": headers, "preview_rows": preview_rows}
    except Exception as e:
        raise HTTPException(500, detail=str(e))


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
            
    # Index special days by date
    special_by_date = {d.date: d for d in special_days}

    for month in data:
        for week in month["weeks"]:
            for day in week["days"]:
                day["events"] = by_date.get(day["date"], [])
                sd = special_by_date.get(day["date"])
                if sd:
                    day["special"] = sd.model_dump()

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
def get_week():
    """Return the current week's days and events."""
    today = datetime.date.today()
    # Find Monday of the current week
    start_of_week = today - datetime.timedelta(days=today.weekday())
    
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
    
    # Filter and attach events
    for day in week_days:
        d_iso = day["date"]
        day_events = []
        for ev in events:
            if ev["start_date"] <= d_iso <= ev["end_date"]:
                day_events.append(ev)
        day["events"] = day_events
        
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
    days_map = {d.date: d for d in current_days}
    
    for date_str in req.dates:
        if date_str in days_map:
            days_map[date_str].tags = req.tags
            days_map[date_str].where = req.where
        else:
            days_map[date_str] = SpecialDay(date=date_str, tags=req.tags, where=req.where)
            
    # Remove entries with no tags and no 'where'
    final_days = [d for d in days_map.values() if d.tags or d.where]
    save_special_days(final_days)
    return {"status": "ok", "count": len(req.dates)}
