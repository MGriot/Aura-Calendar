import json
import pandas as pd
import sys
import os

# Ensure the script can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from calendar_generator import generate_calendar_table

def main():
    start = "2026-01-01"
    # We want 4 months: January, February, March, April 2026
    # So end date will be April 30, 2026
    end = "2026-04-30"
    freq = "D"
    regions = ["US/Eastern"] # Assuming default for event/holiday tracking
    countries = ["US"]
    
    print(f"Generating calendar data from {start} to {end}...")
    calendar_df = generate_calendar_table(
        start, end, freq=freq, regions=regions, countries=countries, n_workers=1
    )
    
    # Process output for React UI
    # We mainly need: date (YYYY-MM-DD), day, month, year, cw (week_of_year), is_business_day, holiday_US
    
    data = []
    
    for _, row in calendar_df.iterrows():
        # Extracted basic fields (assuming calendar_generator outputs these or similar based on columns):
        date_str = pd.to_datetime(row['date_utc']).strftime('%Y-%m-%d')
        
        # Determine some mock events for UI based on the reference:
        # Example: 1st Jan=New Year's Day, 6th Jan=Epiphany, 19th MLK Day, 
        # 14 Feb=Valentine's Day, 16 Feb=Presidents' Day, 28 = End of sprint
        events = []
        if date_str == "2026-01-01": events.append("New Year's Day")
        if date_str == "2026-01-06": events.append({"type": "sprint", "label": "Sprint Kickoff"})
        if date_str == "2026-01-19": events.append("MLK Day (Observed)")
        if date_str == "2026-02-04": events.append({"type": "review", "label": "Review Cycle"})
        if date_str == "2026-02-14": events.append("Valentine's Day")
        if date_str == "2026-02-16": events.append("Presidents' Day")
        if date_str == "2026-02-28": events.append("End of Sprint")
        if date_str == "2026-03-06": events.append({"type": "audit", "label": "Audit Report"})
        if date_str == "2026-04-01": events.append("April Fools'")
        if date_str == "2026-04-03": events.append({"type": "goal", "label": "Q2 Goal Post"})
        if date_str == "2026-04-05": events.append("Easter Sunday")
        if date_str == "2026-04-15": events.append("Tax Day (US)")
        
        day_dict = {
            "date": date_str,
            "day_of_month": int(row['day']) if 'day' in row else pd.to_datetime(row['date_utc']).day,
            "month": int(row['month']) if 'month' in row else pd.to_datetime(row['date_utc']).month,
            "year": int(row['year']) if 'year' in row else pd.to_datetime(row['date_utc']).year,
            "cw": int(row['week_of_year']) if 'week_of_year' in row else pd.to_datetime(row['date_utc']).isocalendar()[1],
            "day_of_week": pd.to_datetime(row['date_utc']).dayofweek, # 0=Monday, 6=Sunday
            "events": events
        }
        data.append(day_dict)
        
    output_path = os.path.join(os.path.dirname(__file__), 'calendarData.json')
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Data saved successfully to {output_path}")

if __name__ == "__main__":
    main()
