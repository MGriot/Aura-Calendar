import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import get_calendar, AssignRequest, assign_special_days

def test_get_calendar_merge():
    print("Testing get_calendar merge logic...")
    # First assign something
    req = AssignRequest(dates=["2026-05-04"], tags=["special"], where="office")
    assign_special_days(req)
    
    # Now get calendar
    # start_month=5, start_year=2026, num_months=1
    res = get_calendar(start_month=5, start_year=2026, num_months=1)
    
    found = False
    for month in res["months"]:
        for week in month["weeks"]:
            for day in week["days"]:
                if day["date"] == "2026-05-04":
                    assert "special" in day
                    assert "special" in day["special"]["tags"]
                    assert day["special"]["where"] == "office"
                    found = True
    
    assert found
    assert "tags_config" in res
    assert "special_days" in res
    print("Calendar merge test PASSED")

if __name__ == "__main__":
    try:
        test_get_calendar_merge()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
