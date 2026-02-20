import pandas as pd
import requests
import io

API_KEY = "HXJNgeR_QWyyTYHkf0Fs6Q"
STATION_LIST_URL = f"https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&help=1&authKey={API_KEY}"

def test_station_parsing():
    print("Testing Station List Parsing...")
    try:
        response = requests.get(STATION_LIST_URL)
        response.encoding = 'euc-kr' 
        
        df = pd.read_csv(io.StringIO(response.text), 
                         sep="\s+", 
                         comment="#", 
                         header=None,
                         on_bad_lines='skip')
        
        if len(df.columns) > 10:
            df.rename(columns={0: 'STN_ID', 10: 'STN_NAME'}, inplace=True)
            df['STN_ID'] = df['STN_ID'].astype(str)
            print(f"Success! Found {len(df)} stations.")
            print(df[['STN_ID', 'STN_NAME']].head())
        else:
            print("Failed: Columns not found.")
            print(df.head())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_station_parsing()
