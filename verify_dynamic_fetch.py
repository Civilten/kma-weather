import sys
import pandas as pd
from app import fetch_date_range, get_api_key

API_KEY = "fFr5k0SuRyia-ZNErlcoHA"
selected_ids = ["108", "112"] # Seoul, Incheon

print("Fetching initial data: 2018-09 to 2018-10")
df_initial = fetch_date_range(2018*12+9, 2018*12+10, selected_ids, API_KEY)
print(f"Initial shape: {df_initial.shape}")
print(f"Initial unique time_vals: {sorted(df_initial['time_val'].unique().tolist())}")

fetched_start = 2018*12+9
fetched_end = 2018*12+10

# Simulate extending to 2018-08 (Past)
new_start = 2018*12+8
if new_start < fetched_start:
    print("\nFetching delta for past: 2018-08")
    head_df = fetch_date_range(new_start, fetched_start - 1, selected_ids, API_KEY)
    print(f"Head DF shape: {head_df.shape}")
    if not head_df.empty:
        df_initial = pd.concat([head_df, df_initial], ignore_index=True)
    fetched_start = new_start

# Simulate extending to 2018-11 (Future)
new_end = 2018*12+11
if new_end > fetched_end:
    print("\nFetching delta for future: 2018-11")
    tail_df = fetch_date_range(fetched_end + 1, new_end, selected_ids, API_KEY)
    print(f"Tail DF shape: {tail_df.shape}")
    if not tail_df.empty:
        df_initial = pd.concat([df_initial, tail_df], ignore_index=True)
    fetched_end = new_end

print(f"\nFinal combined shape: {df_initial.shape}")
print(f"Final unique time_vals: {sorted(df_initial['time_val'].unique().tolist())}")

print("\nSimulating shrinking period to 2018-09 to 2018-10")
target_start = 2018*12+9
target_end = 2018*12+10
filtered = df_initial[(df_initial['time_val'] >= target_start) & (df_initial['time_val'] <= target_end)]
print(f"Filtered unique time_vals: {sorted(filtered['time_val'].unique().tolist())}")
