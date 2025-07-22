# test_calendar_generator.py

import unittest
import pandas as pd
import pytz
from datetime import datetime
from calendar_generator import generate_calendar_table
from calendar_utils import save_calendar, calculate_itt_fiscal_columns, additional_calendar_columns, add_country_business_day_flags


class TestCalendarGenerator(unittest.TestCase):

    def setUp(self):
        self.start = "2023-01-01"
        self.end = "2023-01-02"
        self.freq = "1h"
        self.regions = ["US/Eastern", "Europe/Rome", "Asia/Tokyo"]
        self.countries = ["IT", "US"]
        self.df = generate_calendar_table(
            self.start, self.end, freq=self.freq, regions=self.regions, column_groups=[
                "time",
                "standard",
                "fiscal",
                "additional",
                "country_business",
                "regional",
                "extra",
            ]
        )

    def test_datetime_utc_column(self):
        self.assertIn("datetime_utc", self.df.columns)
        self.assertTrue(pd.api.types.is_datetime64tz_dtype(self.df["datetime_utc"]))
        self.assertEqual(str(self.df["datetime_utc"].dt.tz), "UTC")

    def test_time_components(self):
        for col in ["hour", "minute", "second"]:
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_integer_dtype(self.df[col]))

    def test_localized_datetime_columns(self):
        for region in self.regions:
            col = f'datetime_{region.replace("/", "_").replace("-", "_')}'
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_datetime64tz_dtype(self.df[col]))
            self.assertEqual(str(self.df[col].dt.tz), str(pytz.timezone(region)))

    def test_business_day_flags(self):
        for region in self.regions:
            col = f"is_business_day_{region.replace("/", "_').replace("-", "_')}"
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[col]))

    def test_business_month_end_flags(self):
        for region in self.regions:
            col = f"is_business_month_end_{region.replace("/", "_').replace("-", "_')}"
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[col]))

    def test_standard_calendar_columns(self):
        for col in [
            "year",
            "month",
            "quarter",
            "week_of_month",
            "is_leap_year",
            "is_year_start",
            "is_year_end",
            "days_in_month",
            "days_in_year",
        ]:
            self.assertIn(col, self.df.columns)

    def test_dst_flags(self):
        for region in self.regions:
            region_col = region.replace("/", "_").replace("-", "_")
            col = f"is_dst_{region_col}"
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[col]))

    def test_fiscal_columns(self):
        self.assertIn("ITTFiscalMonth", self.df.columns)
        # Add more specific tests for fiscal logic if needed

    def test_additional_calendar_columns(self):
        for col in [
            "WeekStart_ISO",
            "WeekEnd_ISO",
            "WeekStart_YearBounded",
            "WeekEnd_YearBounded",
            "WeekOfMonth",
            "IsLastWeekOfMonth",
            "MonthStart",
            "MonthEnd",
            "DaysInMonth",
            "QuarterStart",
            "QuarterEnd",
            "DaysInQuarter",
            "YearMonth",
            "YearWeek",
            "ISOWeekYear",
        ]:
            self.assertIn(col, self.df.columns)

    def test_country_business_day_flags(self):
        for country in self.countries:
            self.assertIn(f"IsHolidayDay_{country}", self.df.columns)
            self.assertIn(f"IsBusinessDay_{country}", self.df.columns)
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[f"IsHolidayDay_{country}"]))
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[f"IsBusinessDay_{country}"]))

    def test_invalid_date_format_error_handling(self):
        with self.assertRaises(ValueError) as cm:
            generate_calendar_table("invalid-date", self.end)
        self.assertIn("Invalid date format or value", str(cm.exception))

    def test_invalid_frequency_error_handling(self):
        with self.assertRaises(ValueError) as cm:
            generate_calendar_table(self.start, self.end, freq="invalid-freq")
        self.assertIn("Invalid frequency", str(cm.exception))

    def test_save_calendar_error_handling(self):
        # Test case for invalid filename
        with self.assertRaises(ValueError) as cm:
            save_calendar(self.df, filename="", format="csv")
        self.assertIn("Filename must be a non-empty string.", str(cm.exception))

        # Test case for unsupported format
        with self.assertRaises(ValueError) as cm:
            save_calendar(self.df, filename="test", format="unsupported")
        self.assertIn("Unsupported format", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
