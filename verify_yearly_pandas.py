import pandas as pd
import requests
import io

API_KEY = "OsOXb4zvRB-Dl2-M78QfKw"
YEAR = "2016"
URL = f"https://apihub.kma.go.kr/api/typ02/openApi/SfcYearlyInfoService/getYearSumry?pageNo=1&numOfRows=10&dataType=XML&year={YEAR}&authKey={API_KEY}"

def check_yearly_pandas():
    print(f"Fetching: {URL}")
    try:
        response = requests.get(URL, timeout=15)
        # response.encoding = 'utf-8' # Auto
        
        print("Attempting pd.read_xml...")
        # xpath might be needed if structure is nested like <items><item><temp><info>...
        # Let's try default first, then specific xpath
        try:
            df = pd.read_xml(io.BytesIO(response.content), xpath=".//info") # Guessing 'info' is the record based on previous print
            print("Success with xpath='.//info'")
            print(df.head())
            print(df.columns)
            return
        except Exception as e:
            print(f"Failed with xpath='.//info': {e}")
            
        try:
            df = pd.read_xml(io.BytesIO(response.content))
            print("Success with default parsers")
            print(df.head())
        except Exception as e:
            print(f"Failed default: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_yearly_pandas()
