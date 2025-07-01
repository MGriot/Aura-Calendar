# test_calendar_generator.py

import unittest
import pandas as pd
import pytz
from datetime import datetime
from calendar_generator_cli import generate_calendar_table


class TestCalendarGenerator(unittest.TestCase):

    def setUp(self):
        self.start = "2023-01-01"
        self.end = "2023-01-02"
        self.freq = "1h"
        self.regions = ["US/Eastern", "Europe/Rome", "Asia/Tokyo"]
        self.df = generate_calendar_table(
            self.start, self.end, freq=self.freq, regions=self.regions
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
            col = f'datetime_{region.replace("/", "_")}'
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_datetime64tz_dtype(self.df[col]))
            self.assertEqual(str(self.df[col].dt.tz), str(pytz.timezone(region)))

    def test_business_day_flags(self):
        for region in self.regions:
            col = f"is_business_day_{region}"
            self.assertIn(col, self.df.columns)
            self.assertTrue(pd.api.types.is_bool_dtype(self.df[col]))

    def test_business_month_end_flags(self):
        for region in self.regions:
            col = f"is_business_month_end_{region}"
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


if __name__ == "__main__":
    unittest.main()
