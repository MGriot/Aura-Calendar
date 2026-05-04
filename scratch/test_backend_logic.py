import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from main import load_tags_config, TagsConfig, TagConfigItem, assign_special_days, AssignRequest, load_special_days

def test_tags():
    print("Testing Tags logic...")
    config = load_tags_config()
    print(f"Loaded {len(config.primary)} primary tags and {len(config.where)} where tags.")
    assert len(config.primary) > 0
    assert len(config.where) > 0

def test_assign():
    print("Testing Assign logic...")
    req = AssignRequest(dates=["2026-12-25"], tags=["holiday"], where="remote")
    assign_special_days(req)
    days = load_special_days()
    found = False
    for d in days:
        if d.date == "2026-12-25":
            assert "holiday" in d.tags
            assert d.where == "remote"
            found = True
    assert found
    print("Assign test PASSED")

if __name__ == "__main__":
    try:
        test_tags()
        test_assign()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        sys.exit(1)
