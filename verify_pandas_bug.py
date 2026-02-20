import pandas as pd
import requests
import xml.etree.ElementTree as ET

API_KEY = "fFr5k0SuRyia-ZNErlcoHA"

def fetch_single_month_api(api_url):
    try:
        response = requests.get(api_url, timeout=15)
        root = ET.fromstring(response.text)
        infos = root.findall(".//info")
        data_list = []
        for info in infos:
            row = {}
            for child in info:
                row[child.tag] = child.text
            data_list.append(row)
        return pd.DataFrame(data_list)
    except:
        return pd.DataFrame()

def fetch_monthly_data(year, month, api_key):
    month_str = f"{month:02d}"
    url1 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry?pageNo=1&numOfRows=999&dataType=XML&year={year}&month={month_str}&authKey={api_key}"
    url2 = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcMtlyInfoService/getMmSumry2?pageNo=1&numOfRows=999&dataType=XML&year={year}&month={month_str}&authKey={api_key}"
    
    df1 = fetch_single_month_api(url1)
    df2 = fetch_single_month_api(url2)
    
    print(f"[{year}-{month_str}] df1: {df1.shape}, df2: {df2.shape}")
    
    if df1.empty and df2.empty:
        return pd.DataFrame()
        
    # Standardize STN_ID
    if not df1.empty and 'stnid' in df1.columns:
        df1.rename(columns={'stnid': 'stn_id'}, inplace=True)
    if not df2.empty and 'stn_id' not in df2.columns and 'stnid' in df2.columns:
        df2.rename(columns={'stnid': 'stn_id'}, inplace=True)
        
    print(f"  Columns df1: {df1.columns.tolist() if not df1.empty else []}")
    print(f"  Columns df2: {df2.columns.tolist() if not df2.empty else []}")
    
    # Merge
    if not df1.empty and not df2.empty:
        merged_df = pd.merge(df1, df2, on='stn_id', how='outer', suffixes=('', '_y'))
        print(f"  Merged columns: {merged_df.columns.tolist()}")
        if 'stnko' in merged_df.columns:
            merged_df.rename(columns={'stnko': 'stn_ko'}, inplace=True)
            print("  Renamed stnko to stn_ko")
    elif not df1.empty:
        merged_df = df1
        if 'stnko' in merged_df.columns:
            merged_df.rename(columns={'stnko': 'stn_ko'}, inplace=True)
    else:
        merged_df = df2
        
    merged_df['year'] = year
    merged_df['month'] = month
    
    numeric_cols = ['avgtamax', 'avgtamin', 'taavg', 'tamax', 'tamin', 'avghm', 'rn_day', 'ws', 'ws_max']
    for col in numeric_cols:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            
    return merged_df

try:
    print("Testing merge logic...")
    # Fetch 2 months to test concat
    df_2016_09 = fetch_monthly_data(2016, 9, API_KEY)
    df_2016_10 = fetch_monthly_data(2016, 10, API_KEY)
    
    # Simulate saving to session state
    raw_df = pd.concat([df_2016_09, df_2016_10], ignore_index=True)
    print(f"Total raw records: {len(raw_df)}")
    
    # Simulate subsetting stn_ids
    selected_ids = ['108', '112', '119']  # Seoul, Incheon, Suwon
    filtered_df = raw_df[raw_df['stn_id'].isin(selected_ids)]
    print(f"Filtered records: {len(filtered_df)}")
    
    print("\nTesting Aggregate Yearly...")
    grouped_yearly = filtered_df.groupby(['stn_id', 'year'])
    agg_funcs = {'taavg':'mean', 'rn_day':'sum'}
    res_yearly = grouped_yearly.agg(agg_funcs).reset_index()
    print("Yearly success!")
    
    print("\nTesting Aggregate Monthly...")
    grouped_monthly = filtered_df.groupby(['stn_id', 'month'])
    agg_funcs_m = {'taavg':'mean', 'rn_day':'mean'}
    res_monthly = grouped_monthly.agg(agg_funcs_m).reset_index()
    print("Monthly success!")
    
except Exception as e:
    import traceback
    traceback.print_exc()
