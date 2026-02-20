import pandas as pd
import requests
import io

API_KEY = "HXJNgeR_QWyyTYHkf0Fs6Q"
STATION_LIST_URL = f"https://apihub.kma.go.kr/api/typ01/url/stn_inf.php?inf=SFC&stn=&help=1&authKey={API_KEY}"

def load_station_list_debug():
    print("Attempting to load station list...")
    try:
        # User-Agent header might be needed if API blocks default python requests
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(STATION_LIST_URL, headers=headers, timeout=15)
        response.encoding = 'euc-kr' 
        
        print(f"Status Code: {response.status_code}")
        
        # Parse fixed width/whitespace separated content
        # Skip bad lines, use # as comment
        df = pd.read_csv(io.StringIO(response.text), 
                         sep=r"\s+", 
                         comment="#", 
                         header=None, 
                         on_bad_lines='skip')
        
        print(f"Columns found: {len(df.columns)}")
        if not df.empty:
            print(f"First row: {df.iloc[0].tolist()}")

        if len(df.columns) > 10:
            df.rename(columns={0: 'STN_ID', 10: 'STN_NAME'}, inplace=True)
            df['STN_ID'] = df['STN_ID'].astype(str)
            print("Successfully parsed dataframe.")
            print(df.head())
            return df
        else:
            print("DataFrame has less than 10 columns.")
            return pd.DataFrame()
    except Exception as e:
        print(f"Error occurred: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    load_station_list_debug()
