# visualize_business_eom.py

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import argparse
import os


def load_calendar_data(file_path):
    """Load calendar data from CSV."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    return pd.read_csv(file_path, parse_dates=True)


def extract_business_eom_flags(df):
    """Identify columns that represent business end-of-month flags."""
    return [col for col in df.columns if col.startswith("is_business_month_end_")]


def plot_business_eom_heatmap(
    df, region_flag_col, date_col="datetime_utc", save_path=None
):
    """Plot and optionally save a heatmap of business EOM days."""
    df[date_col] = pd.to_datetime(df[date_col])
    df["year"] = df[date_col].dt.year
    df["month"] = df[date_col].dt.month

    eom_df = df[df[region_flag_col]]
    heatmap_data = eom_df.groupby(["year", "month"]).size().unstack(fill_value=0)

    plt.figure(figsize=(12, 6))
    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt="d",
        cmap="YlGnBu",
        cbar_kws={"label": "Business EOM Days"},
    )
    plt.title(
        f"Business End-of-Month Days Heatmap for {region_flag_col.replace('is_business_month_end_', '')}"
    )
    plt.xlabel("Month")
    plt.ylabel("Year")
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path)
    plt.show()


def main():
    parser = argparse.ArgumentParser(
        description="Visualize Business End-of-Month Days from Calendar CSV"
    )
    parser.add_argument("file", help="Path to the calendar CSV file")
    parser.add_argument(
        "--region", help="Region to visualize (e.g., Europe_Rome)", default=None
    )
    parser.add_argument("--save", help="Path to save the heatmap image", default=None)
    args = parser.parse_args()

    df = load_calendar_data(args.file)
    eom_flags = extract_business_eom_flags(df)

    if not eom_flags:
        print("No business end-of-month flags found in the file.")
        return

    if args.region:
        flag_col = f"is_business_month_end_{args.region}"
        if flag_col not in df.columns:
            print(f"Region '{args.region}' not found in columns.")
            return
        plot_business_eom_heatmap(df, flag_col, save_path=args.save)
    else:
        for flag_col in eom_flags:
            plot_business_eom_heatmap(df, flag_col, save_path=args.save)


if __name__ == "__main__":
    main()
