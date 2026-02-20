import pandas as pd
import requests
import io
import xml.etree.ElementTree as ET
from datetime import datetime

API_KEY_STATION = "essYXrddTSaLGF63Xc0mAw" 
API_KEY_YEARLY = "OsOXb4zvRB-Dl2-M78QfKw" 

def test_new_logic():
    print("1. Testing Time-based Station List (202211300900)...")
    try:
        url = f"https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&tm=202211300900&help=1&authKey={API_KEY_STATION}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'euc-kr' 
        
        # Write to file to debug
        with open("debug_response.txt", "wb") as f:
            f.write(response.content)
        print("   Response written to debug_response.txt")
        
        df = pd.read_csv(io.StringIO(response.text), sep=r"\s+", comment="#", header=None, on_bad_lines='skip')
        
        if len(df.columns) > 10:
            df.rename(columns={0: 'STN_ID', 10: 'STN_NAME'}, inplace=True)
            df['STN_ID'] = df['STN_ID'].astype(str)
            print(f"   Success: Found {len(df)} stations.")
            # Pick a station ID for next step (e.g., 108 Seoul)
            target_id = "108"
        else:
            print(f"   Failed to parse station list. Columns found: {len(df.columns)}")
            print("   First 3 rows:")
            print(df.head(3))
            return

    except Exception as e:
        print(f"   Error: {e}")
        return

    print(f"\n2. Testing Yearly Data Fetching (2016) for Station {target_id}...")
    try:
        url = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcYearlyInfoService/getYearSumry?pageNo=1&numOfRows=999&dataType=XML&year=2016&authKey={API_KEY_YEARLY}"
        response = requests.get(url, timeout=15)
        root = ET.fromstring(response.text)
        infos = root.findall(".//info")
        
        data_list = []
        for info in infos:
            row = {}
            for child in info:
                row[child.tag] = child.text
            row['year'] = '2016'
            data_list.append(row)
            
        df_year = pd.DataFrame(data_list)
        if not df_year.empty:
            print(f"   Success: Fetched {len(df_year)} records.")
            if 'stn_id' in df_year.columns:
                filtered = df_year[df_year['stn_id'] == target_id]
                print(f"   Filtered for Station {target_id}: found {len(filtered)} rows.")
                if not filtered.empty:
                    print("   Sample Data (va_lst_03 - Avg Temp):", filtered.iloc[0].get('va_lst_03'))
            else:
                 print("   'stn_id' column not found in XML data.")
        else:
            print("   No data returned.")

    except Exception as e:
        print(f"   Error: {e}")

if __name__ == "__main__":
    test_new_logic()
