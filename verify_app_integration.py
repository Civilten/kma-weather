import sys
import os
import pandas as pd
from app import fetch_monthly_data, aggregate_data, get_api_key

API_KEY = "fFr5k0SuRyia-ZNErlcoHA"

print("Fetching data for 2016-09...")
df1 = fetch_monthly_data(2016, 9, API_KEY)
print("Fetching data for 2017-09...")
df2 = fetch_monthly_data(2017, 9, API_KEY)
print("Fetching data for 2016-10...")
df3 = fetch_monthly_data(2016, 10, API_KEY)

raw_df = pd.concat([df1, df2, df3], ignore_index=True)
print(f"Raw shape: {raw_df.shape}")
print(f"Raw Columns: {raw_df.columns.tolist()}")

stn_map = {"108": "서울", "112": "인천", "119": "수원"}
test_df = raw_df[raw_df['stn_id'].isin(["108", "112", "119"])].copy()

print("\n--- Testing Yearly ---")
try:
    yearly_df = aggregate_data(test_df, 'yearly', stn_map)
    print("Success. Yearly Columns:")
    print(yearly_df.columns.tolist())
    print(yearly_df.head(2))
except Exception as e:
    print(f"FAILED YEARLY: {e}")

print("\n--- Testing Monthly ---")
try:
    monthly_df = aggregate_data(test_df, 'monthly', stn_map)
    print("Success. Monthly Columns:")
    print(monthly_df.columns.tolist())
    print(monthly_df.head(2))
except Exception as e:
    print(f"FAILED MONTHLY: {e}")
